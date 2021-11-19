#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Catalog(IceFlix.MediaCatalog):
    def isAdmin(self, token, current=None):
        if token == self.properties.getProperty('AdminToken'):
            return True

        return False
        

class CatalogServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        servant = Catalog()

        catalogAdapter = broker.createObjectAdapter("CatalogAdapter")
        catalogPrx = catalogAdapter.add(servant, broker.stringToIdentity("CatalogService"))

        mainService.register(catalogPrx)        

        catalogAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(CatalogServer().main(sys.argv))
