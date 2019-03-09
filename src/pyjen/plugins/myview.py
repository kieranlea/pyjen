"""Primitives for interacting with Jenkins views of type 'MyView'"""
import logging
from pyjen.view import View


class MyView(View):
    """Interface to a view associated with a specific user

    Instances of this class are typically instantiated directly or indirectly
    through :py:meth:`pyjen.View.create`

    :param api:
        Pre-initialized connection to the Jenkins REST API
    :param parent:
        PyJen object that "owns" this view. Typically this is a reference to
        the :class:`pyjen.jenkins.Jenkins` object for the current Jenkins
        instance but in certain cases this may be a different object like
        a :class:`pyjen.plugins.nestedview.NestedView`.

        The parent object is expected to expose a method named `create_view`
        which can be used to clone instances of this view.
    :type api: :class:`~/utils/jenkins_api/JenkinsAPI`
    """

    def __init__(self, api, parent):
        super(MyView, self).__init__(api, parent)
        self._log = logging.getLogger(__name__)

    @staticmethod
    def get_jenkins_plugin_name():
        """Gets the name of the Jenkins plugin associated with this PyJen plugin

        This static method is used by the PyJen plugin API to associate this
        class with a specific Jenkins plugin, as it is encoded in the config.xml

        :rtype: :class:`str`
        """
        return "hudson.model.MyView"


PluginClass = MyView


if __name__ == "__main__":  # pragma: no cover
    pass
