#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
from utils import CatalogDB
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Catalog(IceFlix.MediaCatalog):
    def __init__(self, catalog):
        self._catalog = catalog
        self._mediaWithProxy = {}

    def updateMedia(self, id, initialName, provider, current=None): 
        if not self._catalog.isInCatalog(id):
            self._catalog.addMedia(id, initialName)

        self._mediaWithProxy[id] = provider

    def getTile(self, id, current=None):
        if not self._catalog.isInCatalog(id):
            raise IceFlix.WrongMediaId(id)
        
        elif id not in self._mediaWithProxy:
            raise IceFlix.TemporaryUnavailable

        #Add struct media object

    def getTilesByName(self, name, exact, current=None):
        if exact:
            return self._catalog.getByName(name)
        return self._catalog.getWithName(name)
        

class CatalogServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        catalog_db = CatalogDB('catalog.db')

        servant = Catalog(catalog_db)

        catalogAdapter = broker.createObjectAdapter("CatalogAdapter")
        catalogPrx = catalogAdapter.add(servant, broker.stringToIdentity("CatalogService"))

        mainService.register(catalogPrx)        

        catalogAdapter.activate()
        self.shutdownOnInterrupt()
        catalog_db.closeConnection()
        broker.waitForShutdown()

        return 0

sys.exit(CatalogServer().main(sys.argv))
