'''Discover topic implementation for announces and new services.'''
from time import sleep
import threading
import random
import Ice  # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class Discover(IceFlix.ServiceAnnouncements): # pylint: disable=too-many-instance-attributes
    """Discover class to listen to announcements and new services from all services."""
    def __init__(self, service_servant, service): # pylint: disable=too-many-instance-attributes
        """Initialize the Discover object with empty services."""
        self._service_servant = service_servant
        self._service = service
        self.auth_services = {}
        self.catalog_services = {}
        self.main_services = {}
        self.provider_services = {}
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
            list(self.main_services.keys()) + list(self.provider_services.keys())

    def newService(self, service, srv_id, current=None): # pylint: disable=unused-argument, invalid-name
        """Check service type and add it."""
        if srv_id == self._service_servant.service_id:
            return

        if service.ice_isA('::IceFlix::Authenticator'):
            self.auth_services[srv_id] = IceFlix.AuthenticatorPrx.checkedCast(service)

            if self._service.ice_isA('::IceFlix::Authenticator')\
                and self._service_servant.is_up_to_date:
                print(f'New authenticator service: {srv_id}')
                self.publisher.announce(self._service, self._service_servant.service_id)
                sleep(1)
                self.auth_services[srv_id].updateDB(
                    self._service_servant.current_database, self._service_servant.service_id)

            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.auth_services.append(
                    self.auth_services[srv_id])

        elif service.ice_isA('::IceFlix::MediaCatalog'):
            self.catalog_services[srv_id] = IceFlix.MediaCatalogPrx.checkedCast(service)
            if self._service.ice_isA('::IceFlix::MediaCatalog')\
                and self._service_servant.is_up_to_date:
                print(f'New catalog service: {srv_id}')
                self.publisher.announce(self._service, self._service_servant.service_id)
                sleep(1)
                self.catalog_services[srv_id].updateDB(
                    self._service_servant.current_database, self._service_servant.service_id)

            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.catalog_services.append(
                    self.catalog_services[srv_id])

        elif service.ice_isA('::IceFlix::StreamProvider') \
            and self._service.ice_isA('::IceFlix::MediaCatalog'):
            print(f'New stream provider service: {srv_id}', flush=True)
            self.provider_services[srv_id] = IceFlix.StreamProviderPrx.checkedCast(service)

        elif service.ice_isA('::IceFlix::Main'):
            print(f'New main service: {srv_id}', flush=True)
            self.main_services[srv_id] = IceFlix.MainPrx.checkedCast(service)

            if self._service.ice_isA('::IceFlix::Main') and self._service_servant.is_up_to_date:
                self.publisher.announce(self._service, self._service_servant.service_id)
                sleep(1)
                try:
                    self.main_services[srv_id].updateDB(
                        self._service_servant.get_volatile_services,
                        self._service_servant.service_id)
                except IceFlix.UnknownService:
                    print(f'{srv_id} didn\'t recognize me as a Main service.')

    def announce(self, service, srv_id, current=None):  # pylint: disable=unused-argument, too-many-branches
        """Check service type and add it if it is new."""
        if srv_id == self._service_servant.service_id:
            self.announce_timer = threading.Timer(
                10.0+random.uniform(0.0, 2.0), self.publisher.announce,
                args=[self._service, self._service_servant.service_id])
            self.announce_timer.start()

        # Comprobación de cada uno de los servicios y eliminación de los que ya no están activos.
        for auth_srv in self.auth_services.values():
            try:
                auth_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.auth_services = {
                    key:val for key, val in self.auth_services.items() \
                    if val != auth_srv}
                if self._service.ice_isA('::IceFlix::Main'):
                    self._service_servant.get_volatile_services.authenticators.remove(auth_srv)

        for catalog_srv in self.catalog_services.values():
            try:
                catalog_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.catalog_services = {
                    key:val for key, val in self.catalog_services.items() \
                    if val != catalog_srv}
                if self._service.ice_isA('::IceFlix::Main'):
                    self._service_servant.get_volatile_services.mediaCatalogs.remove(catalog_srv)

        for main_srv in self.main_services.values():
            try:
                main_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.main_services = {
                    key:val for key, val in self.main_services.items() \
                    if val != main_srv}

        for provider_srv in self.provider_services.values():
            try:
                provider_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                # Todos los catalogs deben reiniciar los proxies. Así, pedirán el reannounce
                # y evitarán tener proxies inválidos o que no se hayan incluido algunos medios.
                # Si un provider no está disponible, no tiene sentido que el catálogo muestre ese
                # medio ya que no se podría reproducir.
                self.provider_services = {}
                if self._service.ice_isA('::IceFlix::MediaCatalog'):
                    self._service_servant.catalog.drop_table()
                    self._service_servant.catalog.create_table()
                    self._service_servant.media_with_proxy = {}

        if srv_id in self.known_services or srv_id == self._service_servant.service_id:
            return

        if service.ice_isA('::IceFlix::Authenticator'):
            self.auth_services[srv_id] = IceFlix.AuthenticatorPrx.checkedCast(service)

            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.auth_services.append(
                    self.auth_services[srv_id])

        elif service.ice_isA('::IceFlix::MediaCatalog'):
            self.catalog_services[srv_id] = IceFlix.MediaCatalogPrx.checkedCast(service)

            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.catalog_services.append(
                    self.catalog_services[srv_id])

        elif service.ice_isA('::IceFlix::StreamProvider') \
            and self._service.ice_isA('::IceFlix::MediaCatalog') \
                and self._service_servant.is_up_to_date:
            self.provider_services[srv_id] = IceFlix.StreamProviderPrx.checkedCast(service)
            try:
                self.provider_services[srv_id].reannounceMedia(self._service_servant.service_id)
            except IceFlix.UnknownService:
                print(
                    '\n[CATALOG SERVICE][ERROR] El servicio no ha reconocido ' +
                    'el id de mi servicio. Se volverá a intentar en su próximo anuncio.\n')

        elif service.ice_isA('::IceFlix::Main'):
            self.main_services[srv_id] = IceFlix.MainPrx.checkedCast(service)
