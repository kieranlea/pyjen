from pyjen.build import build
from pyjen.utils.job_xml import job_xml
from pyjen.utils.data_requester import data_requester
from pyjen.utils.common import get_root_url

class job(object):
    """Interface to all primitives associated with a Jenkins job"""
    
    def __init__ (self, url, http_io_class=data_requester):
        """Constructor
        
        :param str url: URL of the job to be managed. This may be a full URL, starting with
            the root Jenkins URL, or a partial URL relative to the Jenkins root
            
            Examples: 
                * 'http://jenkins/jobs/job1'
                * 'jobs/job2'
                
        :param obj http_io_class:
            class capable of handling HTTP IO requests between
            this class and the Jenkins REST API
            If not explicitly defined a standard IO class will be used 
        """
        self.__requester = http_io_class(url)
        
        
    def get_name(self):
        """Returns the name of the job managed by this object
        
        :returns: The name of the job
        :rtype: :func:`str`
        """
        data = self.__requester.get_api_data()      
        return data['name']
    
    def get_url(self):
        """Gets the full URL for the main web page for this job
        
        :returns: URL of the main web page for the job
        :rtype: :func:`str`
        """
        return self.__requester.url
    
    
    
    def get_recent_builds(self):
        """Gets a list of the most recent builds for this job
        
        Rather than returning all data on all available builds, this
        method only returns the latest 20 or 30 builds. This list is
        synonymous with the short list provided on the main info
        page for the job on the dashboard.
        
        :rtype: :func:`list` of :py:mod:`pyjen.build` objects
        """
        data = self.__requester.get_api_data()
        
        builds = data['builds']
        
        retval = []
        for b in builds:
            retval.append(build(b['url']))
        
        return retval
    
    def get_downstream_jobs(self, recursive=False):
        """Gets the list of immediate downstream dependencies for this job
        
        :param bool recursive:
            Set to True to recursively scan all downstream jobs
            for their downstream dependencies and return the complete
            list of all dependencies
            
            Set to False to only report the immediate downstream
            dependencies - those directly triggered by this job.
            
            Defaults to False
        :returns: 
            A dictionary of 0 or more jobs which depend on this one
            the keys in the dictionary are the names of the jobs that
            were found in the dependency search
        :rtype:  :class:`dict` with :func:`str` job names for keys, and :py:mod:`pyjen.job` objects for values
        """
        data = self.__requester.get_api_data()
        
        jobs = data['downstreamProjects']
        
        retval = {}
        
        
        for j in jobs:
            temp = job(j['url'])
            retval[temp.get_name()] = temp
            if recursive:
                retval.update(temp.get_downstream_jobs(recursive))
        
        return retval
    
    def get_upstream_jobs(self, recursive=False):
        """Gets the list of upstream dependencies for this job
        
        :param bool recursive:
            Set to True to recursively scan all upstream jobs
            for their upstream dependencies and return the complete
            list of all dependencies
            
            Set to False to only report the immediate upstream
            dependencies - those that directly trigger this job.
            
            Defaults to False
            
        :returns:
            A dictionary of 0 or more jobs that this job depends on
            the keys in the dictionary are the names of the jobs that
            were found in the dependency search
        :rtype: :class:`dict` with :func:`str` job names for keys and :py:mod:`pyjen.job` objects for values
        """
        data = self.__requester.get_api_data()
        
        jobs = data['upstreamProjects']
        
        retval = {}
                
        for j in jobs:
            temp = job(j['url'])
            retval[temp.get_name()] = temp
            if recursive:
                retval.update(temp.get_upstream_jobs(recursive))
        
        return retval    
        
    def get_last_good_build(self):
        """Gets the most recent successful build of this job
        
        Synonymous with the "Last successful build" permalink on the jobs' main status page
        
        
        :returns:
            object that provides information and control for the
            last build which completed with a status of 'success'
            If there are no such builds in the build history, this method returns None
        :rtype: :py:mod:`pyjen.build`
        """
        data = self.__requester.get_api_data()
        
        lgb = data['lastSuccessfulBuild']
        
        if lgb == None:
            return None
        
        return build(lgb['url'])
        
    def get_last_build(self):
        """Returns a reference to the most recent build of this job
        
        Synonymous with the "Last Build" permalink on the jobs' main status page
        
        :returns:
            object that provides information and control for the
            most recent build of this job.
            If there are no such builds in the build history, this method returns None
        :rtype: :py:mod:`pyjen.build`
        """
        data = self.__requester.get_api_data()
        
        last_build = data['lastBuild']
        
        if last_build == None:
            return None
        
        return build (last_build['url'])
    
    def get_last_failed_build(self):
        """Returns a reference to the most recent build of this job with a status of "failed"
        
        Synonymous with the "Last failed build" permalink on the jobs' main status page
        
        :returns:
            Most recent build with a status of 'failed'
            If there are no such builds in the build history, this method returns None
        :rtype: :py:mod:`pyjen.build`
        """
        data = self.__requester.get_api_data()
        
        bld = data['lastFailedBuild']
        
        if bld == None:
            return None
        
        return build(bld['url'])
                
    def get_last_stable_build(self):
        """Returns a reference to the most recent build of this job with a status of "stable"
        
        Synonymous with the "Last stable build" permalink on the jobs' main status page
        
        
        :returns:
            Most recent build with a status of 'stable'
            If there are no such builds in the build history, this method returns None
        :rtype: :py:mod:`pyjen.build`
        """
        data = self.__requester.get_api_data()

        bld = data['lastCompletedBuild']
        
        if bld == None:
            return None
        
        return build(bld['url'])
    
    def get_last_unsuccessful_build(self):
        """Returns a reference to the most recent build of this job with a status of "unstable"
        
        Synonymous with the "Last unsuccessful build" permalink on the jobs' main status page
        
        :returns:
            Most recent build with a status of 'unstable'
            If there are no such builds in the build history, this method returns None
        :rtype: :py:mod:`pyjen.build`
        """
        data = self.__requester.get_api_data()

        bld = data['lastUnsuccessfulBuild']
        
        if bld == None:
            return None
        
        return build(bld['url'])    
        
    def get_build_by_number(self, build_number):
        """Gets a specific build of this job from the build history
        
        :param int build_number:
            Numeric identifier of the build to retrieve
            Value is typically non-negative
        :returns:
            Build object for the build with the given numeric identifier
            If such a build does not exist, returns None
        :rtype: :py:mod:`pyjen.build`
        """
        try:
            data = self.__requester.get_data("/" + str(build_number)  + "/api/python")
        except AssertionError:
            #TODO: Find a more elegant way to detect whether the build exists or not
            return None
        
        return build(data['url'])
    
    def start_build(self):
        """Forces a build of this job
        
        Synonymous with a manual trigger. A new instance
        of the job (ie: a build) will be added to the
        appropriate build queue where it will be scheduled
        for execution on the next available agent + executor.
        """
        self.__requester.post("/build")
        
    def disable(self):
        """Disables this job
        
        Sets the state of this job to disabled so as to prevent the 
        job from being triggered.
        
        Use in conjunction with the :py:func:`enable` and :py:func:`is_disabled`
        methods to control the state of the job.
        """
        self.__requester.post("/disable")
        
    def enable(self):
        """Enables this job
        
        If this jobs current state is disabled, it will be
        re-enabled after calling this method. If the job
        is already enabled then this method does nothing.
        
        Enabling a job allows it to be triggered, either automatically
        via commit hooks / polls or manually through the dashboard.
        
        Use in conjunction with the :py:func:`disable` and :py:func:`is_disabled` methods
        """
        self.__requester.post("/enable")
        
    def is_disabled(self):
        """Indicates whether this job is disabled or not
        
        :returns:
            true if the job is disabled, otherwise false
        :rtype: :func:`bool`
        """
        data = self.__requester.get_api_data()
        
        return (data['color'] == "disabled")
        
        
    def delete (self):
        """Deletes this job from the Jenkins dashboard"""
        self.__requester.post("/doDelete")
        
    def get_config_xml(self):
        """Gets the raw XML configuration for the job
        
        Used in conjunction with the set_config_xml method,
        callers are free to manipulate the raw job configuration
        as desired.
        
        :returns:
            the full XML tree describing this jobs configuration
        :rtype: :func:`str`
        """
        return self.__requester.get_text('/config.xml')
    
    def set_config_xml(self, new_xml):
        """Allows a caller to manually override the entire job configuration
        
        WARNING: This is an advanced method that should only be used in
        rare circumstances. All configuration changes should normally
        be handled using other methods provided on this class.
        
        :param str new_xml:
            A complete XML tree compatible with the Jenkins API
        """
        headers = {'Content-Type': 'text/xml'}
        args = {}
        args['data'] = new_xml
        args['headers'] = headers
        
        self.__requester.post("/config.xml", args)
        
    def set_custom_workspace(self, path):
        """Defines a new custom workspace for the job
        
        If this job is already using a custom workspace it
        will be updated to the new path provided.
        
        :param str path: new custom workspace path
        """
        xml = self.get_config_xml()
        
        jobxml = job_xml(xml)
        jobxml.set_custom_workspace(path)
        
        self.set_config_xml(jobxml.get_xml())
        
    def get_scm(self):
        """Gets the object that manages the source code management configuration for a job
        
        :returns:
            One of several possible plugin objects which exposes the relevant set
            of properties supported by a given source code management tool.
        :rtype: :py:class:`pyjen.plugins.pluginbase`    
        """
        xml = self.get_config_xml()
        jobxml = job_xml(xml)
        return jobxml.get_scm()

    def get_builds_in_time_range(self, startTime, endTime):
        """ Returns a list of all of the builds for a job that 
            occurred between the specified start and end times
            
            :param datetime startTime: 
                    starting time index for range of builds to find
            :param datetime endTime:
                    ending time index for range of builds to find
            :returns: a list of 0 or more builds
            :rtype: :class:`list` of :py:mod:`pyjen.build` objects            
        """       
        builds = []                
        
        for run in self.get_recent_builds():            
            if (run.get_build_time() < startTime):
                break
            elif (run.get_build_time() >= startTime and run.get_build_time() <= endTime):
                builds.append(run)                               
        return builds
        
    def clone(self, new_job_name):
        """Makes a copy of this job on the dashboard with a new name        
        
        :param str new_job_name:
            the name of the newly created job whose settings will
            be an exact copy of this job. It is expected that this
            new job name be unique across the dashboard.
            
        :returns: a reference to the newly created job resulting
            from the clone operation
        :rtype: :py:mod:`pyjen.job`
        """
        #TODO: Need to relocate this method to the Jenkins class
        params = {'name': new_job_name,
                  'mode': 'copy',
                  'from': self.get_name()}
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
        args = {}
        args['params'] = params
        args['data'] = ''
        args['headers'] = headers
        
        dashboard_url = get_root_url(self.get_url())
        self.__requester.post_url(dashboard_url + "/createItem", args)
        
        new_job_url = dashboard_url + "/job/" + new_job_name + "/"
        new_job = job(new_job_url)
        
        # Sanity check - lets make sure the job actually exists by checking its name
        assert(new_job.get_name() == new_job_name)
        
        #as a precaution, lets disable the newly created job so it doesn't automatically start running
        new_job.disable()
        
        return new_job 

if __name__ == "__main__":
    j = job("http://localhost:8080/job/test_job_1")
    print (j.get_last_build().get_build_number())
    pass