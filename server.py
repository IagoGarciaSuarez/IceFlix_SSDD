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

class Discover(IceFlix.ServiceAnnouncements):
    """Listen all announcements."""
    def __init__(self, main_service):
        """Initialize the Discover object with empty services."""
        self._auth_services = {}
        self._catalog_services = {}
        self._main_services = {}
        self._main_service = main_service

    @property
    def known_services(self):
        """Get serviceIds for all services."""
        return list(self._auth_services.keys()) + list(self._catalog_services.keys()) + \
            list(self._main_services.keys())

    def newService(self, service, srvId, current=None): # pylint: disable=unused-argument
        """Check service type and add it."""
        volatile_services = self._main_service.getVolatileServices
        
        if self._main_service.isFirst:
            main_service = IceFlix.MainPrx.checkedCast(service)
            main_service.updateDB(volatile_services, self._main_service.service_id)
        
        if srvId in self.known_services:
            return
        if service.ice_isA('::IceFlix::Authenticator'):
            print(f'New authenticator service: {srvId}')
            self._auth_services[srvId] = IceFlix.AuthenticatorPrx.uncheckedCast(service)
            volatile_services.auth_services.append(IceFlix.AuthenticatorPrx.uncheckedCast(service))
        elif service.ice_isA('::IceFlix::MediaCatalog'):
            print(f'New catalog service: {srvId}')
            self._catalog_services[srvId] = IceFlix.MediaCatalogPrx.uncheckedCast(service)
            volatile_services.catalog_services.append(
                IceFlix.MediaCatalogPrx.uncheckedCast(service))
        elif service.ice_isA('::IceFlix::Main'):
            print(f'New main service: {srvId}')
            self._main_services[srvId] = IceFlix.MainPrx.uncheckedCast(service)

        self._main_service.setVolatileServices(volatile_services)
        
    def announce(self, service, srvId, current=None):  # pylint: disable=unused-argument
        """Check service type and add it."""
        volatile_services = self._main_service.getVolatileServices
        
        if srvId in self.known_services:
            return
        if service.ice_isA('::IceFlix::Authenticator'):
            print(f'New authenticator service: {srvId}')
            self._auth_services[srvId] = IceFlix.AuthenticatorPrx.uncheckedCast(service)
            volatile_services.auth_services.append(IceFlix.AuthenticatorPrx.uncheckedCast(service))
        elif service.ice_isA('::IceFlix::MediaCatalog'):
            print(f'New catalog service: {srvId}')
            self._catalog_services[srvId] = IceFlix.MediaCatalogPrx.uncheckedCast(service)
            volatile_services.catalog_services.append(
                IceFlix.MediaCatalogPrx.uncheckedCast(service))
        elif service.ice_isA('::IceFlix::Main'):
            print(f'New main service: {srvId}')
            self._main_services[srvId] = IceFlix.MainPrx.uncheckedCast(service)

class MainService(IceFlix.Main):
    '''Clase que implementa la interfaz de IceFlix para el servicio principal.'''
    def __init__(self, discover_subscriber, admin_token):
        self.admin_token = admin_token
        self._discover_subscriber = discover_subscriber
        self._volatile_services = VolatileServices()
        self._auth_services = self._volatile_services.auth_services
        self._catalog_services = self._volatile_services.catalog_services
        self._srv_id = str(uuid.uuid4())
        self._is_first = False
        self.timer = None

    @property
    def setFirst(self):
        """Set this instance as the first for the db reference."""
        self._is_first = True

    @property
    def isFirst(self):
        """Get instance ID."""
        return self._is_first

    @property
    def getVolatileServices(self):
        return self._volatile_services

    @property
    def setVolatileServices(self, volatile_services):
        self._volatile_services = volatile_services

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
                auth_prx = random.choice(list(self._auth_services))
                auth_prx.ice_ping()
                print('\n[MAIN SERVICE] Se ha obtenido el proxy de autenticador: ', auth_prx)
                return IceFlix.AuthenticatorPrx.uncheckedCast(auth_prx)

            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self._discover_subscriber._auth_services = {
                    key:val for key, val in self._discover_subscriber._auth_services.items() \
                    if val!=auth_prx}
                self._auth_services.remove(auth_prx)
                
            except IndexError:
                break

        print("\n[MAIN SERVICE][ERROR] No se ha encontrado ningún servicio de autenticación.")
        raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene un catálogo y lo devuelve.'''
        while 1:
            try:
                catalog_prx = random.choice(list(self._catalog_services.values()))
                catalog_prx.ice_ping()
                print('\n[MAIN SERVICE] Se ha obtenido el proxy de catálogo: ', catalog_prx)
                return IceFlix.MediaCatalogPrx.uncheckedCast(catalog_prx)

            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self._discover_subscriber._catalog_services = {
                    key:val for key, val in self._discover_subscriber._catalog_services.items() \
                    if val!=catalog_prx}
                self._catalog_services.remove(catalog_prx)

            except IndexError:
                break

        print("\n[MAIN SERVICE][ERROR] No se ha encontrado ningún servicio de catálogo.")
        raise IceFlix.TemporaryUnavailable

    def updateDB(self, volatile_services, srvId, current=None):
        if srvId in self._discover_subscriber.known_services:
            self.timer.cancel()
            self._auth_services = volatile_services.auth_services
            self._catalog_services = volatile_services.catalog_services

class Server(Ice.Application):
    '''Clase que implementa el servicio principal.'''
    def run(self, arg): # pylint: disable=arguments-differ, unused-argument
        broker = self.communicator()
        main_adapter = broker.createObjectAdapterWithEndpoint('MainAdapter', 'tcp')
        main_adapter.activate()

        discover_topic = topics.getTopic(topics.getTopicManager(self.communicator()), 'discover')
        discover_subscriber = Discover()
        discover_subscriber_proxy = main_adapter.addWithUUID(discover_subscriber)
        publisher = discover_topic.subscribeAndGetPublisher({}, discover_subscriber_proxy)

        servant = MainService(discover_subscriber, broker.getProperties().getProperty('AdminToken'))
        servant_proxy = main_adapter.addWithUUID(servant)

        print(servant_proxy, flush=True)

        discover_publisher = IceFlix.ServiceAnnouncementsPrx.uncheckedCast(publisher)
        discover_publisher.newService(servant.service_id, servant_proxy)

        servant.timer = threading.Timer(3.0, servant.setFirst)
        servant.timer.start()

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        discover_topic.unsubscribe(discover_subscriber_proxy)

        return 0


SERVER = Server()
sys.exit(SERVER.main(sys.argv))
