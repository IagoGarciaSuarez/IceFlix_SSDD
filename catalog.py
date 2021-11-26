#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
from utils import TAGS_DB, CatalogDB, readTagsDB, writeTagsDB
from media import Media, MediaInfo
import json
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Catalog(IceFlix.MediaCatalog):
    # ====== tagsDB structure ======
    # {
    #     String username: {
    #         String media_id: List<String> tags
    #     }
    # }
    def __init__(self, mainService, catalog):
        self._mainService = mainService
        self._catalog = catalog
        self._mediaWithProxy = {}

    def updateMedia(self, id, initialName, provider, current=None): 
        if not self._catalog.isInCatalog(id):
            self._catalog.addMedia(id, initialName)
            self._mediaWithProxy[id] = []
        
        self._mediaWithProxy[id].append(provider)

    def addTags(self, id, tags, userToken, current=None):
        auth = self._mainService.getAuthenticator()

        if not auth.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        if not self._catalog.isInCatalog(id):
            raise IceFlix.WrongMediaId(id)

        #Needs change if tags is not passed as a List object
        tagsDB = readTagsDB()

        for tag in tags:
            tagsDB[auth.whois(userToken)][id].append(tag)

        writeTagsDB(tagsDB)

    def removeTags(self, id, tags, userToken, current=None):
        auth = self._mainService.getAuthenticator()

        if not auth.isAuthorized(userToken):
            raise IceFlix.Unauthorized

        if not self._catalog.isInCatalog(id):
            raise IceFlix.WrongMediaId(id)
        
        user = auth.whois(userToken)
        #Needs change if tags is not passed as a List object
        tagsDB = readTagsDB()
        tagsDB[user][id] = [t for t in tagsDB[user][id] if t not in tags]
        tagsDB = writeTagsDB(tagsDB)

    def renameTile(self, id, name, adminToken):
        if not self._mainService.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        if not self._catalog.isInCatalog(id):
            raise IceFlix.WrongMediaId(id)
        
        self._catalog.renameMedia(id, name)    
        
    def getTile(self, id, current=None):
        if not self._catalog.isInCatalog(id):
            raise IceFlix.WrongMediaId(id)
        
        elif id not in self._mediaWithProxy:
            raise IceFlix.TemporaryUnavailable

        tagsDB = readTagsDB()
        for user in tagsDB:
            for media in tagsDB[user]:
                tags = [tag for tag in tags for tags in tagsDB[media]]
        #Check struct media object
        return Media(id, self._mediaWithProxy[id][-1], 
                MediaInfo(self._catalog.getNameById(id), tags))

    def getTilesByName(self, name, exact, current=None):        
        tilesList = self._catalog.getIdByName(name, exact)
        if tilesList:
            return tilesList
        return []
        
    def getTilesbyTags(self, tags, includeAllTags, userToken):
        auth = self._mainService.getAuthenticator()

        if not auth.isAuthorized(userToken):
            raise IceFlix.Unauthorized
        
        tagsDB = readTagsDB()
        user = auth.whois(userToken)
        tilesList = []
        for media in tagsDB[user]:
            if includeAllTags and all(tag in tagsDB[user][media] for tag in tags):
                tilesList.append(media)
            elif not includeAllTags and any(tag in tagsDB[user][media] for tag in tags):
                tilesList.append(media)

        return tilesList
                

class CatalogServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        catalog_db = CatalogDB('catalog.db')

        servant = Catalog(mainService, catalog_db)

        catalogAdapter = broker.createObjectAdapter("CatalogAdapter")
        catalogPrx = catalogAdapter.add(servant, broker.stringToIdentity("CatalogService"))

        mainService.register(catalogPrx)        

        catalogAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(CatalogServer().main(sys.argv))
