#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
from os.path import splitext
from os import remove
from utils import getSHA256, listFiles, SERVER_MEDIA_DIR
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class StreamProvider(IceFlix.StreamProvider):
    def __init__(self, mainService, catalogService, broker):
        self.mainService = mainService
        self.catalogService = catalogService
        self.broker = broker

    def getStream(self, current=None):
        #No funciona, falta claridad en la definición de esta función.
        #current es none
        controllerServant = StreamController()
        #controllerAdapter = self.broker.createObjectAdapter('StreamController')
        controllerPrx = current.addWithUUID(controllerServant)

        return IceFlix.StreamControllerPrx.checkedCast(controllerPrx)

    def isAvailable(self, id, current=None):
        for media in listFiles(SERVER_MEDIA_DIR):
            if getSHA256(SERVER_MEDIA_DIR + media) == id:
                return True
        return False

    def uploadMedia(self, fileName, uploader, adminToken, current=None):
        if not self.mainService.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        #Implementar subida con MediaUploader

        raise IceFlix.UploadError

    def deleteMedia(self, id, adminToken, current=None):
        if not self.mainService.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        for media in listFiles(SERVER_MEDIA_DIR):
            if getSHA256(SERVER_MEDIA_DIR + media) == id:
                remove(SERVER_MEDIA_DIR + media)
                return
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


        servant = StreamProvider(mainService, catalogService, broker)

        providerAdapter = broker.createObjectAdapter("ProviderAdapter")
        providerPrx = providerAdapter.add(servant, broker.stringToIdentity("ProviderService"))

        mediaFilesList = listFiles(SERVER_MEDIA_DIR)
        for media in mediaFilesList:
            catalogService.updateMedia(getSHA256(SERVER_MEDIA_DIR + media), splitext(media), 
                                        servant.getStream())

        providerAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(StreamServer().main(sys.argv))