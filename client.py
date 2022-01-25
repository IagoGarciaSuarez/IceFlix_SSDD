#!/usr/bin/python3
# -*- coding: utf-8 -*-

'''
Archivo que define las 3 clases necesarias para la elaboración del cliente IceFlix.
Clases en el archivo:
    - IceFlixClient -> Contiene la lógica necesaria para conectar con los servicios de IceFlix.
    - Client        -> Hereda de Ice para utilizar sus funciones.
    - IceFlixCLI    -> Interfaz de línea de comandos para el control del cliente de IceFlix.
'''

import sys
import time
import cmd
from getpass import getpass
import Ice  # pylint: disable=import-error,wrong-import-position
import topics
from revocations import Revocations
from stream_sync import StreamSync
from iceflixrtsp import RTSPPlayer
from utils import get_password_sha256, ICEFLIX_BANNER
Ice.loadSlice('iceflix.ice')
import IceFlix  # pylint: disable=import-error,wrong-import-position

class IceFlixClient: # pylint: disable=too-few-public-methods
    '''
    Clase que permite la conexión a los servicios de IceFlix.
    '''
    def __init__(self, broker):
        self.communicator = broker
        self.adapter = self.communicator.createObjectAdapterWithEndpoints(
            'IceFlix', 'tcp')
        self.adapter.activate()
        self.main_service = None
        self.player = None

    def run(self, mainprx):
        '''Main de IceFlixClient'''
        main_proxy = self.communicator.stringToProxy(mainprx)

        for intento in range(3):
            try:
                self.main_service = IceFlix.MainPrx.checkedCast(main_proxy)
                print('\n[INFO] Servicio IceFlix conectado.\n')
                break
            except Ice.NoEndpointException: # pylint: disable=no-member
                print('\n[ERROR] No se ha podido conectar con el servicio IceFlix indicado.\n')
                for sec in range(10, 0, -1):
                    print(
                        f'[ERROR] Reintentando en {sec} segundos. [{intento+1}/3]', end='\r')
                    time.sleep(1)

        if not self.main_service:
            raise RuntimeError('\n[ERROR] Invalid proxy for the main service.\n')

