from ast import arg
from time import sleep
import threading
import random
import Ice  # pylint: disable=import-error,wrong-import-position
try:
    import IceFlix # pylint: disable=import-error,wrong-import-position
except ImportError:
    Ice.loadSlice('iceflix.ice')
    import IceFlix # pylint: disable=import-error,wrong-import-position

class Discover(IceFlix.ServiceAnnouncements):
    """Discover class to listen to announcements and new services from all services."""
    def __init__(self, service_servant, service):
        """Initialize the Discover object with empty services."""
        self._service_servant = service_servant
        self._service = service
        self.auth_services = {}
        self.catalog_services = {}
        self.main_services = {}
        self.publisher = None
        self.announce_timer = None

        if self._service.ice_isA('::IceFlix::Authenticator'):
            self.auth_services[self._service_servant.service_id] = self._service
        elif self._service.ice_isA('::IceFlix::MediaCatalog'):
            self.catalog_services[self._service_servant.service_id] = self._service
        elif self._service.ice_isA('::IceFlix::Main'):
            self.main_services[self._service_servant.service_id] = self._service

    @property
    def known_services(self):
        """Get serviceIds for all services."""
        return list(self.auth_services.keys()) + list(self.catalog_services.keys()) + \
            list(self.main_services.keys())

    def newService(self, service, srvId, current=None): # pylint: disable=unused-argument
        """Check service type and add it."""
        if srvId == self._service_servant.service_id:
            return

        if service.ice_isA('::IceFlix::Authenticator'):
            self.auth_services[srvId] = IceFlix.AuthenticatorPrx.checkedCast(service)
            
            if self._service.ice_isA('::IceFlix::Authenticator')\
                and self._service_servant.is_up_to_date:
                print(f'New authenticator service: {srvId}')
                self.publisher.announce(self._service, self._service_servant.service_id)
                sleep(1)
                self.auth_services[srvId].updateDB(
                    self._service_servant.current_database, self._service_servant.service_id)

            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.auth_services.append(
                    self.auth_services[srvId])

        elif service.ice_isA('::IceFlix::MediaCatalog'):
            self.catalog_services[srvId] = IceFlix.MediaCatalogPrx.checkedCast(service)
            if self._service.ice_isA('::IceFlix::MediaCatalog')\
                and self._service_servant.is_up_to_date:
                print(f'New catalog service: {srvId}')
                self.publisher.announce(self._service, self._service_servant.service_id)
                sleep(1)
                self.catalog_services[srvId].updateDB(
                    self._service_servant.current_database, self._service_servant.service_id)

            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.catalog_services.append(
                    self.catalog_services[srvId])

        elif service.ice_isA('::IceFlix::Main'):
            print(f'New main service: {srvId}', flush=True)
            self.main_services[srvId] = IceFlix.MainPrx.checkedCast(service)

            if self._service.ice_isA('::IceFlix::Main') and self._service_servant.is_up_to_date:
                self.publisher.announce(self._service, self._service_servant.service_id)
                sleep(1)
                try:
                    self.main_services[srvId].updateDB(
                        self._service_servant.get_volatile_services, 
                        self._service_servant.service_id)
                except IceFlix.UnknownService:
                    print(f'{srvId} didn\'t recognize me as a Main service.')

    def announce(self, service, srvId, current=None):  # pylint: disable=unused-argument
        """Check service type and add it if it is new."""
        # print(f'Known services por service {self._service_servant.service_id} are {self.known_services}')
        if srvId == self._service_servant.service_id:
            self.announce_timer = threading.Timer(
                10.0+random.uniform(0.0, 2.0), self.publisher.announce, args=[self._service, 
                self._service_servant.service_id])
            self.announce_timer.start()
        
        for auth_srv in self.auth_services.values():
            try:
                auth_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.auth_services = {
                    key:val for key, val in self.auth_services.items() \
                    if val!=auth_srv}
                if self._service.ice_isA('::IceFlix::Main'):
                    self._service_servant.get_volatile_services.authenticators.remove(auth_srv)

        for catalog_srv in self.catalog_services.values():
            try:
                catalog_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.catalog_services = {
                    key:val for key, val in self.catalog_services.items() \
                    if val!=catalog_srv}  
                if self._service.ice_isA('::IceFlix::Main'):
                    self._service_servant.get_volatile_services.mediaCatalogs.remove(catalog_srv)

        for main_srv in self.main_services.values():
            try:
                main_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.main_services = {
                    key:val for key, val in self.main_services.items() \
                    if val!=main_srv}

        # print(f'Known services por service {self._service_servant.service_id} are {self.known_services}')

        if srvId in self.known_services or srvId == self._service_servant.service_id:
            return

        if service.ice_isA('::IceFlix::Authenticator'):
            self.auth_services[srvId] = IceFlix.AuthenticatorPrx.checkedCast(service)

        elif service.ice_isA('::IceFlix::MediaCatalog'):
            self.catalog_services[srvId] = IceFlix.MediaCatalogPrx.checkedCast(service)

        if service.ice_isA('::IceFlix::Main'):
            self.main_services[srvId] = IceFlix.MainPrx.checkedCast(service)

        # print(f'Known services por service {self._service_servant.service_id} are {self.known_services}')
