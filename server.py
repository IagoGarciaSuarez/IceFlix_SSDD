#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de principal de IceFlix.
'''

import sys
import Ice  # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix  # pylint: disable=import-error,wrong-import-position

class MainService(IceFlix.Main):
    '''Clase que implementa la interfaz de IceFlix para el servicio principal.'''
    def __init__(self, services_proxies, admin_token):
        self._services_proxies = services_proxies
        self.admin_token = admin_token

    def isAdmin(self, token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba si el token es de admin.'''
        if token == self.admin_token:
            return True
        return False

    def register(self, proxy, current=None): # pylint: disable=invalid-name, unused-argument
        '''Registra un servicio.'''
        # proxy.ice_isA('::IceFlix::MediaCatalog')
        # print('BIEN')
        # try:
        #     authPrx = IceFlix.AuthenticatorPrx.checkedCast(proxy)
        #     if authPrx in self._services_proxies["AuthPrx"]:
        #         print("Se ha intentado registrar un servicio de autenticación ya existente.")
        #         return

        #     return authPrx

        # except Ice.NoEndpointException:
        #     try:
        #         catalogPrx = IceFlix.MediaCatalogPrx.checkedCast(proxy)
        #         if catalogPrx in self._services_proxies["CatalogPrx"]:
        #             print("Se ha intentado registrar un servicio de catálogo ya existente.")
        #             return
        #         return catalogPrx

        #     except Ice.NoEndpointException:
        #         print('[ERROR] Se ha intentado registrar un servicio desconocido.')
        #         raise IceFlix.UnknownService
        # =================================================
        if "AuthService" in str(proxy):
            for auth_prx in self._services_proxies["AuthPrx"]:
                if auth_prx == proxy:
                    print(
                        "\n[MAIN SERVICE] Se ha intentado registrar un servicio de autenticación " +
                        "ya existente.")
                    return

            print("\n[MAIN SERVICE] Añadiendo nuevo servicio de autenticación...")
            self._services_proxies["AuthPrx"].append(proxy)
            print("[MAIN SERVICE] Nuevo servicio de autenticación añadido.")

        elif "CatalogService" in str(proxy):
            for catalog_prx in self._services_proxies["CatalogPrx"]:
                if catalog_prx == proxy:
                    print(
                        "\n[MAIN SERVICE] Se ha intentado registrar un servicio de catálogo " +
                        "ya existente.")
                    return

            print("\n[MAIN SERVICE] Añadiendo nuevo servicio de catálogo...")
            self._services_proxies["CatalogPrx"].append(proxy)
            print("[MAIN SERVICE] Nuevo servicio de catálogo añadido.")

        else:
            raise IceFlix.UnknownService

    def getAuthenticator(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene un autenticator y lo devuelve.'''
        for auth_prx in self._services_proxies["AuthPrx"]:
            try:
                auth_prx.ice_ping()
                print('\n[MAIN SERVICE] Se ha obtenido el proxy de autenticador: ', auth_prx)
                return IceFlix.AuthenticatorPrx.checkedCast(auth_prx)

            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                pass

        print("\n[MAIN SERVICE][ERROR] No se ha encontrado ningún servicio de autenticación.")
        raise IceFlix.TemporaryUnavailable

    def getCatalog(self, current=None): # pylint: disable=invalid-name, unused-argument
        '''Obtiene un catálogo y lo devuelve.'''
        for catalog_prx in self._services_proxies["CatalogPrx"]:
            try:
                catalog_prx.ice_ping()
                print('\n[MAIN SERVICE] Se ha obtenido el proxy de catalogo: ', catalog_prx)
                return IceFlix.MediaCatalogPrx.checkedCast(catalog_prx)

            except Ice.ConnectionRefusedException: # pylint: disable=no-member
                pass

        print("\n[MAIN SERVICE][ERROR] No se ha encontrado ningún servicio de catálogo.")
        raise IceFlix.TemporaryUnavailable


class Server(Ice.Application):
    '''Clase que implementa el servicio principal.'''
    def run(self, arg): # pylint: disable=arguments-differ, unused-argument
        services_proxies = {
            "AuthPrx": [],
            "CatalogPrx": [],
        }

        broker = self.communicator()
        servant = MainService(
            services_proxies, broker.getProperties().getProperty('AdminToken'))

        main_adapter = broker.createObjectAdapter("MainAdapter")
        proxy = main_adapter.add(
            servant, broker.stringToIdentity("MainService"))

        print(proxy, flush=True)

        main_adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


SERVER = Server()
sys.exit(SERVER.main(sys.argv))
