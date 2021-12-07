#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de catálogo.
'''

import sys
import Ice # pylint: disable=import-error,wrong-import-position
from utils import CatalogDB, readTagsDB, writeTagsDB, CATALOG_DB
from media import Media, MediaInfo
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position


class Catalog(IceFlix.MediaCatalog):
    '''Clase que implementa la interfaz de IceFlix para el catálogo.'''
    def __init__(self, main_service, catalog):
        self._main_service = main_service
        self._catalog = catalog
        self._media_with_proxy = {}

    def updateMedia(self, media_id, initial_name, provider, current=None): # pylint: disable=invalid-name, unused-argument
        '''Actualiza los datos de un medio.'''
        if not self._catalog.isInCatalog(media_id):
            self._catalog.addMedia(media_id, initial_name)

        self._media_with_proxy[media_id] = []
        self._media_with_proxy[media_id].append(provider)

    def addTags(self, media_id, tags, user_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Añade tags a un medio.'''
        auth = self._main_service.getAuthenticator()

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        if not self._catalog.isInCatalog(media_id):
            raise IceFlix.WrongMediaId(media_id)

        tags_db = readTagsDB()
        username = auth.whois(user_token)

        if username in tags_db and media_id in tags_db[username]:
            for tag in tags:
                tags_db[username][media_id].append(tag)
        else:
            tags_dic = {}
            tags_dic[media_id] = tags
            tags_db[username] = tags_dic

        writeTagsDB(tags_db)

    def removeTags(self, media_id, tags, user_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Elimina tags de un medio.'''
        auth = self._main_service.getAuthenticator()

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        if not self._catalog.isInCatalog(media_id):
            raise IceFlix.WrongMediaId(media_id)

        user = auth.whois(user_token)
        tags_db = readTagsDB()
        tags_db[user][media_id] = [t for t in tags_db[user][media_id] if t not in tags]
        writeTagsDB(tags_db)

    def renameTile(self, media_id, name, adminToken, current=None): # pylint: disable=invalid-name, unused-argument
        '''Renombra un medio.'''
        if not self._main_service.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        if not self._catalog.isInCatalog(media_id):
            raise IceFlix.WrongMediaId(media_id)

        self._catalog.renameMedia(media_id, name)

    def getTile(self, media_id, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene toda la información en forma de objeto Media dado un ID.'''
        if not self._catalog.isInCatalog(media_id):
            raise IceFlix.WrongMediaId(media_id)

        if media_id not in self._media_with_proxy:
            raise IceFlix.TemporaryUnavailable

        tags_db = readTagsDB()
        tag_list = []
        for user in tags_db:
            if media_id in tags_db[user]:
                tag_list = [tag for tag in tags_db[user][media_id]]

        return Media(media_id, self._media_with_proxy[media_id][-1],
                     MediaInfo(self._catalog.getNameById(media_id), tag_list))

    def getTilesByName(self, name, exact, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene el ID de un medio dado un nombre.'''
        tiles_list = self._catalog.getIdByName(name, exact)
        if tiles_list:
            return tiles_list
        return []

    def getTilesByTags(self, tags, include_all_tags, user_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene el ID de un medio dada una lista de tags.'''
        auth = self._main_service.getAuthenticator()

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        tags_db = readTagsDB()
        user = auth.whois(user_token)
        tiles_list = []
        for media in tags_db[user]:
            if include_all_tags and all(tag in tags_db[user][media] for tag in tags):
                tiles_list.append(media)
            elif not include_all_tags and any(tag in tags_db[user][media] for tag in tags):
                tiles_list.append(media)

        return tiles_list


class CatalogServer(Ice.Application):
    '''Clase que implementa el servicio de catálogo.'''
    def run(self, argv): # pylint: disable=arguments-differ
        broker = self.communicator()

        main_proxy = broker.stringToProxy(argv[1])
        main_service = IceFlix.MainPrx.checkedCast(main_proxy)

        if not main_service:
            raise RuntimeError('Invalid proxy for the main service')

        catalog_db = CatalogDB(CATALOG_DB)
        catalog_db.create_table()

        servant = Catalog(main_service, catalog_db)

        catalog_adapter = broker.createObjectAdapter("CatalogAdapter")
        catalog_prx = catalog_adapter.add(
            servant, broker.stringToIdentity("CatalogService"))

        main_service.register(catalog_prx)

        catalog_adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


sys.exit(CatalogServer().main(sys.argv))
