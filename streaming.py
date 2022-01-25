#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de streaming.
'''
from os.path import splitext, isfile, getsize
import threading
import random
import uuid
import sys
import Ice
import utils
from discover import Discover
from iceflixrtsp import RTSPEmitter
import topics
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class StreamProvider(IceFlix.StreamProvider):
    '''Clase que implementa la interfaz de IceFlix para el stream provider.'''
    def __init__(self, broker):
        self._srv_id = str(uuid.uuid4())
        self.media_dir = utils.SERVER_MEDIA_DIR
        self.broker = broker
        self.discover_subscriber = None
        self.stream_announcements_publisher = None

    @property
    def service_id(self):
        """Get instance ID."""
        return self._srv_id

    def getStream(self, media_id, user_token, current=None): # pylint: disable=invalid-name
        '''Comprueba que el token es válido y devuelve un objeto stream controller.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))

        try:
            auth = main_service.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print(
                '\n[PROVIDER SERVICE][ERROR] No se ha podido ' +
                'encontrar un servicio de autenticación.\n')
            return ''

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        media_files_list = utils.list_files(self.media_dir)

        for media in media_files_list:
            if utils.get_sha256(self.media_dir + media) == media_id:
                servant = StreamController(user_token, media, self.media_dir)
                controller_prx = current.adapter.addWithUUID(servant)
                controller_topic = controller_topic = topics.getTopic(topics.getTopicManager(
                    self.broker), servant.getSyncTopic())
                publisher = controller_topic.getPublisher()
                servant.stream_sync = IceFlix.StreamSyncPrx.uncheckedCast(publisher)
                return IceFlix.StreamControllerPrx.checkedCast(controller_prx)

        raise IceFlix.WrongMediaId(media_id)

    def isAvailable(self, media_id, current=None): # pylint: disable=invalid-name, unused-argument, no-self-use
        '''Comprueba si el medio está disponible.'''
        for media in utils.list_files(self.media_dir):
            if utils.get_sha256(self.media_dir + media) == media_id:
                return True
        return False

    def reannounceMedia(self, srv_id, current=None): # pylint: disable=invalid-name, unused-argument, no-self-use
        '''Reanuncia los medios disponibles. Si el servicio que lo pide es conocido.'''
        if srv_id not in self.discover_subscriber.known_services:
            raise IceFlix.UnknownService

        media_files_list = utils.list_files(self.media_dir)
        for media in media_files_list:
            self.stream_announcements_publisher.newMedia(
                utils.get_sha256(self.media_dir + media),
                splitext(media)[0], self.service_id)

    def uploadMedia(self, file_name, uploader, admin_token, current=None): # pylint: disable=unused-argument, invalid-name
        '''Sube un medio al servidor. Not implemented.'''
        if not self._main_service.isAdmin(admin_token):
            raise IceFlix.Unauthorized

        file_origin_route = utils.CLIENT_MEDIA_DIR + file_name
        file_dest_route = self.media_dir + file_name

        if not isfile(file_origin_route) or isfile(file_dest_route):
            raise IceFlix.UploadError

        with open(file_dest_route, 'wb') as out:
            count = 0
            filesize = getsize(file_origin_route)
            while True:
                chunk = uploader.receive(utils.CHUNK_SIZE)
                if not chunk:
                    break

                out.write(chunk)
                print(
                    f'\r\033[KDownloading {count}/{filesize} bytes... {next(utils.SPINNER)}',
                    end='')
                count += len(chunk)

            print(f'\r\033[KDownloading {count}/{filesize} bytes... {next(utils.SPINNER)}', end='')

        uploader.close()
        print('\n[UPLOADER] Transfer completed!')

    def deleteMedia(self, media_id, admin_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Elimina un medio dado su id si el token de administración es válido.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))
        if not main_service.isAdmin(admin_token):
            raise IceFlix.Unauthorized

        if not utils.remove_file(media_id):
            raise IceFlix.WrongMediaId

        self.stream_announcements_publisher.removedMedia(
            utils.get_sha256(self.media_dir + media_id), self.service_id)
        print(f'\n[PROVIDER SERVICE][INFO] Se ha eliminado correctamente el medio {media_id}\n')


