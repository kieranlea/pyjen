import pytest
from pyjen.jenkins import Jenkins
from pyjen.plugins.shellbuilder import ShellBuilder
from pyjen.plugins.freestylejob import FreestyleJob
from ..utils import async_assert, clean_job


def test_add_simple_shell_builder(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    job_name = "test_add_simple_shell_builder"
    jb = jk.create_job(job_name, FreestyleJob)
    with clean_job(jb):
        expected_script = "echo hello"
        shell_builder = ShellBuilder.instantiate(expected_script)
        jb.add_builder(shell_builder)

        # Get a fresh copy of our job to ensure we have an up to date
        # copy of the config.xml for the job
        async_assert(lambda: jk.find_job(job_name).builders)
        builders = jk.find_job(job_name).builders

        assert isinstance(builders, list)
        assert len(builders) == 1
        assert isinstance(builders[0], ShellBuilder)
        assert builders[0].script == expected_script
        assert builders[0].unstable_return_code is None


def test_unstable_return_code(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    job_name = "test_unstable_return_code"
    jb = jk.create_job(job_name, FreestyleJob)
    with clean_job(jb):
        rcode = 12
        failing_step = ShellBuilder.instantiate("exit " + str(rcode))
        failing_step.unstable_return_code = rcode
        jb.add_builder(failing_step)
        async_assert(lambda: jb.builders)

        # Get a fresh copy of our job to ensure we have an up to date
        # copy of the config.xml for the job
        async_assert(lambda: jk.find_job(job_name).builders)
        builders = jk.find_job(job_name).builders

        assert isinstance(builders, list)
        assert len(builders) == 1
        assert builders[0].unstable_return_code == rcode


def test_edit_unstable_return_code(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    job_name = "test_edit_unstable_return_code"
    jb = jk.create_job(job_name, FreestyleJob)
    with clean_job(jb):
        jb.quiet_period = 0
        rcode = 12
        failing_step = ShellBuilder.instantiate("exit " + str(rcode))
        failing_step.unstable_return_code = 1
        jb.add_builder(failing_step)

        # Get a fresh copy of our job to ensure we have an up to date
        # copy of the config.xml for the job
        async_assert(lambda: jk.find_job(job_name).builders)
        jb2 = jk.find_job(job_name)
        builders = jb2.builders

        # Edit the builder and run a build to see if the changes were auto applied
        builders[0].unstable_return_code = rcode
        jb2.start_build()
        async_assert(lambda: jb2.last_build)
        bld = jb2.last_build

        # Because of our changes to the configuration, the returned error code
        # should have resulted in an unstable build instead of a failed build
        assert bld.result == "UNSTABLE"


def test_add_then_edit_unstable_return_code(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    job_name = "test_add_then_edit_unstable_return_code"
    jb = jk.create_job(job_name, FreestyleJob)
    with clean_job(jb):
        jb.quiet_period = 0
        rcode = 12
        failing_step = ShellBuilder.instantiate("exit " + str(rcode))
        failing_step.unstable_return_code = 1
        jb.add_builder(failing_step)

        # Edit the build step using the original failed_step object -
        # these changes should still get applied to the job the step is
        # associated with
        failing_step.unstable_return_code = rcode

        # Get a fresh copy of our job to ensure we have an up to date
        # copy of the config.xml for the job
        async_assert(lambda: jk.find_job(job_name).builders)
        jb2 = jk.find_job(job_name)

        # run a build to see if the changes were auto applied
        jb2.start_build()
        async_assert(lambda: jb2.last_build)
        bld = jb2.last_build

        # Because of our changes to the configuration, the returned error code
        # should have resulted in an unstable build instead of a failed build
        assert bld.result == "UNSTABLE"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
