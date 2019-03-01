"""Primitives that manage Jenkins job of type 'Freestyle'"""
from pyjen.job import Job
from pyjen.utils.jobxml import JobXML


class FreestyleJob(Job):
    """Jenkins job of type 'freestyle'

    :param str url: Full URL of a job on a Jenkins master
    """

    def __init__(self, url):
        super(FreestyleJob, self).__init__(url)

    @property
    def scm(self):
        """source code management configuration for a job

        :returns:
            One of several possible plugin objects which exposes the relevant
            set of properties supported by a given source code management tool.
        :rtype: :class:`~.utils.pluginapi.PluginBase`
        """
        xml = self.config_xml
        jobxml = JobXML(xml)
        return jobxml.scm

    @property
    def custom_workspace(self):
        """
        :returns: custom workspace associated with this job
        :rtype: :class:`str`
        """
        xml = self.config_xml

        jobxml = JobXML(xml)
        return jobxml.custom_workspace

    @custom_workspace.setter
    def custom_workspace(self, path):
        """Defines a new custom workspace for the job

        :param str path: new custom workspace path
        """
        xml = self.config_xml

        jobxml = JobXML(xml)
        jobxml.custom_workspace = path

        self.config_xml = jobxml.xml

    @staticmethod
    def template_config_xml():
        """XML configuration template for  instantiating jobs of this type

        :returns:
            a basic XML configuration template for use when instantiating
            jobs of this type
        :rtype: :class:`str`
        """
        xml = """<project>
<actions/>
<description/>
<keepDependencies>false</keepDependencies>
<properties/>
<scm class="hudson.scm.NullSCM"/>
<canRoam>true</canRoam>
<disabled>false</disabled>
<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
<triggers/>
<concurrentBuild>false</concurrentBuild>
<builders/>
<publishers/>
<buildWrappers/>
</project>"""
        return xml

    @staticmethod
    def get_jenkins_plugin_name():
        """Gets the name of the Jenkins plugin associated with this PyJen plugin

        This static method is used by the PyJen plugin API to associate this
        class with a specific Jenkins plugin, as it is encoded in the config.xml

        :rtype: :class:`str`
        """
        return "project"


PluginClass = FreestyleJob


if __name__ == "__main__":  # pragma: no cover
    pass