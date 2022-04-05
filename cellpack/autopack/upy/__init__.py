def getHClass(host):
    """
    Return the base class for modelling design according the provide host.

    @type  host: string
    @param host: name of the host application

    @rtype:   Class
    @return:  the specific ui class
    """
    # print globals()

    if host == "simularium":
        from .simularium.simularium_helper import simulariumHelper as helper

        # from .dejavuTk.dejavuHelper import dejavuHelper as helper
    else:
        helper = None
    return helper


def retrieveHost():
    """
    Retrieve the 3d host application where the script is running.

    @rtype:   string
    @return:  the name of the host, ie blender, maya or c4d
    """
    global host
    host = "simularium"
    return host


def getHelperClass(host=None):
    """
    Return the base class for modelling design according the provide host.
    If the host is not provide,retrieveHost() will be called to guess the host.

    @type  host: string
    @param host: name of the host application

    @rtype:   Class
    @return:  the specific ui class
    """
    global helper
    if host is None:
        host = retrieveHost()
    if not host:
        return None
    helper = getHClass(host)
    return helper
