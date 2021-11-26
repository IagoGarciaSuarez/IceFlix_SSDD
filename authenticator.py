#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import secrets
from utils import readCredDB, writeCredDB
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Authenticator(IceFlix.Authenticator):
    def __init__(self, usersToken, mainService):
        self._usersToken = usersToken
        self._mainService = mainService

    def refreshAuthorization(self, username, passwordHash, current=None):
        credentials = readCredDB()
        #Needs another way to read the adminToken
        if username == 'admin' and credentials[username] == passwordHash:
            self._usersToken[username] = "sysadmin"
            return "sysadmin"

        if username in credentials and credentials[username] == passwordHash:
            newToken = secrets.token_urlsafe(40)
            self._usersToken[username]=newToken
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

        credentials = readCredDB()
        credentials[username] = passwordHash
        writeCredDB(credentials)
        print("Nuevo usuario creado con nombre: ", username)
        

    def removeUser(self, username, adminToken, current=None):
        credentials = readCredDB()
        if not self._mainService.isAdmin(adminToken) or username not in credentials:
            raise IceFlix.Unauthorized

        credentials.pop(username)
        writeCredDB(credentials)

        self._usersToken.pop(username)
        

class AuthServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')


        usersTokens = {}

        servant = Authenticator(usersTokens, mainService)

        authAdapter = broker.createObjectAdapter("AuthAdapter")
        authPrx = authAdapter.add(servant, broker.stringToIdentity("AuthService"))

        mainService.register(authPrx)        

        authAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(AuthServer().main(sys.argv))
