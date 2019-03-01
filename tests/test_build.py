from datetime import datetime
import pytest
from .utils import clean_job, async_assert
from pyjen.jenkins import Jenkins
from pyjen.build import Build
from pyjen.plugins.shellbuilder import ShellBuilder


@pytest.mark.usefixtures('test_builds')
class TestSingleBuild:
    def test_build_number(self):
        bld = self.job.last_build
        assert bld.number == 1

    def test_is_not_building(self):
        bld = self.job.last_build
        assert bld.is_building is False

    def test_build_no_description(self):
        bld = self.job.last_build
        assert bld.description == ''

    def test_build_result(self):
        bld = self.job.last_good_build
        assert bld.result == "SUCCESS"

    def test_build_id(self):
        bld = self.job.last_build
        assert bld.id == '1'

    def test_build_equality(self):
        bld1 = self.job.all_builds[0]
        bld2 = self.job.last_build

        assert bld1 == bld2
        assert not bld1 != bld2


def test_start_time(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    jb = jk.create_job("test_start_time_job", "project")
    with clean_job(jb):
        before = datetime.now()
        jb.start_build()
        async_assert(lambda: jb.last_build)
        after = datetime.now()

        bld = jb.last_build
        assert before <= bld.start_time <= after


def test_build_inequality(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    jb = jk.create_job("test_build_inequality_job", "project")
    with clean_job(jb):
        jb.start_build()
        async_assert(lambda: len(jb.all_builds) == 1)
        jb.start_build()
        async_assert(lambda: len(jb.all_builds) == 2)

        bld1 = jb.all_builds[0]
        bld2 = jb.all_builds[1]

        assert bld1 != bld2
        assert not bld1 == bld2
        assert bld1 != 1


def test_console_text(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    expected_job_name = "test_console_text_job"
    jb = jk.create_job(expected_job_name, "project")
    with clean_job(jb):
        expected_output = "Here is my sample output..."
        shell_builder = ShellBuilder.create("echo " + expected_output)
        jb.add_builder(shell_builder)

        # Get a fresh copy of our job to ensure we have an up to date
        # copy of the config.xml for the job
        async_assert(lambda: jk.find_job(expected_job_name).builders)

        # Trigger a build and wait for it to complete
        jb.start_build()
        async_assert(lambda: jb.last_build)

        assert expected_output in jb.last_build.console_output


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# LEGACY UNIT TESTS


def test_build_changesets(monkeypatch):
    changeset_message = "Here's my commit message"

    fake_build_data = {
        "changeSet": {
            "items": [
                {"msg": changeset_message}
            ],
            "kind": "git"
        }
    }
    monkeypatch.setattr(Build, "get_api_data", lambda s: fake_build_data)

    bld1 = Build('http://localhost:8080/job/MyJob/3')
    changes = bld1.changeset

    assert changes.has_changes is True
    assert changes.scm_type == "git"
    assert len(changes.affected_items) == 1
    assert changes.affected_items[0].message == changeset_message


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])