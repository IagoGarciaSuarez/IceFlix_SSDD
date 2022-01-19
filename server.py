#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de principal de IceFlix.
'''
import sys
import random
import uuid
import threading
import Ice  # pylint: disable=import-error,wrong-import-position
try:
    import IceFlix # pylint: disable=import-error,wrong-import-position
except ImportError:
    Ice.loadSlice('iceflix.ice')
    import IceFlix # pylint: disable=import-error,wrong-import-position
import topics
from volatile_services import VolatileServices
from discover import Discover

class MainService(IceFlix.Main):
    '''Clase que implementa la interfaz de IceFlix para el servicio principal.'''
    def __init__(self, admin_token, broker):
        self.admin_token = admin_token
        self.discover_subscriber = None
        self._broker = broker
        self.auth_services = []
        self.catalog_services = []
        self._srv_id = str(uuid.uuid4())
        self.is_up_to_date = False
        self.up_to_date_timer = None

    @property
    def is_up_to_date(self):
        """Return if the database is up to date or not."""
        return self.is_up_to_date

    @property
    def get_volatile_services(self):
        return VolatileServices(self.auth_services, self.catalog_services)
    # @property
    # def addAuthService(self, auth_service):
    #     self._volatile_services.auth_services.append(auth_service)

    # @property
    # def addCatalogService(self, catalog_service):
    #     self._volatile_services.catalog_services.append(catalog_service)

    @property
    def service_id(self):
        """Get instance ID."""
        return self._srv_id

    def isAdmin(self, token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba si el token es de admin.'''
        if token == self.admin_token:
            return True
        return False

    def getAuthenticator(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene un autenticator y lo devuelve.'''
        while 1:
            try:
                auth_prx = random.choice(list(self.auth_services))
                auth_prx.ice_ping()
                print('\n[MAIN SERVICE] Se ha obtenido el proxy de autenticador: ', auth_prx)
                return IceFlix.AuthenticatorPrx.uncheckedCast(auth_prx)

            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self._discover_subscriber._auth_services = {
                    key:val for key, val in self._discover_subscriber._auth_services.items() \
                    if val!=auth_prx}
                self.auth_services.remove(auth_prx)
                
            except IndexError:
                break

        print("\n[MAIN SERVICE][ERROR] No se ha encontrado ningún servicio de autenticación.")
        raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene un catálogo y lo devuelve.'''
        while 1:
            try:
                catalog_prx = random.choice(self.catalog_services)
                catalog_prx.ice_ping()
                print('\n[MAIN SERVICE] Se ha obtenido el proxy de catálogo: ', catalog_prx)
                return IceFlix.MediaCatalogPrx.uncheckedCast(catalog_prx)

            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self._discover_subscriber._catalog_services = {
                    key:val for key, val in self._discover_subscriber._catalog_services.items() \
                    if val!=catalog_prx}
                self.catalog_services.remove(catalog_prx)

            except IndexError:
                break

        print("\n[MAIN SERVICE][ERROR] No se ha encontrado ningún servicio de catálogo.")
        raise IceFlix.TemporaryUnavailable

    def updateDB(self, volatile_services, srvId, current=None):
        if self.service_id == srvId:
            return
        if not self.is_up_to_date:  
            if srvId in self.discover_subscriber.main_services.keys():
                service = IceFlix.MainPrx.checkedCast(self.discover_subscriber.main_services[srvId])
                if not service.isAdmin(self.admin_token):
                    print(
                        "\n[MAIN SERVICE][ERROR] Token de administración no válido. " +
                        "Terminando ejecución...", flush=True)
                    self.up_to_date_timer.cancel()
                    self._broker.shutdown()
                    return
                if self.up_to_date_timer.is_alive():
                    self.up_to_date_timer.cancel()
                self.auth_services = volatile_services.authenticators.copy()
                self.catalog_services = volatile_services.mediaCatalogs.copy()
                self.is_up_to_date = True
                self.discover_subscriber.announce_timer.start()

class Server(Ice.Application):
    '''Clase que implementa el servicio principal.'''
    def run(self, arg): # pylint: disable=arguments-differ, unused-argument
        broker = self.communicator()
        main_adapter = broker.createObjectAdapterWithEndpoints('MainAdapter', 'tcp')
        main_adapter.activate()

        servant = MainService(broker.getProperties().getProperty('AdminToken'), broker)
        servant_proxy = main_adapter.addWithUUID(servant)

        discover_topic = topics.getTopic(topics.getTopicManager(self.communicator()), 'discover')

        servant.discover_subscriber = Discover(servant, servant_proxy)
        discover_subscriber_proxy = main_adapter.addWithUUID(servant.discover_subscriber)

        discover_topic.subscribeAndGetPublisher({}, discover_subscriber_proxy)
        publisher = discover_topic.getPublisher()
        print(servant_proxy, flush=True)

        discover_publisher = IceFlix.ServiceAnnouncementsPrx.uncheckedCast(publisher)
        servant.discover_subscriber.publisher = discover_publisher

        servant.discover_subscriber.publisher.newService(servant_proxy, servant.service_id)
            
        def set_up_to_date():
            print("\n[MAIN SERVICE] No update event received. Assuming I'm the first of my kind...")
            servant.is_up_to_date = True
            servant.discover_subscriber.publisher.announce(servant_proxy, servant.service_id)
            servant.discover_subscriber.announce_timer.start()   
            
        servant.up_to_date_timer = threading.Timer(3.0, set_up_to_date)
        servant.up_to_date_timer.start()


        print("\n[MAIN SERVICE] Servicio iniciado.")


        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        discover_topic.unsubscribe(discover_subscriber_proxy)

        return 0


SERVER = Server()
sys.exit(SERVER.main(sys.argv))
