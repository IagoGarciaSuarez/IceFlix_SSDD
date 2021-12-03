#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de streaming.
'''
import sys
from os.path import splitext
import Ice # pylint: disable=import-error,wrong-import-position
from utils import getSHA256, listFiles, removeFile, SERVER_MEDIA_DIR
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class StreamProvider(IceFlix.StreamProvider):
    '''Clase que implementa la interfaz de IceFlix para el stream provider.'''
    def __init__(self, main_service, catalog_service, provider_adapter):
        self._main_service = main_service
        self._catalog_service = catalog_service
        self._prx = provider_adapter

    def getStream(self, media_id, user_token, current=None):# pylint: disable=invalid-name
        '''Comprueba que el token es válido y devuelve un objeto stream controller.'''
        auth = self._main_service.getAuthenticator()

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        media_files_list = listFiles(SERVER_MEDIA_DIR)

        for media in media_files_list:
            if getSHA256(SERVER_MEDIA_DIR + media) == media_id:
                servant = StreamController(user_token, self._main_service)
                controller_prx = current.adapter.addWithUUID(servant)
                return IceFlix.StreamControllerPrx.checkedCast(controller_prx)

        raise IceFlix.WrongMediaId(media_id)

    def isAvailable(self, media_id, current=None): # pylint: disable=invalid-name, unused-argument, no-self-use
        '''Comprueba si el medio está disponible.'''
        for media in listFiles(SERVER_MEDIA_DIR):
            if getSHA256(SERVER_MEDIA_DIR + media) == media_id:
                return True
        return False

    def uploadMedia(self, fileName, uploader, adminToken, current=None): # pylint: disable=invalid-name, unused-argument
        '''Sube un medio al servidor.'''
        if not self._main_service.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        # Implementar subida con MediaUploader

        raise IceFlix.UploadError

    def deleteMedia(self, media_id, adminToken, current=None): # pylint: disable=invalid-name, unused-argument
        '''Elimina un medio dado su id si el token de administración es válido.'''
        if not self._main_service.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        if not removeFile(media_id):
            raise IceFlix.WrongMediaId


class StreamController(IceFlix.StreamController):
    '''Clase que implementa la interfaz de IceFlix para el stream controller.'''
    def __init__(self, user_token, main_service):
        self._user_token = user_token
        self._main_service = main_service

    def getSDP(self, user_token, port, current=None): # pylint: disable=invalid-name, unused-argument
        '''Devuelve la configuración del flujo RTSP para la reproducción del vídeo.'''
        auth = self._main_service.getAuthenticator()

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

    def stop(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Interrumpe la reproducción de vídeo.'''


class MediaUploader(IceFlix.MediaUploader):
    '''Clase que implementa la interfaz de IceFlix para el media uploader.'''
    def receive(self, size, current=None):
        '''Recibe los datos.'''

    def close(self):
        '''Cierra el archivo.'''

    def destroy(self):
        '''Destruye el archivo.'''


class StreamServer(Ice.Application):
    '''Clase que implementa a interfaz de IceFlix para el servicio de streaming.'''
    def run(self, argv): # pylint: disable=arguments-differ
        broker = self.communicator()

        main_proxy = broker.stringToProxy(argv[1])
        main_service = IceFlix.MainPrx.checkedCast(main_proxy)

        if not main_service:
            raise RuntimeError('Invalid proxy for the main service')

        catalog_proxy = main_service.getCatalog()
        catalog_service = IceFlix.MediaCatalogPrx.checkedCast(catalog_proxy)

        if not catalog_service:
            raise RuntimeError('Invalid proxy for the catalog service')

        provider_adapter = broker.createObjectAdapter("ProviderAdapter")
        servant = StreamProvider(main_service, catalog_service, provider_adapter)

        provider_prx = provider_adapter.add(
            servant, broker.stringToIdentity("ProviderService"))
        provider_adapter.activate()

        media_files_list = listFiles(SERVER_MEDIA_DIR)
        provider = IceFlix.StreamProviderPrx.checkedCast(provider_prx)
        for media in media_files_list:
            catalog_service.updateMedia(
                getSHA256(SERVER_MEDIA_DIR + media), splitext(media)[0], provider)

        provider_adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


sys.exit(StreamServer().main(sys.argv))
