import os
import shutil
import tarfile
import io
import json
import pytest
import logging
import docker
import multiprocessing
from docker.errors import DockerException
from pyjen.jenkins import Jenkins
from .utils import async_assert

# TODO: Add support for Jenkins 1 testing

# Global flag used to see whether we've already attempted to run our Jenkins
# containerized environment. Prevents redundant failures from slowing down
# the test runner
FAILED_DOCKER_SETUP = False


def pytest_addoption(parser):
    """Customizations for the py.test command line options"""
    parser.addoption(
        "--skip-docker",
        action="store_true",
        help="don't run tests that depend on the Jenkins service"
    )
    parser.addoption(
        "--preserve",
        action="store_true",
        help="Keeps the Docker container used for testing alive after the "
             "test run has completed"
    )
    parser.addoption(
        "--jenkins-version",
        action="store",
        default="jenkins:alpine",
        help="Name of docker container for the Jenkins version to test against"
    )


def extract_file(client, container, path):
    """Extracts a single file from a Docker container

    Extraction is performed in-memory to improve performance and minimize
    disk dependency

    :param client: Docker API connection to the service
    :param int container: ID of the container to work with
    :param str path:
        path within the container where the file to extract
    :returns: contents of the specified file
    :rtype: :class:`str`
    """
    log = logging.getLogger(__name__)

    # Get docker to generate an in memory tar ball for the file
    byte_stream, stats = client.get_archive(container, path)
    log.debug(json.dumps(stats, indent=4))

    # convert the in memory byte stream from a generator
    # to a file-like container
    in_memory_tar = io.BytesIO()
    for packet in byte_stream:
        in_memory_tar.write(packet)
    in_memory_tar.seek(0)

    # parse the in-memory tar data
    with tarfile.open(fileobj=in_memory_tar) as tf:
        cur_mem = tf.getmember(os.path.split(path)[1])
        return tf.extractfile(cur_mem).read().decode("utf-8").strip()


def inject_file(client, container, local_file_path, container_path):
    """Adds a single file to a Docker container

    :param client: Docker API connection to the service
    :param int container: ID of the container to work with
    :param str local_file_path:
        path to the local file to add to the container
    :param str container_path:
        path within the container to inject the file to
    """
    if os.path.exists("temp.tar"):
        os.unlink("temp.tar")

    with tarfile.open("temp.tar", 'w') as tar:
        tar.add(local_file_path)

    with open("temp.tar") as tf:
        client.put_archive(container, container_path, tf)

    os.unlink("temp.tar")


def _workspace_dir():
    """Gets the absolute path to the root folder of the workspace

    :rtype: :class:`str`
    """
    cur_path = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(cur_path, ".."))


def docker_logger(client, container_id):
    """Helper method that redirects Docker logs to Python logger

    This helper method is intended to be used as a background daemon to
    redirect all log messages from a given Docker container to the Python
    logging subsystem.

    :param client: docker-py API client object
    :param str container_id: ID for the container to check logs for
    """
    log = logging.getLogger(__name__)
    for cur_log in client.logs(container_id, stream=True, follow=True):
        log.debug(cur_log.decode("utf-8").strip())


