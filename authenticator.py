#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de autenticación.
'''
import sys
import secrets
import Ice # pylint: disable=import-error,wrong-import-position
from utils import readCredDB, writeCredDB
Ice.loadSlice('iceflix_full.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position


class Authenticator(IceFlix.Authenticator):
    '''Clase que implementa la interfaz de IceFlix para el authenticator.'''
    def __init__(self, users_token, main_service):
        self._users_token = users_token
        self._main_service = main_service

    def refreshAuthorization(self, username, password_hash, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba que las credenciales son correctas.'''
        credentials = readCredDB()
        # Needs another way to read the adminToken
        if username == 'admin' and credentials[username] == password_hash:
            self._users_token[username] = "sysadmin"
            return "sysadmin"

        if username in credentials and credentials[username] == password_hash:
            new_token = secrets.token_urlsafe(40)
            self._users_token[username] = new_token
            return new_token
        raise IceFlix.Unauthorized

    def isAuthorized(self, token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba que el token es válido.'''
        for user in self._users_token:
            if token == self._users_token[user]:
                return True
        return False

    def whois(self, token, current=None):# pylint: disable=unused-argument
        '''Devuelve el nombre de usuario asignado a un token dado.'''
        if self.isAuthorized(token):
            for user in self._users_token:
                if self._users_token[user] == token:
                    return user
        raise IceFlix.Unauthorized

    def addUser(self, username, password_hash, adminToken, current=None): # pylint: disable=invalid-name, unused-argument
        '''Añade un nuevo usuario si el token de administración es válido.'''
        if not self._main_service.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        credentials = readCredDB()
        credentials[username] = password_hash
        writeCredDB(credentials)
        print("\n[AUTH SERVICE] Nuevo usuario creado con nombre: ", username)

    def removeUser(self, username, adminToken, current=None): # pylint: disable=invalid-name, unused-argument
        '''Elimina un usuario si el token de administración es válido.'''
        credentials = readCredDB()
        if not self._main_service.isAdmin(adminToken) or username not in credentials:
            raise IceFlix.Unauthorized

        credentials.pop(username)
        writeCredDB(credentials)

        self._users_token.pop(username)


class AuthServer(Ice.Application):
    '''Clase que implementa el servicio de autenticación.'''
    def run(self, argv): # pylint: disable=arguments-differ
        broker = self.communicator()

        main_proxy = broker.stringToProxy(argv[1])
        main_service = IceFlix.MainPrx.checkedCast(main_proxy)

        if not main_service:
            raise RuntimeError('Invalid proxy for the main service')

        users_tokens = {"admin": "sysadmin"}

        servant = Authenticator(users_tokens, main_service)

        auth_adapter = broker.createObjectAdapter("AuthAdapter")
        auth_prx = auth_adapter.add(
            servant, broker.stringToIdentity("AuthService"))

        main_service.register(auth_prx)

        auth_adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


sys.exit(AuthServer().main(sys.argv))
