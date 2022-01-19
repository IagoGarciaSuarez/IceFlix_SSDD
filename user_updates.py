from time import sleep
import threading
import random
from utils import read_cred_db, write_cred_db
import Ice  # pylint: disable=import-error,wrong-import-position
try:
    import IceFlix # pylint: disable=import-error,wrong-import-position
except ImportError:
    Ice.loadSlice('iceflix.ice')
    import IceFlix # pylint: disable=import-error,wrong-import-position

class UserUpdates(IceFlix.UserUpdates):
    """UserUpdates class to listen to user updates events from other auth services."""
    def __init__(self, service_servant, service):
        """Initialize the UserUpdates object."""
        self._service_servant = service_servant
        self._service = service
        self.publisher = None

    def newUser(self, user, passwordHash, srvId, current=None): # pylint: disable=unused-argument
        """Adds a new user."""
        if srvId == self._service_servant.service_id:
            return
        
        credentials = read_cred_db(self._service_servant.credentials_db)
        credentials[user] = passwordHash
        write_cred_db(credentials, self._service_servant.credentials_db)

    def announce(self, service, srvId, current=None):  # pylint: disable=unused-argument
        """Check service type and add it if it is new."""
        # print(f'Known services por service {self._service_servant.service_id} are {self.known_services}')
        if self.announce_timer.is_alive():
            self.announce_timer.cancel()
            self.announce_timer = threading.Timer(
                4.0+random.uniform(0.0, 2.0), lambda: self.announce(
                    self._service, self._service_servant.service_id))
            self.announce_timer.start()
        
        for auth_srv in self._auth_services.values():
            try:
                auth_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self._auth_services = {
                    key:val for key, val in self._auth_services.items() \
                    if val!=auth_srv}
                self._service_servant.getVolatileServices.authenticators.remove(auth_srv)

        # for catalog_srv in self._catalog_services.values():
        #     try:
        #         catalog_srv.ice_ping()
        #     except Ice.ConnectionRefusedException: # pylint: disable=no-member
        #         self._catalog_services = {
        #             key:val for key, val in self._catalog_services.items() \
        #             if val!=catalog_srv}
        #         self._service_servant.getVolatileServices.mediaCatalogs.remove(catalog_srv)

        for main_srv in self.main_services.values():
            try:
                main_srv.ice_ping()
            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                self.main_services = {
                    key:val for key, val in self.main_services.items() \
                    if val!=main_srv}

        if srvId in self.known_services or srvId == self._service_servant.service_id:
            return

        if service.ice_isA('::IceFlix::Authenticator'):
            self._auth_services[srvId] = IceFlix.AuthenticatorPrx.uncheckedCast(service)

        # elif service.ice_isA('::IceFlix::MediaCatalog'):
        #     self._catalog_services[srvId] = IceFlix.MediaCatalogPrx.uncheckedCast(service)

        if service.ice_isA('::IceFlix::Main'):
            self.main_services[srvId] = IceFlix.MainPrx.checkedCast(service)

        # print(f'Known services por service {self._service_servant.service_id} are {self.known_services}')
