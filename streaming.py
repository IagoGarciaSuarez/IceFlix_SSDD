#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

from os import remove
import sys
from os.path import splitext
from utils import getSHA256, listFiles, removeFile, SERVER_MEDIA_DIR 
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class StreamProvider(IceFlix.StreamProvider):
    def __init__(self, mainService, catalogService, providerAdapter):
        self._mainService = mainService
        self._catalogService = catalogService
        self._prx = providerAdapter

    def getStream(self, id, userToken, current=None):
        auth = self._mainService.getAuthenticator()

        if not auth.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        mediaFilesList = listFiles(SERVER_MEDIA_DIR)

        for media in mediaFilesList:
            if getSHA256(SERVER_MEDIA_DIR + media) == id:
                servant = StreamController(userToken, self._mainService)
                controllerPrx = current.adapter.addWithUUID(servant)
                return IceFlix.StreamControllerPrx.checkedCast(controllerPrx)
        
        raise IceFlix.WrongMediaId(id)

    def isAvailable(self, id, current=None):
        for media in listFiles(SERVER_MEDIA_DIR):
            if getSHA256(SERVER_MEDIA_DIR + media) == id:
                return True
        return False

    def uploadMedia(self, fileName, uploader, adminToken, current=None):
        if not self._mainService.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        #Implementar subida con MediaUploader

        raise IceFlix.UploadError

    def deleteMedia(self, id, adminToken, current=None):
        if not self._mainService.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        if not removeFile(id):
            raise IceFlix.WrongMediaId

class StreamController(IceFlix.StreamController):
    def __init__(self, userToken, mainService):
        self._userToken = userToken
        self._mainService = mainService

    def getSDP(self, userToken, port, current=None):
        auth = self._mainService.getAuthenticator()

        if not auth.isAuthorized(userToken):
            raise IceFlix.Unauthorized
        

    def stop(self, current=None):
        pass

class MediaUploader(IceFlix.MediaUploader):
    def receive(self, size, current=None):
        pass

    def close():
        pass

    def destroy():
        pass

class StreamServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        catalogProxy =  mainService.getCatalog()
        catalogService = IceFlix.MediaCatalogPrx.checkedCast(catalogProxy)
        
        if not catalogService:
            raise RuntimeError('Invalid proxy for the catalog service')


        providerAdapter = broker.createObjectAdapter("ProviderAdapter")
        servant = StreamProvider(mainService, catalogService, providerAdapter)

        providerPrx = providerAdapter.add(servant, broker.stringToIdentity("ProviderService"))
        providerAdapter.activate()

        mediaFilesList = listFiles(SERVER_MEDIA_DIR)
        provider = IceFlix.StreamProviderPrx.checkedCast(providerPrx)
        for media in mediaFilesList:
            catalogService.updateMedia(getSHA256(SERVER_MEDIA_DIR + media),
                                        splitext(media)[0], provider)

        providerAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(StreamServer().main(sys.argv))