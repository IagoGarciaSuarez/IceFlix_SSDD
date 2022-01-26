#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
'''
Archivo que implementa las clases correspondientes al servicio de autenticación.
'''
import sys
import secrets
import uuid
import threading
import random
import Ice # pylint: disable=import-error,wrong-import-position
import topics
from revocations import Revocations
from users_db import UsersDB
from user_updates import UserUpdates
from discover import Discover
from utils import read_cred_db, write_cred_db
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class Authenticator(IceFlix.Authenticator): # pylint: disable=too-many-instance-attributes
    '''Clase que implementa la interfaz de IceFlix para el authenticator.'''
    def __init__(self, broker, users_token):
        self.broker = broker
        self.users_token = users_token
        self._srv_id = str(uuid.uuid4())
        self.credentials_db = self._srv_id + '.json'
        self.prx = None
        self.discover_subscriber = None
        self.userupdates_subscriber = None
        self.revocations_subscriber = None
        self.is_up_to_date = False
        self.up_to_date_timer = None
        self.ua_prx = None
        self.rev_prx = None

    @property
    def current_database(self):
        """Get current users db."""
        return UsersDB(read_cred_db(self.credentials_db), self.users_token)
    @property
    def service_id(self):
        """Get instance ID."""
        return self._srv_id

    def refreshAuthorization(self, username, password_hash, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba que las credenciales son correctas y genera un token de 120 segundos.'''
        credentials = read_cred_db(self.credentials_db)

        if username in credentials and credentials[username] == password_hash:
            new_token = secrets.token_urlsafe(40)
            self.users_token[username] = new_token
            self.userupdates_subscriber.publisher.newToken(username, new_token, self.service_id)
            revocation_timer = threading.Timer(
                12.0, self.revocations_subscriber.publisher.revokeToken,
                args=[new_token, self.service_id])
            revocation_timer.start()
            return new_token

        raise IceFlix.Unauthorized

    def isAuthorized(self, token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Comprueba que el token es válido.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))
        if main_service.isAdmin(token):
            return True
        for user in self.users_token:
            if token == self.users_token[user]:
                return True
        return False

    def whois(self, token, current=None):# pylint: disable=unused-argument
        '''Devuelve el nombre de usuario asignado a un token dado.'''
        if self.isAuthorized(token):
            for user in self.users_token:
                if self.users_token[user] == token:
                    return user
        raise IceFlix.Unauthorized

    def addUser(self, username, password_hash, admin_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Añade un nuevo usuario si el token de administración es válido.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))

        if not main_service.isAdmin(admin_token):
            raise IceFlix.Unauthorized

        credentials = read_cred_db(self.credentials_db)
        credentials[username] = password_hash
        write_cred_db(credentials, self.credentials_db)
        self.userupdates_subscriber.publisher.newUser(username, password_hash, self.service_id)
        print("\n[AUTH SERVICE] Nuevo usuario creado con nombre: ", username)

    def removeUser(self, username, admin_token, current=None): # pylint: disable=invalid-name, unused-argument
        '''Elimina un usuario si el token de administración es válido.'''
        main_service = random.choice(list(self.discover_subscriber.main_services.values()))
        credentials = read_cred_db(self.credentials_db)
        if not main_service.isAdmin(admin_token) or username not in credentials:
            raise IceFlix.Unauthorized

        if username in self.users_token:
            self.revocations_subscriber.publisher.revokeToken(
                self.users_token.pop(username), self.service_id)
        credentials.pop(username)
        write_cred_db(credentials, self.credentials_db)
        self.revocations_subscriber.publisher.revokeUser(username, self.service_id)

    def updateDB(self, current_database, srv_id, current=None): # pylint: disable=invalid-name, unused-argument
        '''Actualiza la base de datos de un servicio que esté vivo desde antes.'''
        if self.service_id == srv_id:
            return
        if not self.is_up_to_date:
            if srv_id not in self.discover_subscriber.auth_services.keys():
                raise IceFlix.UnknownService
            if self.up_to_date_timer.is_alive():
                self.up_to_date_timer.cancel()
            print(f'\n[AUTH SERVICE][INFO] Update received from {srv_id}.')
            self.users_token = current_database.usersToken
            write_cred_db(current_database.userPasswords, self.credentials_db)
            self.is_up_to_date = True
            self.discover_subscriber.publisher.announce(self.prx, self.service_id)
            user_updates_topic = topics.getTopic(topics.getTopicManager(
                self.broker), 'userupdates')
            user_updates_topic.subscribeAndGetPublisher({}, self.ua_prx)
            revocations_topic = topics.getTopic(topics.getTopicManager(
                self.broker), 'revocations')
            revocations_topic.subscribeAndGetPublisher({}, self.rev_prx)

class AuthServer(Ice.Application):
    '''Clase que implementa el servicio de autenticación.'''
    def run(self, argv): # pylint: disable=arguments-differ, unused-argument
        broker = self.communicator()
        auth_adapter = broker.createObjectAdapterWithEndpoints('AuthAdapter', 'tcp')
        auth_adapter.activate()

        users_tokens = {}

        servant = Authenticator(broker, users_tokens)
        servant_proxy = auth_adapter.addWithUUID(servant)
        servant.prx = servant_proxy

        # User updates topic
        user_updates_topic = topics.getTopic(topics.getTopicManager(
            self.communicator()), 'userupdates')
        servant.userupdates_subscriber = UserUpdates(servant, servant_proxy)
        servant.ua_prx = auth_adapter.addWithUUID(servant.userupdates_subscriber)
        publisher = user_updates_topic.getPublisher()
        publisher = IceFlix.UserUpdatesPrx.uncheckedCast(publisher)
        servant.userupdates_subscriber.publisher = publisher

        # Revocations topic
        revocations_topic = topics.getTopic(topics.getTopicManager(
            self.communicator()), 'revocations')
        servant.revocations_subscriber = Revocations(servant, servant_proxy)
        servant.rev_prx = auth_adapter.addWithUUID(servant.revocations_subscriber)
        publisher = revocations_topic.getPublisher()
        publisher = IceFlix.RevocationsPrx.uncheckedCast(publisher)
        servant.revocations_subscriber.publisher = publisher

        # Discover topic
        discover_topic = topics.getTopic(topics.getTopicManager(self.communicator()), 'discover')
        servant.discover_subscriber = Discover(servant, servant_proxy)
        discover_subscriber_proxy = auth_adapter.addWithUUID(servant.discover_subscriber)
        discover_topic.subscribeAndGetPublisher({}, discover_subscriber_proxy)
        publisher = discover_topic.getPublisher()
        publisher = IceFlix.ServiceAnnouncementsPrx.uncheckedCast(publisher)
        servant.discover_subscriber.publisher = publisher
        servant.discover_subscriber.announce_timer = threading.Timer(
            10.0+random.uniform(0.0, 2.0), servant.discover_subscriber.publisher.announce,
            args=[servant_proxy, servant.service_id])

        servant.discover_subscriber.publisher.newService(servant_proxy, servant.service_id)

        def set_up_to_date():
            print(
                "\n[AUTH SERVICE][INFO] No update event received. " +
                "Assuming I'm the first of my kind...")
            servant.is_up_to_date = True
            servant.credentials_db = 'credentials.json'
            revocations_topic.subscribeAndGetPublisher({}, servant.rev_prx)
            user_updates_topic.subscribeAndGetPublisher({}, servant.ua_prx)
            servant.discover_subscriber.publisher.announce(servant_proxy, servant.service_id)

        servant.up_to_date_timer = threading.Timer(3.0, set_up_to_date)
        servant.up_to_date_timer.start()

        print(f'\n[AUTH SERVICE][INFO] My ID is {servant.service_id}')
        print("\n[AUTH SERVICE][INFO] Servicio iniciado.")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        discover_topic.unsubscribe(discover_subscriber_proxy)
        user_updates_topic.unsubscribe(servant.ua_prx)
        revocations_topic.unsubscribe(servant.rev_prx)

        return 0


sys.exit(AuthServer().main(sys.argv))
