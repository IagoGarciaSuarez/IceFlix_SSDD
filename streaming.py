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

    def getStream(self, current=None):
        #No funciona, falta claridad en la definición de esta función.
        #current es none
        #controllerAdapter = self.broker.createObjectAdapter('StreamController')
        controllerPrx = self._prx.addWithUUID(self)

        return IceFlix.StreamProviderPrx.checkedCast(controllerPrx)

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
            #No debería borrar también la entrada del catálogo y del almacén de proxies?
            raise IceFlix.WrongMediaId

class StreamController(IceFlix.StreamController):
    def getSDP(self, userToken, port, current=None):
        pass

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
        #servant = StreamProvider(mainService, catalogService, providerAdapter)

        #providerPrx = providerAdapter.add(servant, broker.stringToIdentity("ProviderService"))

        mediaFilesList = listFiles(SERVER_MEDIA_DIR)
        for media in mediaFilesList:
            catalogService.updateMedia(getSHA256(SERVER_MEDIA_DIR + media),
                                        splitext(media)[0], providerAdapter)

        providerAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(StreamServer().main(sys.argv))