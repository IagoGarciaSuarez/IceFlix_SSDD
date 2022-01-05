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
        self._auth_services = {}
        self._catalog_services = {}
        self._main_services = {}
        self.publisher = None

        if self._service.ice_isA('::IceFlix::Authenticator'):
            self._auth_services[self._service_servant.service_id] = self._service
        elif self._service.ice_isA('::IceFlix::MediaCatalog'):
            self._catalog_services[self._service_servant.service_id] = self._service
        elif self._service.ice_isA('::IceFlix::Main'):
            self._main_services[self._service_servant.service_id] = self._service
            
    @property
    def known_services(self):
        """Get serviceIds for all services."""
        return list(self._auth_services.keys()) + list(self._catalog_services.keys()) + \
            list(self._main_services.keys())

    def newService(self, service, srvId, current=None): # pylint: disable=unused-argument
        """Check service type and add it.""" 
        if srvId == self._service_servant.service_id:
            return

        if service.ice_isA('::IceFlix::Authenticator'):
            print(f'New authenticator service: {srvId}')
            self._auth_services[srvId] = IceFlix.AuthenticatorPrx.checkedCast(service)
            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.getVolatileServices.authenticators.append(
                    self._auth_services[srvId])

        elif service.ice_isA('::IceFlix::MediaCatalog'):
            print(f'New catalog service: {srvId}')
            self._catalog_services[srvId] = IceFlix.MediaCatalogPrx.checkedCast(service)
            if self._service.ice_isA('::IceFlix::Main'):
                self._service_servant.getVolatileServices.mediaCatalogs.append(
                    self._catalog_services[srvId])

        elif service.ice_isA('::IceFlix::Main'):
            print(f'New main service: {srvId}', flush=True)
            self._main_services[srvId] = IceFlix.MainPrx.uncheckedCast(service)
            if self._service.ice_isA('::IceFlix::Main') and self._service_servant.isUpToDate:
                # self.publisher.announce(self._service, self._service_servant.service_id)
                self._main_services[srvId].updateDB(
                    self._service_servant.getVolatileServices, self._service_servant.service_id)

    def announce(self, service, srvId, current=None):  # pylint: disable=unused-argument
        """Check service type and add it."""
        print(self.known_services, flush=True)
        # for auth_srv in self._auth_services.values():
        #     try:
        #         auth_srv.ice_ping()
        #     except Ice.ConnectionRefusedException: # pylint: disable=no-member
        #         self._auth_services = {
        #             key:val for key, val in self._auth_services.items() \
        #             if val!=auth_srv}
        #         self._service_servant.getVolatileServices.authenticators.remove(auth_srv)

        # for catalog_srv in self._catalog_services.values():
        #     try:
        #         catalog_srv.ice_ping()
        #     except Ice.ConnectionRefusedException: # pylint: disable=no-member
        #         self._catalog_services = {
        #             key:val for key, val in self._catalog_services.items() \
        #             if val!=catalog_srv}
        #         self._service_servant.getVolatileServices.mediaCatalogs.remove(catalog_srv)

        # for main_srv in self._main_services.values():
        #     try:
        #         main_srv.ice_ping()
        #     except Ice.ConnectionRefusedException: # pylint: disable=no-member
        #         self._main_services = {
        #             key:val for key, val in self._main_services.items() \
        #             if val!=main_srv}

        if srvId in self.known_services or srvId == self._service_servant.service_id:
            return

        # if service.ice_isA('::IceFlix::Authenticator'):
        #     self._auth_services[srvId] = IceFlix.AuthenticatorPrx.uncheckedCast(service)

        # elif service.ice_isA('::IceFlix::MediaCatalog'):
        #     self._catalog_services[srvId] = IceFlix.MediaCatalogPrx.uncheckedCast(service)

        elif service.ice_isA('::IceFlix::Main'):
            self._main_services[srvId] = IceFlix.MainPrx.uncheckedCast(service)