class StreamController(IceFlix.StreamController): # pylint: disable=too-many-instance-attributes
    '''Clase que implementa la interfaz de IceFlix para el stream controller.'''
    def __init__(self, user_token, media_name, media_dir):
        self.user_token = user_token
        self.media_dir = media_dir
        self._srv_id = str(uuid.uuid4())
        self.username = None
        self.media_name = media_name
        self._emitter = None
        self.stream_sync = None
        self.revocations = None
        self.auth_timer = None

    @property
    def service_id(self):
        """Get instance ID."""
        return self._srv_id

    def getSDP(self, user_token, port, current=None): # pylint: disable=invalid-name, unused-argument
        '''Devuelve la configuración del flujo RTSP para la reproducción del vídeo.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))
        try:
            auth = main_service.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print(
                '\n[CONTROLLER SERVICE][ERROR] No se ha podido ' +
                'encontrar un servicio de autenticación.\n')
            return ''

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        self._emitter = RTSPEmitter(self.media_dir + self.media_name, '127.0.0.1', 5000)
        self._emitter.start()

        return f'rtp://@127.0.0.1:{port}'

    def getSyncTopic(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Devuelve el topic del controlador.'''
        return str(self.service_id)

    def refreshAuthentication(self, user_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Refresca el token o eleva una excepción.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))
        try:
            auth = main_service.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print(
                '\n[CONTROLLER SERVICE][ERROR] No se ha podido ' +
                'encontrar un servicio de autenticación.\n')
            return

        if not auth.isAuthorized(user_token):
            raise IceFlix.Unauthorized

        if self.auth_timer.is_alive():
            self.auth_timer.cancel()

    def stop(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Interrumpe la reproducción de vídeo.'''
        self._emitter.stop()
        current.adapter.remove(current.id)


class StreamServer(Ice.Application):
    '''Clase que implementa a interfaz de IceFlix para el servicio de streaming.'''
    def run(self, argv): # pylint: disable=arguments-differ, unused-argument
        broker = self.communicator()
        stream_adapter = broker.createObjectAdapterWithEndpoints('ProviderAdapter', 'tcp')
        stream_adapter.activate()

        servant = StreamProvider(broker)
        servant_proxy = stream_adapter.addWithUUID(servant)

        # Stream announcements topic
        stream_announcements_topic = topics.getTopic(topics.getTopicManager(
            self.communicator()), 'streamannouncements')
        publisher = stream_announcements_topic.getPublisher()
        servant.stream_announcements_publisher = IceFlix.StreamAnnouncementsPrx.uncheckedCast(
            publisher)

        # Discover topic
        discover_topic = topics.getTopic(topics.getTopicManager(self.communicator()), 'discover')
        servant.discover_subscriber = Discover(servant, servant_proxy)
        discover_subscriber_proxy = stream_adapter.addWithUUID(servant.discover_subscriber)
        discover_topic.subscribeAndGetPublisher({}, discover_subscriber_proxy)
        publisher = discover_topic.getPublisher()
        discover_publisher = IceFlix.ServiceAnnouncementsPrx.uncheckedCast(publisher)
        servant.discover_subscriber.publisher = discover_publisher
        servant.discover_subscriber.announce_timer = threading.Timer(
            10.0+random.uniform(0.0, 2.0), servant.discover_subscriber.publisher.announce,
            args=[servant_proxy, servant.service_id])

        servant.discover_subscriber.publisher.newService(servant_proxy, servant.service_id)
        servant.discover_subscriber.announce_timer.start()

        media_files_list = utils.list_files(servant.media_dir)
        for media in media_files_list:
            servant.stream_announcements_publisher.newMedia(
                utils.get_sha256(servant.media_dir + media),
                splitext(media)[0], servant.service_id)

        print("\n[PROVIDER SERVICE][INFO] Servicio iniciado.")

        discover_topic.unsubscribe(discover_subscriber_proxy)
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


sys.exit(StreamServer().main(sys.argv))
