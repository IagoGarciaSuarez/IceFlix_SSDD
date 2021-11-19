#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix


class MainService(IceFlix.Main):
    def __init__(self, services_proxies, adminToken):
        self._services_proxies = services_proxies
        self.adminToken = adminToken
        
    def isAdmin(self, token, current=None):
        if token == self.adminToken:
            return True
        return False

    def register(self, proxy, current=None):
        if "AuthService" in str(proxy):
            for authPrx in self._services_proxies["AuthPrx"]:
                if authPrx == proxy:
                    print("Se ha intentado registrar un servicio de autenticación ya existente.")
                    return               
            
            print("\nAñadiendo nuevo servicio de autenticación...")
            self._services_proxies["AuthPrx"].append(proxy)
            print("Nuevo servicio de autenticación añadido.")
        
        elif "CatalogService" in str(proxy):
            for catalogPrx in self._services_proxies["CatalogPrx"]:
                if catalogPrx == proxy:
                    print("Se ha intentado registrar un servicio de catálogo ya existente.")
                    return               
            
            print("\nAñadiendo nuevo servicio de catálogo...")
            self._services_proxies["CatalogPrx"].append(proxy)
            print("Nuevo servicio de catálogo añadido.")

        else:
            raise IceFlix.UnknownService

    def getAuthenticator(self, current=None):
        for authPrx in self._services_proxies["AuthPrx"]:
            try:
                authPrx.ice_ping()
                return authPrx

            except Ice.ConnectionRefusedException:
                pass

        print("\n[ERROR] No se ha encontrado ningún servicio de autenticación.")
        raise IceFlix.TemporaryUnavailable
        

    def getCatalog(self, current=None):
        for catalogPrx in self._services_proxies["CatalogPrx"]:
            try:
                catalogPrx.ice_ping()
                return catalogPrx

            except Ice.ConnectionRefusedException:
                pass

        print("\n[ERROR] No se ha encontrado ningún servicio de catálogo.")
        raise IceFlix.TemporaryUnavailable

class Server(Ice.Application):
    def run(self, argv):
        services_proxies = {
            "AuthPrx":[], 
            "CatalogPrx":[],
        }

        broker = self.communicator()
        servant = MainService(services_proxies, broker.getProperties().getProperty('AdminToken'))

        mainAdapter = broker.createObjectAdapter("MainAdapter")
        proxy = mainAdapter.add(servant, broker.stringToIdentity("MainService"))

        print(proxy, flush=True)

        mainAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

server = Server()
sys.exit(server.main(sys.argv))