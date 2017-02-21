"""Primitives for interacting with Jenkins views"""
import logging
import xml.etree.ElementTree as ElementTree
from pyjen.job import Job
from pyjen.exceptions import PluginNotSupportedError
from pyjen.utils.pluginapi import PluginBase, get_view_plugins, get_plugin_name, init_extension_plugin
from pyjen.utils.viewxml import ViewXML
from pyjen.utils.jenkins_api import JenkinsAPI
import json


class View(PluginBase, JenkinsAPI):
    """ Abstraction for generic Jenkins views providing interfaces common to all view types

    :param str url: Full URL of a view on a Jenkins master
    """
    def __init__(self, url):
        super(View, self).__init__(url)
        self._type = None
        self._log = logging.getLogger(__name__)

    @property
    def derived_object(self):
        """Looks for a custom plugin supporting the specific type of view managed by this object"""
        # check to see if we're trying to derive an object from an already derived object
        if not isinstance(self, View):
            return self

        plugin = init_extension_plugin(self.url, self._master)
        if plugin is not None:
            return plugin

        raise PluginNotSupportedError("View plugin {0} not found".format(self.type), self.type)

    @property
    def type(self):
        if self._type is None:
            node = ElementTree.fromstring(self._controller.config_xml)
            self._type = get_plugin_name(node)
        return self._type

    @staticmethod
    def supported_types():
        """Returns a list of all view types supported by this instance of PyJen

        These view types can be used in such methods as :py:meth:`~.jenkins.Jenkins.create_view`, which take as input
        a view type classifier

        :return: list of all view types supported by this instance of PyJen, including those supported by plugins
        :rtype: :class:`list` of :class:`str`
        """
        retval = []
        for plugin in get_view_plugins():
            retval.append(plugin.type)

        return retval

    @property
    def name(self):
        """Gets the display name for this view

        This is the name as it appears in the tabbed view
        of the main Jenkins dashboard

        :returns: the name of the view
        :rtype: :class:`str`
        """
        data = self.get_api_data()
        return data['name']

    @property
    def jobs(self):
        """Gets a list of jobs associated with this view

        Views are simply filters to help organize jobs on the
        Jenkins dashboard. This method returns the set of jobs
        that meet the requirements of the filter associated
        with this view.

        :returns: list of 0 or more jobs that are included in this view
        :rtype:  :class:`list` of :class:`~.job.Job` objects
        """
        data = self.get_api_data(query_params="depth=2")

        view_jobs = data['jobs']

        retval = []
        for j in view_jobs:
            # TODO: Find a way to prepoulate api data
            # temp_data_io.set_api_data(j)
            retval.append(Job(j['url'], self._master))

        return retval

    @property
    def job_count(self):
        """Gets the number of jobs contained under this view

        :returns: number of jobs contained under this view
        :rtype: :class:`int`
        """
        data = self.get_api_data()

        return len(data['jobs'])

    @property
    def job_names(self):
        """Gets the list of names of all jobs contained within this view

        :returns: the list of names of all jobs contained within this view
        :rtype: :class:`list` of :class:`str`
        """
        data = self.get_api_data()
        retval = []
        for j in data['jobs']:
            retval.append(j['name'])
        return retval

    @property
    def config_xml(self):
        """Gets the raw configuration data in XML format

        This is an advanced function which allows the caller
        to manually manipulate the raw configuration settings
        of the view. Use with caution.

        This method allows callers to dynamically update arbitrary properties of this view.

        :returns:
            returns the raw XML of the views configuration in
            a plain text string format
        :rtype: :class:`str`
        """
        return self.get_text("/config.xml")

    @config_xml.setter
    def config_xml(self, new_xml):
        """Updates the raw configuration of this view with a new set of properties

        :param str new_xml:
            XML encoded text string to be used as a replacement for the
            current configuration being used by this view.

            NOTE: It is assumed that this input text meets the schema
            requirements for a Jenkins view.
        """
        args = {
            'data': new_xml,
            'headers': {'Content-Type': 'text/xml'}
        }
        self.post(self.url + "config.xml", args)

    def delete(self):
        """Deletes this view from the dashboard"""
        self.post(self.url + "doDelete")

    def delete_all_jobs(self):
        """Batch method that allows callers to do bulk deletes of all jobs found in this view"""

        # TODO: Find a way to leverage the job URLs contained within the View API data to accelerate this process
        #   Maybe we could expose some static methods on the job() base class for doing deletes using an absolute URL
        #   Or maybe we could allow the instantiation of the job() base class for performing basic operations through
        #       the abstract interface, without needing to know the derived class we're using (and hence, avoid having
        #       to make an extra hit on the server for each job just to pull back the config.xml)
        # TODO: Apply this same pattern to other similar batch methods like disable_all_jobs

        for j in self.jobs:
            self._log.debug("Deleting job " + j.name)
            j.delete()

    def disable_all_jobs(self):
        """Batch method that allows caller to bulk-disable all jobs found in this view"""
        for j in self.jobs:
            self._log.debug("Disabling job " + j.name)
            j.disable()

    def enable_all_jobs(self):
        """Batch method that allows caller to bulk-enable all jobs found in this view"""
        for j in self.jobs:
            self._log.debug("Enabling job " + j.name)
            j.enable()

    def clone_all_jobs(self, source_job_name_pattern, new_job_substring):
        """Batch-clones all jobs contained within this view

        :param str source_job_name_pattern:
            pattern to use as a substitution rule when generating new names for cloned jobs. Substrings within the
            existing job names that match this pattern will be replaced by the given substitution string
        :param str new_job_substring:
            character string used to generate new job names for the clones of the existing jobs. The substring
            of an existing job that matches the given regex will be replaced by this new string to create the
            new job name for it's cloned counterpart.
        """
        retval = []
        for cur_job in self.jobs:
            new_name = cur_job.name.replace(source_job_name_pattern, new_job_substring)
            new_job = cur_job.clone(new_name)
            retval.append(new_job)
        return retval

    def clone(self, new_view_name):
        """Make a copy of this view with the specified name

        :param str new_view_name: name of the newly cloned view
        :return: reference to the View object that manages the new, cloned view
        :rtype: :class:`~.view.View`
        """

        view_type = self.type
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            "name": new_view_name,
            "mode": view_type,
            "Submit": "OK",
            "json": json.dumps({"name": new_view_name, "mode": view_type}) # TODO: See if this is necessary
        }

        args = {
            'data': data,
            'headers': headers
        }

        self.post(self.url + 'createView', args)

        new_url = self.url.replace(self.name, new_view_name)
        new_view = View(new_url)

        vxml = ViewXML(self.config_xml)
        vxml.rename(new_view_name)
        new_view.config_xml = vxml.xml
        return new_view

    def rename(self, new_name):
        """Rename this view

        :param str new_name: new name for this view
        """
        new_view = self.clone(new_name)
        self.delete()
        return new_view

    def view_metrics(self):
        """Composes a report on the jobs contained within the view

        :return: Dictionary containing metrics about the view
        :rtype: :class:`dict`
        """
        data = self.get_api_data()

        broken_jobs = []
        disabled_jobs = []
        unstable_jobs = []
        broken_job_count = 0
        disabled_jobs_count = 0
        unstable_job_count = 0

        for job in data["jobs"]:

            # TODO: Figure out how to prepopulate name field here
            #temp_job = Job._create(temp_data_io, self._master, job['name'])
            temp_job = Job(job['url'])

            if job["color"] == "red":
                broken_job_count += 1
                broken_jobs.append(temp_job)
            elif job["color"] == "disabled":
                disabled_jobs_count += 1
                disabled_jobs.append(temp_job)
            elif job["color"] == "yellow":
                unstable_job_count += 1
                unstable_jobs.append(temp_job)

        return {"broken_jobs_count": broken_job_count,
                "disabled_jobs_count": disabled_jobs_count,
                "unstable_jobs_count": unstable_job_count,
                "broken_jobs": broken_jobs,
                "unstable_jobs": unstable_jobs,
                "disabled_jobs": disabled_jobs}

if __name__ == "__main__":  # pragma: no cover
    #for i in View.supported_types():
    #    print(i)
    pass
