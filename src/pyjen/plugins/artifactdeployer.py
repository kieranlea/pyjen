"""properties of the 'artifact deployer' publishing plugin"""
#from pyjen.utils.pluginapi import init_plugin
from pyjen.exceptions import PluginNotSupportedError


class ArtifactDeployer(object):
    """Interface to the Jenkins 'artifact deployer' publishing plugin

    https://wiki.jenkins-ci.org/display/JENKINS/ArtifactDeployer+Plugin
    """

    def __init__(self, node):
        """
        :param node: XML node defining the settings for a this plugin
        :type node: :class:`ElementTree.Element`
        """
        self._root = node
        assert 'plugin' in self._root.attrib
        assert self._root.attrib['plugin'].startswith('artifactdeployer')

    @property
    def entries(self):
        """Gets the list of deployment options associated with this plugin

        :returns:
            list of configuration options for each set of artifacts managed by
            this instance
        :rtype: :class:`list` of :class:`ArtifactDeployerEntry` objects
        """

        nodes = self._root.find("entries")

        retval = []
        for node in nodes:
            plugin = init_plugin(node)
            if plugin is not None:
                retval.append(plugin)
            else:
                raise PluginNotSupportedError("Artifact deployer configuration "
                                              "plugin not found", 'entries')

        return retval

    @staticmethod
    def get_jenkins_plugin_name():
        """Gets the name of the Jenkins plugin associated with this PyJen plugin

        This static method is used by the PyJen plugin API to associate this
        class with a specific Jenkins plugin, as it is encoded in the config.xml

        :rtype: :class:`str`
        """
        return "artifactdeployer"


class ArtifactDeployerEntry(object):
    """a single artifacts to be deployed by an Artifact Deployer instance"""
    def __init__(self, node):
        """
        :param node: XML node defining the settings for a this plugin
        :type node: :class:`ElementTree.Element`
        """
        self._root = node

    @property
    def remote(self):
        """Gets the remote location where these artifacts are to be published

        :rtype: :class:`str`
        """
        node = self._root.find("remote")
        return node.text


PluginClass = ArtifactDeployer


if __name__ == "__main__":  # pragma: no cover
    pass