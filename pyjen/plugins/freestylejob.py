"""Primitives that manage Jenkins job of type 'Freestyle'"""
from pyjen.job import Job
from pyjen.user_params import JenkinsConfigParser
from pyjen.utils.datarequester import DataRequester
from pyjen.exceptions import InvalidJenkinsURLError
from pyjen.utils.jobxml import JobXML


class FreestyleJob(Job):
    """Jenkins job of type 'freestyle' """
    type = "project"

    def __init__(self, controller, jenkins_master):
        """Constructor

        To instantiate an instance of this class using auto-generated
        configuration parameters, see the :py:func:`easy_connect` method

        :param obj data_io_controller:
            class capable of handling common HTTP IO requests sent by this
            object to the Jenkins REST API
        """
        super(FreestyleJob, self).__init__(controller, jenkins_master)

    @staticmethod
    def easy_connect(url, credentials=None):
        """Factory method to simplify creating connections to Jenkins servers

        :param str url: Full URL of the Jenkins instance to connect to. Must be
            a valid running Jenkins instance.
        :param tuple credentials: A 2-element tuple with the username and
            password for authenticating to the URL
            If omitted, credentials will be loaded from any pyjen config files found on the system
            If no credentials can be found, anonymous access will be used
        :returns: :py:mod:`pyjen.Jenkins` object, pre-configured with the
            appropriate credentials and connection parameters for the given URL.
        :rtype: :py:mod:`pyjen.Jenkins`
        """
        # Default to anonymous access
        username = None
        password = None

        # If not explicit credentials provided, load credentials from any config files
        if not credentials:
            config = JenkinsConfigParser()
            config.read(JenkinsConfigParser.get_default_configfiles())
            credentials = config.get_credentials(url)

        # If explicit credentials have been found, use them rather than use anonymous access
        if credentials:
            username = credentials[0]
            password = credentials[1]

        http_io = DataRequester(url, username, password)
        retval = FreestyleJob(http_io, None)

        # Sanity check: make sure we can successfully parse the view's name from the IO controller
        # to make sure we have a valid configuration
        try:
            name = retval.name
        except:
            raise InvalidJenkinsURLError("Invalid connection parameters provided to PyJen.Job. \
                Please check configuration.", http_io)
        if name is None or name == "":
            raise InvalidJenkinsURLError("Invalid connection parameters provided to PyJen.Job. \
                Please check configuration.", http_io)

        return retval

    @property
    def scm(self):
        """Gets the object that manages the source code management configuration for a job

        :returns:
            One of several possible plugin objects which exposes the relevant set
            of properties supported by a given source code management tool.
        :rtype: :py:class:`pyjen.utils.pluginapi.pluginxml`
        """
        xml = self.config_xml
        jobxml = JobXML(xml)
        return jobxml.scm()

    @property
    def custom_workspace(self):
        xml = self.config_xml

        jobxml = JobXML(xml)
        return jobxml.custom_workspace

    @custom_workspace.setter
    def custom_workspace(self, path):
        """Defines a new custom workspace for the job

        If this job is already using a custom workspace it
        will be updated to the new path provided.

        :param str path: new custom workspace path
        """
        xml = self.config_xml

        jobxml = JobXML(xml)
        jobxml.custom_workspace = path

        self.set_config_xml(jobxml.XML)

    @staticmethod
    def template_config_xml():
        """Gets a basic XML configuration template for use when instantiating jobs of this type

        :returns: a basic XML configuration template for use when instantiating jobs of this type
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


if __name__ == "__main__":  # pragma: no cover
    pass