@pytest.fixture(scope="session", autouse=True)
def configure_logger():
    """Configure logging for the test runner"""
    log_dir = os.path.join(_workspace_dir(), "logs")
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir)

    global_log = logging.getLogger()
    global_log.setLevel(logging.DEBUG)

    verbose_format = "%(asctime)s(%(levelname)s->%(module)s):%(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    fmt = logging.Formatter(verbose_format, date_format)
    file_handler = logging.FileHandler(
        os.path.join(log_dir, "tests.log"),
        mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    global_log.addHandler(file_handler)


@pytest.fixture(scope="session")
def jenkins_env(request, configure_logger):
    """Fixture that generates a dockerized Jenkins environment for testing"""
    global FAILED_DOCKER_SETUP
    log = logging.getLogger(__name__)

    if FAILED_DOCKER_SETUP:
        raise Exception(
            "Skipping Docker setup logic. Previous attempt failed.")

    image_name = request.config.getoption("--jenkins-version")
    preserve_container = request.config.getoption("--preserve")
    container_id_file = os.path.join(_workspace_dir(), "container_id.txt")

    try:
       client = docker.APIClient(version="auto")
    except DockerException as err:
        log.error("Unable to connect to Docker service. Make sure you have "
                  "Docker installed and that the service is running.")
        log.exception(err)
        FAILED_DOCKER_SETUP = True
        return

    # Make sure we have a copy of the Docker image in the local cache.
    # If we do already have a copy of the image locally, we don't need to pull
    # a new copy. This allows us to run the tests offline so long as the
    # local Docker cache contains the image we need
    found_image = False
    for cur_image in client.images():
        if image_name in cur_image["RepoTags"]:
            found_image = True
            break
    if not found_image:
        log.info("Pulling Jenkins Docker image...")
        for cur_line in client.pull(image_name, stream=True, decode=True):
            log.debug(json.dumps(cur_line, indent=4))

    # create our docker container, if one doesn't already exist
    log.info("Creating Jenkins Docker container...")
    hc = client.create_host_config(
        port_bindings={8080: None},
    )

    if os.path.exists(container_id_file):
        with open(container_id_file) as file_handle:
            container_id = file_handle.read().strip()
        log.info("Reusing existing container %s", container_id)

        # TODO: Detect when the ID in the file is invalid and re-create
        #       the docker environment on the fly
    else:
        res = client.create_container(
            image_name, host_config=hc, volumes=["/var/jenkins_home"])
        log.debug(json.dumps(res, indent=4))
        container_id = res["Id"]
        log.debug("Container %s created", container_id)

    # Setup background thread for redirecting log output to Python logger
    d = multiprocessing.Process(
        name='docker_logger',
        target=docker_logger,
        args=(client, container_id))
    d.daemon = True
    d.start()

    try:
        log.info("Starting Jenkins Docker container...")
        client.start(container_id)

        # Look for a magic phrase in the log output from our container
        # to see when the Jenkins service is up and running before running
        # any tests
        log.info("Waiting for Jenkins Docker container to start...")
        magic_message = "Jenkins is fully up and running"

        # Parse admin password from container
        for cur_log in client.logs(container_id, stream=True, follow=True):
            temp = cur_log.decode("utf-8").strip()
            if magic_message in temp:
                break
        log.info("Container started. Extracting admin token...")
        token = extract_file(
            client,
            container_id,
            "/var/jenkins_home/secrets/initialAdminPassword")
        log.info("Extracted token " + str(token))

        # prepare connection parameters for the docker environment
        # for the tests to use
        http_port = client.port(container_id, 8080)[0]["HostPort"]
        data = {
            "url": "http://localhost:{0}".format(http_port),
            "admin_user": "admin",
            "admin_token": token,
        }

        # If the docker container launches successful, save the ID so we
        # can reuse the same container for the next test run
        if preserve_container:
            with open(container_id_file, mode="w") as file_handle:
                file_handle.write(container_id)
            with open(container_id_file + ".token", mode="w") as file_handle:
                file_handle.write(token)

        yield data
    finally:
        if preserve_container:
            log.info("Leaving Jenkins Docker container running: %s",
                     container_id)
            log.info("Container will be reused on next test run. To start "
                     "a new container on next run, delete this file: %s",
                     container_id_file)
        else:
            log.info("Shutting down Jenkins Docker container...")
            client.stop(container_id)
            client.remove_container(container_id)
            if os.path.exists(container_id_file):
                os.unlink(container_id_file)
            log.info("Done Docker cleanup")


@pytest.fixture(scope="function", autouse=True)
def clear_global_state(request):
    """Clears all global state from the PyJen library

    This fixture is a total hack to compensate for the use of global state
    in the PyJen library. My hope is to break dependency on this global state
    and eliminate the need for this fixture completely
    """
    yield
    # For any test that is a member of a class, lets assume that the class has
    # one or more test fixtures configured to manage it's global state. That
    # being the case, we can't safely reset the global state of the pyjen
    # API here because this fixture runs after every test function. So functions
    # that are part of a test class would invalidate the connection which is
    # then shared between the other tests in the class
    if request.cls:
        return

    from pyjen.utils.jenkins_api import JenkinsAPI
    JenkinsAPI.creds = ()
    JenkinsAPI.ssl_verify_enabled = False
    JenkinsAPI.crumb_cache = None
    JenkinsAPI.jenkins_root_url = None
    JenkinsAPI.jenkins_headers_cache = None


@pytest.fixture(scope="class")
def test_job(request, jenkins_env):
    """Test fixture that creates a Jenkins Freestyle job for testing purposes

    The generated job is automatically cleaned up at the end of the test
    suite, which is defined as all of the methods contained within the same
    class.

    The expectation here is that tests that share this generated job will
    only perform read operations on the job and will not change it's state.
    This will ensure the tests within the suite don't affect one another.
    """
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    request.cls.jenkins = jk
    request.cls.job = jk.create_job(request.cls.__name__ + "Job", "project")
    assert request.cls.job is not None

    yield

    request.cls.job.delete()


@pytest.fixture(scope="class")
def test_builds(request, test_job):
    """Helper fixture that creates a job with a sample good build for testing"""
    request.cls.job.start_build()

    async_assert(lambda: request.cls.job.has_been_built)


def pytest_collection_modifyitems(config, items):
    """Applies command line customizations to filter tests to be run"""
    if not config.getoption("--skip-docker"):
        return

    skip_jenkins = pytest.mark.skip(reason="Skipping Jenkins Server tests")
    for item in items:
        if "jenkins_env" in item.fixturenames:
            item.add_marker(skip_jenkins)