import pytest
from .utils import async_assert, clean_job
from pyjen.jenkins import Jenkins
from pyjen.queue_item import QueueItem


def test_waiting_build_queue(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    queue = jk.build_queue
    jb = jk.create_job("test_waiting_build_queue", "hudson.model.FreeStyleProject")
    with clean_job(jb):
        jb.quiet_period = 5
        jb.start_build()
        res = queue.items
        assert isinstance(res, list)
        assert len(res) == 1
        assert res[0].stuck is False
        assert isinstance(res[0].id, int)
        qjob = res[0].job
        assert qjob == jb


def test_out_of_queue(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    queue = jk.build_queue
    jb = jk.create_job("test_waiting_build_queue", "hudson.model.FreeStyleProject")
    with clean_job(jb):
        jb.quiet_period = 1
        jb.start_build()

        res = queue.items
        assert isinstance(res, list)
        assert len(res) == 1
        item = res[0]
        assert item.waiting is True
        async_assert(lambda: jb.last_build)
        assert item.waiting is False


def test_cancel_queued_build(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    queue = jk.build_queue
    jb = jk.create_job("test_cancel_queued_build", "hudson.model.FreeStyleProject")
    with clean_job(jb):
        jb.quiet_period = 10
        jb.start_build()

        res = queue.items
        item = res[0]
        assert item.waiting is True
        item.cancel()
        assert item.waiting is False
        assert item.cancelled is True


def test_get_build_after_queued(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    queue = jk.build_queue
    jb = jk.create_job("test_get_build_after_queued", "hudson.model.FreeStyleProject")
    with clean_job(jb):
        jb.quiet_period = 1
        jb.start_build()

        res = queue.items
        item = res[0]
        assert item.build is None
        async_assert(lambda: jb.last_build)

        assert item.build is not None
        assert item.build == jb.last_build


def test_start_build_returned_queue_item(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    queue = jk.build_queue
    jb = jk.create_job("test_start_build_returned_queue_item", "hudson.model.FreeStyleProject")
    with clean_job(jb):
        jb.quiet_period = 1
        item = jb.start_build()

        assert item is not None
        assert isinstance(item, QueueItem)
        assert queue.items[0] == item


def test_queue_get_build(jenkins_env):
    jk = Jenkins(jenkins_env["url"], (jenkins_env["admin_user"], jenkins_env["admin_token"]))
    jb = jk.create_job("test_queue_get_build", "hudson.model.FreeStyleProject")
    with clean_job(jb):
        jb.quiet_period = 0
        item = jb.start_build()

        async_assert(lambda: not item.waiting)

        bld = item.build
        assert bld is not None
        assert bld == jb.last_build


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
