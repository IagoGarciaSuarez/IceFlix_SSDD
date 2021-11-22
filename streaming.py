#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class StreamProvider(IceFlix.StreamProvider):
    def getStream(self, current=None):
        pass

class StreamServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        catalogProxy =  mainService.getCatalog()
        catalogService = IceFlix.CatalogPrx.checkedCast(catalogProxy)
        
        if not catalogService:
            raise RuntimeError('Invalid proxy for the catalog service')


        servant = StreamProvider()

        providerAdapter = broker.createObjectAdapter("ProviderAdapter")
        providerPrx = providerAdapter.add(servant, broker.stringToIdentity("ProviderService"))

        providerAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(StreamServer().main(sys.argv))