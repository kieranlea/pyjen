"""Declarations for the abstraction of a Jenkins build agent"""
import time
from six.moves import urllib_parse


class Node(object):
    """Wrapper around a Jenkins build agent (aka: Node) configuration

    Use this class to manipulate agents managed by a Jenkins master

    .. seealso: :py:meth:`~.jenkins.Jenkins.find_node`

    :param api:
        Pre-initialized connection to the Jenkins REST API
    :type api: :class:`~/utils/jenkins_api/JenkinsAPI`
    """

    def __init__(self, api):
        super(Node, self).__init__()
        self._api = api

    @property
    def name(self):
        """Gets the display name of this Node

        :rtype: :class:`str`
        """
        data = self._api.get_api_data()

        return data['displayName']

    @property
    def is_offline(self):
        """Checks to see whether this Node is currently offline or not

        :rtype: :class:`bool`
        """
        data = self._api.get_api_data()

        return data['offline']

    @property
    def is_idle(self):
        """Checks to see whether any executors are in use on this Node or not

        :rtype: :class:`bool`
        """
        data = self._api.get_api_data()
        return data['idle']

    @property
    def number_of_executors(self):
        """Returns the number of executors this node provides

        :rtype: :class:`int`
        """
        data = self._api.get_api_data()
        return data['numExecutors']

    def toggle_offline(self, message=None):
        """Toggles the online status of this Node

        If the current state of this Node is "offline" it will be toggled to
        "online" and vice-versa.

        :param str message:
            optional descriptive message explaining the reason this node has
            been taken offline.
        """
        post_cmd = self._api.url + "toggleOffline"
        if message is not None:
            post_cmd += "?offlineMessage=" + urllib_parse.quote(message)

        self._api.post(post_cmd)

    def wait_for_idle(self, max_timeout=None):
        """Blocks execution until this Node enters an idle state

        :param int max_timeout:
            The maximum amount of time, in seconds, to wait for an idle state.
            If this value is undefined, this method will block indefinitely.

        :returns:
            True if the Node has entered idle state before returning
            otherwise returns False
        :rtype: :class:`bool`
        """
        polling_period_in_seconds = 1

        total_wait_time = 0
        while not self.is_idle:
            time.sleep(polling_period_in_seconds)
            if max_timeout is None:
                continue

            total_wait_time += polling_period_in_seconds
            if total_wait_time >= max_timeout:
                break

        return self.is_idle


if __name__ == "__main__":  # pragma: no cover
    pass
