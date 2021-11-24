#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import json
import secrets
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Authenticator(IceFlix.Authenticator):
    def __init__(self, credentials, usersToken, mainService):
        self._credentials = credentials
        self._usersToken = usersToken
        self._mainService = mainService

    def refreshAuthorization(self, username, passwordHash, current=None):
        for user in self._credentials:
            if user == username and self._credentials[user] == passwordHash:
                newToken = secrets.token_urlsafe(40)
                self._usersToken[user]=newToken
                return newToken

        raise IceFlix.Unauthorized

    def isAuthorized(self, token, current=None):
        for user in self._usersToken:
            if token == self._usersToken[user]:
                return True
        return False

    def whois(self, token, current=None):
        if self.isAuthorized(token):
            for user in self._usersToken:
                if self._usersToken[user] == token:
                    return user
        raise IceFlix.Unauthorized
    
    def addUser(self, username, passwordHash, adminToken, current=None):
        if not self._mainService.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        if username in self._usersToken:
            print("Nombre de usuario ya existente.")
            return
        self._credentials[username] = passwordHash
        print("Nuevo usuario creado con nombre: ", username)
        

    def removeUser(self, username, adminToken, current=None):
        if not self._mainService.isAdmin(adminToken) or username not in self._credentials:
            raise IceFlix.Unauthorized

        self._credentials.pop(username)
        self._usersToken.pop(username)
        

class AuthServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        credentials = open('credentials.json', 'r')
        #usersToken with form {<username>: <token>}
        usersTokens = {}

        servant = Authenticator(credentials, usersTokens, mainService)

        authAdapter = broker.createObjectAdapter("AuthAdapter")
        authPrx = authAdapter.add(servant, broker.stringToIdentity("AuthService"))

        mainService.register(authPrx)        

        authAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(AuthServer().main(sys.argv))