class IceFlixCLI(cmd.Cmd): # pylint: disable=too-many-instance-attributes
    '''IceFlix shell'''
    def __init__(self, stdin=None, stdout=None):
        if stdin is not None:
            self.use_rawinput = False
        super(IceFlixCLI, self).__init__(
            completekey='tab', stdin=stdin, stdout=stdout)
        self.client = None
        self._last_results_ = {}
        self.controller = None

    prompt = '> '
    intro = ICEFLIX_BANNER + \
        '\nEscribe \'help\' o \'?\' para mostrar los comandos disponibles.\nEscribe ' + \
        '\'iniciar <main server proxy>\' indicando el proxy del servicio IceFlix principal al ' + \
        'que quieres conectarte.\n'
    iniciado = False
    username = None
    password_hash = None
    user_token = None
    logged = False
    admin = False
    selected_media = None
    revocations_topic = None
    revocations_subscriber_proxy = None
    controller_topic = None
    controller_subscriber_proxy = None
    token_refreshed = False

    def do_iniciar(self, arg, initial=None): # pylint: disable=unused-argument
        'iniciar <proxy> - Se conecta a un servicio IceFlix para comenzar a utilizar la plataforma.'
        if self.iniciado:
            print('\n[ERROR] Servicio IceFlix ya conectado. Puede cerrarlo escribiendo \'q\'.\n')
            return

        if not arg:
            print('\n[ERROR] Se debe indicar un proxy.\n')
            return

        mainprx = arg.replace('\'', '').replace('\"', '').strip()
        try:
            self.client.run(mainprx)
        except RuntimeError:
            print('\n[ERROR] No se ha podido conectar con el servicio IceFlix.\n')
            return

        self.iniciado = True

    def do_login(self, initial=None): # pylint: disable=unused-argument
        ('login - Inicia sesión una vez indicado un usuario y contraseña correctos.'
         ' Se puede iniciar sesión como administrador utilizando el comando adminlogin.')

        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if self.logged:
            print(f'\n[ERROR] Ya existe una sesión iniciada por {self.username}.\n')
            return

        try:
            auth_service = self.client.main_service.getAuthenticator()
            self.username = input('Nombre de usuario: ')
            self.password_hash = get_password_sha256(getpass('Contraseña: '))
            self.user_token = auth_service.refreshAuthorization(self.username, self.password_hash)
            self.token_refreshed = True
            self.logged = True
            print('\n[INFO] Se ha iniciado sesión correctamente.\n')
            self.prompt = f'{self.username}> '

            self.revocations_topic = topics.getTopic(topics.getTopicManager(
                self.client.communicator), 'revocations')
            revocations = Revocations(self)
            self.revocations_subscriber_proxy = self.client.adapter.addWithUUID(revocations)
            self.revocations_topic.subscribeAndGetPublisher({}, self.revocations_subscriber_proxy)

        except IceFlix.Unauthorized:
            print('\n[ERROR] Error al introducir las credenciales.\n')
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de autenticación disponible.\n')
        except EOFError:
            print()

    def do_adminlogin(self, initial=None): # pylint: disable=unused-argument
        'adminlogin - Inicia sesión de administrador una vez indicado un admin token correcto.\n'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if not self.logged:
            try:
                self.user_token = input('Token de administrador: ')
            except EOFError:
                print()
                return
            if self.client.main_service.isAdmin(self.user_token):
                self.logged = True
                self.admin = True
                self.username = None
                self.password_hash = None
                self.token_refreshed = True
                print(
                    '\n[INFO] Se ha iniciado sesión de administrador correctamente.\n')
                self.prompt = f'[ADMIN]> '

                self.revocations_topic = topics.getTopic(topics.getTopicManager(
                    self.client.communicator), 'revocations')
                revocations = Revocations(self)
                self.revocations_subscriber_proxy = self.client.adapter.addWithUUID(revocations)
                self.revocations_topic.subscribeAndGetPublisher(
                    {}, self.revocations_subscriber_proxy)
            else:
                print('\n[ERROR] Error al introducir el token de administrador.\n')

        else:
            print(
                f'\n[ERROR] Ya existe una sesión iniciada por {self.username}.\n')

    def do_logout(self, initial=None): # pylint: disable=unused-argument
        'logout - Cierra sesión si hay una iniciada.\n'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if self.logged:
            self.username = None
            self.password_hash = None
            self.user_token = None
            self.logged = False
            self.admin = False
            self.prompt = '> '
            self.revocations_topic.unsubscribe(self.revocations_subscriber_proxy)
            print('\n[INFO] Se ha cerrado la sesión correctamente.\n')

        else:
            print('\n[ERROR] No hay ninguna sesión iniciada.\n')

    def do_search(self, arg, initial=None): # pylint: disable=unused-argument
        '''search <mode> <name|tags> - Busca medios según el modo seleccionado.
            mode:   1 - Búsqueda por nombre exacto.
                    2 - Búsqueda por nombre incluído.
                    3 - Búsqueda por tags exactas (es necesario iniciar sesión).
                    4 - Búsqueda por tags incluídas (es necesario iniciar sesión).
                    *Las tags se indicarán separadas por \',\'.
        '''
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        try:
            catalog_service = self.client.main_service.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de catálogo disponible.\n')
            return

        argv = arg.split(' ', 1)
        if len(argv) < 2:
            print(
                '\n[ERROR] Error en el número de argumentos. Escribe \'help addtags\'' +
                ' para más información.\n')
            return

        mode = argv[0].strip()
        self._last_results_ = None
        if mode in ['1', '2']:
            name = argv[1].strip()
            self._last_results_ = catalog_service.getTilesByName(name, (mode == '1'))

        elif mode in ['3', '4']:
            tags = [tag.strip() for tag in argv[1].split(',')]
            try:
                self._last_results_ = catalog_service.getTilesByTags(
                    tags, (mode == '3'), self.user_token)
            except IceFlix.Unauthorized:
                print('\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
                return

        else:
            print(
                f'\n[ERROR] No se ha reconocido el modo \'{mode}\'. Escribe \'help addtags\' ' +
                'para más información.\n ')
            return

        self.do_lastsearch()

    def do_lastsearch(self, initial=None): # pylint: disable=unused-argument
        'lastsearch - Muestra los resultados de la última búsqued realizada.\n'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if self._last_results_:
            try:
                catalog_service = self.client.main_service.getCatalog()
            except IceFlix.TemporaryUnavailable:
                print('\n[ERROR] No existe ningún servicio de catálogo disponible.\n')
                return

            for i, media_id in zip(range(len(self._last_results_)), self._last_results_):
                try:
                    media_info = catalog_service.getTile(media_id)
                except IceFlix.WrongMediaId as wmid:
                    print(
                        f'\n[ERROR] No se ha encontrado el medio con id {wmid.mediaId}\n')
                    return
                except IceFlix.TemporaryUnavailable:
                    print(
                        f'\n[ERROR] El medio {media_id} no está disponible en este momento.\n')
                    return

                if self.admin or not self.user_token:
                    print(
                        f'Resultado {i+1}:\n\tTítulo: {media_info.info.name}\n\tID: {media_id}\n')

                else:
                    print(f'Resultado {i+1}:\n\tTítulo: {media_info.info.name}\n' +
                          f'\tTags de {self.username}: {media_info.info.tags}\n\tID: {media_id}\n')

            print(
                f'\n[INFO] Se han encontrado {len(self._last_results_)} resultados.\n')

        else:
            print('\n[INFO] No se ha encontrado ningún resultado.\n')

    def do_select(self, arg, initial=None): # pylint: disable=unused-argument
        ('select <media_id> - Indicando el ID de un medio disponible, se selecciona dicho medio '
         'para poder realizar operaciones con él.\n')
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return
        try:
            catalog_service = self.client.main_service.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de catálogo disponible.\n')
            return

        if not self.user_token:
            print(
                '\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return

        if not arg:
            print(
                '\n[ERROR] Debe indicar un ID. Escriba \'help select\' para más información.\n')
            return

        media_id = arg.strip()

        try:
            self.selected_media = catalog_service.getTile(media_id)
        except IceFlix.WrongMediaId as wmid:
            print(f'\n[ERROR] No se ha encontrado el medio con id \'{wmid.mediaId}\'.\n')
            return
        except IceFlix.TemporaryUnavailable:
            print(
                f'\n[ERROR] El medio {media_id} no está disponible en este momento.\n')
            return
        if self.admin:
            self.prompt = (
                f'[ADMIN]\nSelección actual:'
                f' {self.selected_media.mediaId} ({self.selected_media.info.name})\n> ')
        else:
            self.prompt = (
                f'Usuario: {self.username}\nSelección actual:'
                f' {self.selected_media.mediaId} ({self.selected_media.info.name})\n> ')

    def do_unselect(self, initial=None): # pylint: disable=unused-argument
        'unselect - Desselecciona el elemento seleccionado.\n'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if not self.user_token:
            print(
                '\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return
        self.selected_media = None
        self.prompt = f'{self.username}> '

    def do_rename(self, arg, initial=None): # pylint: disable=unused-argument, too-many-return-statements
        ('rename <nuevo nombre> - Cambia el nombre de un medio por el valor <nuevo nombre>. '
         'Operación de administrador.\n')
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        try:
            catalog_service = self.client.main_service.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de catálogo disponible.\n')
            return

        if not arg:
            print('\n[ERROR] Es necesario indicar un nuevo nombre.\n')
            return

        if not self.admin:
            print('\n[ERROR] Para realizar esta operación debe ser un administrador.\n')
            return

        newname = arg.strip()

        if not self.selected_media:
            print(
                '\n[ERROR] Debe seleccionar un medio antes. Escriba \'help select\' ' +
                'para más información.\n')
            return

        try:
            catalog_service.renameTile(self.selected_media.mediaId, newname, self.user_token)
            self.selected_media = catalog_service.getTile(self.selected_media.mediaId)

            if self.admin:
                self.prompt = (
                    f'[ADMIN]\nSelección actual: {self.selected_media.mediaId} '
                    f'({self.selected_media.info.name})\n> ')
            else:
                self.prompt = (
                    f'Usuario: {self.username}\nSelección actual: '
                    f'{self.selected_media.mediaId} ({self.selected_media.info.name})\n> ')
            print('\n[INFO] Título renombrado con éxito.\n')
        except IceFlix.Unauthorized:
            print(
                '\n[ERROR] Para realizar esta operación debe ser un administrador.\n')
            return
        except IceFlix.WrongMediaId as wmid:
            print(
                f'\n[ERROR] El medio con id {wmid.mediaId} no está disponible en este momento.\n')
            return
        except IceFlix.TemporaryUnavailable:
            print(
                f'\n[ERROR] El medio con id {self.selected_media.mediaId} ' +
                'no está disponible en este momento.\n')
            return

    def do_addtags(self, arg, initial=None): # pylint: disable=unused-argument, too-many-return-statements
        '''addtags tags - Añade una secuencia de tags al medio seleccionado.
            Ejemplo:
                Tags a añadir al medio seleccionado: Accion, Thriller, Romántica.
                Comando: addtags Accion,Thriller,Romántica
                *La lista de tags se indicará escribiendo las tags separadas por \',\'.
                **El nombre de los tags es sensible a mayúsculas.
        '''
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        try:
            catalog_service = self.client.main_service.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de catálogo disponible.\n')
            return

        if not self.user_token:
            print(
                '\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return

        if self.admin:
            print('\n[ERROR] No puede realizar esta operación como administrador.\n')
            return

        if not self.selected_media:
            print('\n[ERROR] Debe seleccionar antes un medio.\n')
            return

        if not arg:
            print(
                '\n[ERROR] Debe indicar al menos una tag. Escribe \'help addtags\' ' +
                'para más información.\n')
            return

        media_id = self.selected_media.mediaId
        tag_list = [tag.strip() for tag in arg.split(',')]

        try:
            catalog_service.addTags(media_id, tag_list, self.user_token)
            print('\n[INFO] Tags añadidas correctamente.\n')
        except IceFlix.Unauthorized:
            print(
                '\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
            return
        except IceFlix.WrongMediaId:
            print(
                f'\n[ERROR] ID de medio {media_id} no encontrado en el catálogo.\n')
            return

    def do_removetags(self, arg, initial=None): # pylint: disable=unused-argument, too-many-return-statements
        '''removetags tags - Elimina una secuencia de tags al medio seleccionado.
            Ejemplo:
                Tags a eliminar del medio seleccionado: Accion, Thriller, Romántica.
                Comando: removetags Accion,Thriller,Romántica
                *La lista de tags se indicará escribiendo las tags separadas por \',\'.
                **El nombre de los tags es sensible a mayúsculas.
        '''
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        try:
            catalog_service = self.client.main_service.getCatalog()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de catálogo disponible.\n')
            return

        if not self.user_token:
            print(
                '\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return

        if not self.selected_media:
            print('\n[ERROR] Debe seleccionar antes un medio.\n')
            return

        if self.admin:
            print('\n[ERROR] No puede realizar esta operación como administrador.\n')
            return

        if not arg:
            print(
                '\n[ERROR] Debe indicar al menos una tag. Escribe \'help addtags\' ' +
                'para más información.\n')
            return

        media_id = self.selected_media.mediaId
        tag_list = [tag.strip() for tag in arg.split(',')]

        try:
            catalog_service.removeTags(media_id, tag_list, self.user_token)
            print('\n[INFO] Tags eliminadas correctamente.\n')
        except IceFlix.Unauthorized:
            print(
                '\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
            return
        except IceFlix.WrongMediaId as wmid:
            print(
                f'\n[ERROR] ID de medio {wmid.mediaId} no encontrado en el catálogo.\n')
            return

    def do_adduser(self, initial=None): # pylint: disable=unused-argument
        ('adduser - Asks for a username and a password and then add the user to the users '
         'database.\n')
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        try:
            auth_service = self.client.main_service.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de autenticación disponible.\n')
            return

        if not self.admin:
            print('\n[ERROR] Para realizar esta operación debe ser un administrador.\n')
            return
        try:
            username = input('Nombre del nuevo usuario: ')
            password_hash = get_password_sha256(getpass('Contraseña del nuevo usuario: '))
            auth_service.addUser(username, password_hash, self.user_token)
            print('\n[INFO] Usuario añadido correctamente.\n')
        except IceFlix.Unauthorized:
            print('\n[ERROR] Token de administrador no válido.\n')
        except EOFError:
            print()
            return

    def do_removeuser(self, arg, initial=None): # pylint: disable=unused-argument
        'removeuser <username> - Removes the user from the database.'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        try:
            auth_service = self.client.main_service.getAuthenticator()
        except IceFlix.TemporaryUnavailable:
            print('\n[ERROR] No existe ningún servicio de autenticación disponible.\n')
            return

        if not self.admin:
            print('\n[ERROR] Para realizar esta operación debe ser un administrador.\n')
            return

        if not arg:
            print(
                '\n[ERROR] Debe indicar un nombre de usuario. Escribe \'help removeuser\' ' +
                'para más información.\n')
            return

        username = arg.strip()

        try:
            auth_service.removeUser(username, self.user_token)
            print(f'\n[INFO] Se ha elimiado el usuario \'{username}\' con éxito.\n')
        except IceFlix.Unauthorized:
            print(
                '\n[ERROR] No es un administrador o no se ha encontrado ' +
                f'el usuario \'{username}\'.\n')
            return

    def do_play(self, initial=None): # pylint: disable=unused-argument, too-many-return-statements
        'play - Inicia la reproducción del medio seleccionado.\n'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if not self.user_token:
            print(
                '\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return

        if not self.selected_media:
            print('\n[ERROR] Debe seleccionar antes un medio.\n')
            return

        if self.client.player:
            print('\n[ERROR] Ya se está reproduciendo otro medio.\n')
            return

        try:
            self.controller = self.selected_media.provider \
                .getStream(self.selected_media.mediaId, self.user_token)
            if not self.controller:
                print('\n[ERROR] No se ha podido obtener un controlador válido.\n')
                return

            self.controller_topic = topics.getTopic(topics.getTopicManager(
                self.client.communicator), f'{self.controller.service_id}')
            controller = StreamSync(self)
            self.controller_subscriber_proxy = self.client.adapter.addWithUUID(controller)
            self.controller_topic.subscribeAndGetPublisher({}, self.controller_subscriber_proxy)

            rtsp_config = self.controller.getSDP(self.user_token, 5000)
            if not rtsp_config:
                print('\n[ERROR] No se ha podido obtener la configuración de stream.')
                return
        except IceFlix.Unauthorized:
            print(
                '\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
            return
        except IceFlix.WrongMediaId as wmid:
            print(
                f'\n[ERROR] ID de medio {wmid.mediaId} no encontrado en el catálogo.\n')
            return

        self.prompt = '[REPRODUCIENDO] ' + self.prompt

        self.client.player = RTSPPlayer()
        self.client.player.play(rtsp_config)
        print('Puede escribir \'stop\' para parar la reproducción del medio.\n')

    def do_stop(self, initial=None): # pylint: disable=unused-argument
        'stop - Para la reproducción actual si hay alguna en marcha.\n'
        if not self.iniciado:
            print(
                '\n[ERROR] No se ha conectado a ningún servicio. ' +
                'Escriba \'help iniciar\' para más información.\n')
            return

        if not self.client.player:
            print('\n[ERROR] No hay ninguna reproducción en curso.\n')
            return

        self.prompt = self.prompt.replace('[REPRODUCIENDO] ', '')
        self.client.player.stop()
        self.controller.stop()
        self.controller_topic.unsubscribe(self.controller_subscriber_proxy)
        self.controller_topic = None
        self.controller_subscriber_proxy = None
        self.client.player = None

    def do_q(self, initial=None): # pylint: disable=unused-argument
        'q - Cierra el cliente de IceFlix.\n'
        if self.logged:
            self.do_logout()
        if self.client.player:
            self.do_stop()
        return True

    def start(self):
        'Función que inicia el bucle para el CLI.'
        self.cmdloop()

    # ONLY DEBUG
    # def do_autologin(self, initial=None): # pylint: disable=unused-argument, missing-function-docstring
    #     self.username = 'iago'
    #     self.password_hash = get_password_sha256('mipass')
    #     self.user_token = self.client.auth_service.refreshAuthorization(
    #         self.username, self.password_hash)
    #     self.logged = True
    #     print('\n[INFO] Se ha iniciado sesión correctamente.\n')
    #     self.prompt = f'{self.username}> '


class Client(Ice.Application):
    '''Clase que hereda de Ice para tener acceso a sus funcionalidades.'''
    def run(self, argv): # pylint: disable=arguments-differ, unused-argument
        shell = IceFlixCLI()
        shell.client = IceFlixClient(self.communicator())
        self.shutdownOnInterrupt()
        shell.start()


if __name__ == '__main__':
    CLI = Client()
    sys.exit(CLI.main(sys.argv))
