'''Implementación de la clase para almacenar los servicios volátiles de IceFlix.'''
import Ice # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class VolatileServices(IceFlix.VolatileServices): # pylint: disable=too-few-public-methods
    'Clase para el objeto VolatileServices de IceFlix.'
    def __init__(self, auth_services, catalog_services):
        '''Inicializa el objeto.'''
        self.authenticators = auth_services
        self.mediaCatalogs = catalog_services # pylint: disable=invalid-name
