"""Primitives for operating on Jenkins views of type 'StatusView'"""
from pyjen.view import View


class StatusView(View):
    """Interface to Jenkins views of type 'StatusView'"""

    def __init__(self, url):
        """
        :param controller:
            class capable of handling common HTTP IO requests sent by this
            object to the Jenkins REST API
        :type controller: :class:`~.utils.datarequester.DataRequester`
        :param jenkins_master:
            Reference to Jenkins object associated with the master instance
            managing this job
        :type jenkins_master: :class:`~.jenkins.Jenkins`
        """
        super(StatusView, self).__init__(url)

    @staticmethod
    def get_jenkins_plugin_name():
        """Gets the name of the Jenkins plugin associated with this PyJen plugin

        This static method is used by the PyJen plugin API to associate this
        class with a specific Jenkins plugin, as it is encoded in the config.xml

        :rtype: :class:`str`
        """
        return "statusview"


PluginClass = StatusView


if __name__ == "__main__":  # pragma: no cover
    pass