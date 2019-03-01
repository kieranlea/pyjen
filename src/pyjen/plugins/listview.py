"""Primitives that operate on Jenkins views of type 'List'"""
from pyjen.view import View


class ListView(View):
    """all Jenkins related 'view' information for views of type ListView

    Instances of this class are typically instantiated directly or indirectly
    through :py:meth:`pyjen.View.create`
    """

    def __init__(self, url):
        """constructor

        To instantiate an instance of this class using auto-generated
        configuration parameters, see the :py:func:`easy_connect` method

        :param obj data_io_controller:
            class capable of handling common HTTP IO requests sent by this
            object to the Jenkins REST API
        """
        super(ListView, self).__init__(url)

    @staticmethod
    def get_jenkins_plugin_name():
        """Gets the name of the Jenkins plugin associated with this PyJen plugin

        This static method is used by the PyJen plugin API to associate this
        class with a specific Jenkins plugin, as it is encoded in the config.xml

        :rtype: :class:`str`
        """
        return "listview"

PluginClass = ListView


if __name__ == "__main__":  # pragma: no cover
    pass