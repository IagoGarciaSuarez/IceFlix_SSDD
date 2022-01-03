'''Implementación de la clase para almacenar los servicios volátiles de IceFlix.'''

import Ice # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class VolatileServices(IceFlix.VolatileServices):
    'Clase para el objeto Media de IceFlix.'
    def __init__(self, auth_services={}, catalog_services={}):
        self.auth_services = auth_services
        self.catalog_services = catalog_services