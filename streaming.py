#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
from os.path import splitext
from utils import getSHA256, listFiles
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class StreamProvider(IceFlix.StreamProvider):
    def __init__(self, mainService, catalogService, broker):
        self.mainService = mainService
        self.catalogService = catalogService
        self.broker = broker

    def getStream(self, current=None):
        #NO GENERA DISTINTOS PRX
        controllerServant = StreamController()

        controllerAdapter = self.broker.createObjectAdapter("ControllerAdapter")
        controllerPrx = controllerAdapter.add(controllerServant, self.broker.stringToIdentity("ControllerService"))

        return controllerPrx

    def isAvailable(self, id, current=None):
        return True

    def uploadMedia(self, current=None):
        pass

    def deleteMedia(self, current=None):
        pass

class StreamController(IceFlix.StreamController):
    def getSDP(self, userToken, port, current=None):
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

        mediaDir = 'media/'
        mediaFilesList = listFiles(mediaDir)
        for media in mediaFilesList:
            catalogService.updateMedia(getSHA256(mediaDir + media), splitext(media), servant.getStream())

        providerAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(StreamServer().main(sys.argv))