#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-

import sys
import json
import secrets
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Authenticator(IceFlix.Authenticator):
    def __init__(self, usersWithToken):
        self._usersWithToken = usersWithToken

    def refreshAuthorization(self, username, passwordHash, current=None):
        for user in self._usersWithToken:
            if user['username'] == username and user['passwordHash'] == passwordHash:
                newToken = secrets.token_urlsafe(40)
                user["token"]=newToken
                return newToken

        raise IceFlix.Unauthorized()

    def isAuthorized(self, token, current=None):
        for user in self._usersWithToken:
            if token == user['token']:
                return True
        return False

    def whois(self, token, current=None):
        if self.isAuthorized(token):
            for user in self._usersWithToken:
                if user['token'] == token:
                    return user['username']
        raise IceFlix.Unauthorized()
    
    def addUser(self, username, passwordHash, adminToken, current=None):
        for user in self._usersWithToken:
            if user["username"] == username:
                print("Nombre de usuario ya existente.")
                return

        newUser = {
            "username": username,
            "passwordHash": passwordHash
        }
        self._usersWithToken.append(newUser)
        print("Nuevo usuario creado con nombre: ", username)

    def removeUser(self, username, adminToken, current=None):
        for user in self._usersWithToken:
            if user["username"] == username:
                self._usersWithToken.remove(user)
                print("Se ha eliminado el usuario con nombre: ", username)

class AuthServer(Ice.Application):
    def run(self, argv):
        broker = self.communicator()
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)
        
        if not mainService:
            raise RuntimeError('Invalid proxy for the main service')

        credentials = open('credentials.json', 'r')

        servant = Authenticator()

        authAdapter = broker.createObjectAdapter("AuthAdapter")
        authPrx = authAdapter.add(servant, broker.stringToIdentity("AuthService"))

        mainService.register(authPrx)        

        authAdapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0

sys.exit(AuthServer().main(sys.argv))
