#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de autenticación.
'''
import sys
import secrets
import uuid
import topics
import threading
import random
from users_db import UsersDB
from discover import Discover
import Ice # pylint: disable=import-error,wrong-import-position
from utils import read_cred_db, write_cred_db
Ice.loadSlice('iceflix_full.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position


class Authenticator(IceFlix.Authenticator):
    '''Clase que implementa la interfaz de IceFlix para el authenticator.'''
    def __init__(self, users_token):
        self._users_token = users_token
        self._srv_id = str(uuid.uuid4())
        self._credentials_db = self._srv_id + '.json'
        self.discover_subscriber = None
        self.is_up_to_date = False
        self.up_to_date_timer = None

    @property
    def current_database(self):
        """Get current users db."""
        return UsersDB(read_cred_db(self._credentials_db), self._users_token)
    @property
    def service_id(self):
        """Get instance ID."""
        return self._srv_id

    def refreshAuthorization(self, username, password_hash, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba que las credenciales son correctas.'''
        credentials = read_cred_db()
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
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))

        if not main_service.isAdmin(adminToken):
            raise IceFlix.Unauthorized

        credentials = read_cred_db(self._credentials_db)
        credentials[username] = password_hash
        write_cred_db(credentials, self._credentials_db)
        print("\n[AUTH SERVICE] Nuevo usuario creado con nombre: ", username)

    def removeUser(self, username, adminToken, current=None): # pylint: disable=invalid-name, unused-argument
        '''Elimina un usuario si el token de administración es válido.'''
        credentials = read_cred_db()
        if not self._main_service.isAdmin(adminToken) or username not in credentials:
            raise IceFlix.Unauthorized

        credentials.pop(username)
        write_cred_db(credentials)

        self._users_token.pop(username)

    def updateDB(self, currentDatabase, srvId, current=None):
        if self.service_id == srvId:
            return
        if not self.is_up_to_date:  
            if srvId not in self.discover_subscriber._auth_services.keys():
                raise IceFlix.UnknownService

            print('sigue con el update')
            if self.up_to_date_timer.is_alive():
                self.up_to_date_timer.cancel()
            self._users_token = currentDatabase.users_token
            write_cred_db(currentDatabase.users_passwords, self._credentials_db)
            self.is_up_to_date = True
            self.discover_subscriber.announce_timer.start()
            


class AuthServer(Ice.Application):
    '''Clase que implementa el servicio de autenticación.'''
    def run(self, argv): # pylint: disable=arguments-differ
        broker = self.communicator()
        auth_adapter = broker.createObjectAdapterWithEndpoints('AuthAdapter', 'tcp')
        auth_adapter.activate()

        users_tokens = {"admin": "sysadmin"}

        servant = Authenticator(users_tokens)
        servant_proxy = auth_adapter.addWithUUID(servant)

        discover_topic = topics.getTopic(topics.getTopicManager(self.communicator()), 'discover')

        servant.discover_subscriber = Discover(servant, servant_proxy)
        discover_subscriber_proxy = auth_adapter.addWithUUID(servant.discover_subscriber)

        discover_topic.subscribeAndGetPublisher({}, discover_subscriber_proxy)
        publisher = discover_topic.getPublisher()
        
        discover_publisher = IceFlix.ServiceAnnouncementsPrx.uncheckedCast(publisher)
        servant.discover_subscriber.publisher = discover_publisher

        servant.discover_subscriber.publisher.newService(servant_proxy, servant.service_id)
            
        def set_up_to_date():
            print("\n[AUTH SERVICE] No update event received. Assuming I'm the first of my kind...")
            servant.is_up_to_date = True
            servant.discover_subscriber.publisher.announce(servant_proxy, servant.service_id)
            servant.discover_subscriber.announce_timer.start()   
            
        servant.up_to_date_timer = threading.Timer(3.0, set_up_to_date)
        servant.up_to_date_timer.start()

        print("\n[AUTH SERVICE] Servicio iniciado.")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        discover_topic.unsubscribe(discover_subscriber_proxy)

        return 0


sys.exit(AuthServer().main(sys.argv))
