##################################################
# ./SecurityuserimportImplService_services.py
# generated by ZSI.wsdl2python
#
#
##################################################


import urllib.parse, types
from ZSI.TCcompound import Struct
from ZSI import client
import ZSI


class SecurityuserimportImplServiceInterface:
    def getSecurityuserimportImpl(self, portAddress=None, **kw):
        raise NonImplementationError("method not implemented")


class SecurityuserimportImplServiceLocator(SecurityuserimportImplServiceInterface):
    SecurityuserimportImpl_address = (
        "https://gama.nbcr.net:9443/axis/services/SecurityUserImportService"
    )

    def getSecurityuserimportImplAddress(self):
        return SecurityuserimportImplServiceLocator.SecurityuserimportImpl_address

    def getSecurityuserimportImpl(self, portAddress=None, **kw):
        return SecurityUserImportServiceSoapBindingSOAP(
            portAddress
            or SecurityuserimportImplServiceLocator.SecurityuserimportImpl_address,
            **kw
        )


class SecurityUserImportServiceSoapBindingSOAP:
    def __init__(self, addr, **kw):
        netloc = (urllib.parse.urlparse(addr)[1]).split(":") + [
            80,
        ]
        if "host" not in kw:
            kw["host"] = netloc[0]
        if "port" not in kw:
            kw["port"] = int(netloc[1])
        if "url" not in kw:
            kw["url"] = urllib.parse.urlparse(addr)[2]
        self.binding = client.Binding(**kw)

    def listUsers(self, request):
        """
        @param: request to listUsersRequest
        @return: response from listUsersResponse::
          _listUsersReturn: str
        """

        if not isinstance(request, listUsersRequest) and not issubclass(
            listUsersRequest, request.__class__
        ):
            raise TypeError("%s incorrect request type" % (request.__class__))
        kw = {}
        response = self.binding.Send(None, None, request, soapaction="", **kw)
        response = self.binding.Receive(listUsersResponseWrapper())

        if not isinstance(response, listUsersResponse) and not issubclass(
            listUsersResponse, response.__class__
        ):
            raise TypeError("%s incorrect response type" % (response.__class__))
        return response


class listUsersRequest(ZSI.TCcompound.Struct):
    def __init__(self, name=None, ns=None):

        oname = None
        if name:
            oname = name
            if ns:
                oname += ' xmlns="%s"' % ns
            ZSI.TC.Struct.__init__(
                self, listUsersRequest, [], pname=name, aname="%s" % name, oname=oname
            )


class listUsersRequestWrapper(listUsersRequest):
    """wrapper for rpc:encoded message"""

    typecode = listUsersRequest(name="listUsers", ns="urn:axis")

    def __init__(self, name=None, ns=None, **kw):
        listUsersRequest.__init__(self, name="listUsers", ns="urn:axis")


class listUsersResponse(ZSI.TCcompound.Struct):
    def __init__(self, name=None, ns=None):
        self._listUsersReturn = None

        oname = None
        if name:
            oname = name
            if ns:
                oname += ' xmlns="%s"' % ns
            ZSI.TC.Struct.__init__(
                self,
                listUsersResponse,
                [
                    ZSI.TC.String(
                        pname="listUsersReturn", aname="_listUsersReturn", optional=1
                    ),
                ],
                pname=name,
                aname="%s" % name,
                oname=oname,
            )


class listUsersResponseWrapper(listUsersResponse):
    """wrapper for rpc:encoded message"""

    typecode = listUsersResponse(name="listUsersResponse", ns="urn:axis")

    def __init__(self, name=None, ns=None, **kw):
        listUsersResponse.__init__(self, name="listUsersResponse", ns="urn:axis")
