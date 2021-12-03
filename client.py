#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import cmd

from utils import getPasswordSHA256, ICEFLIX_BANNER
from getpass import getpass
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix


class Client(Ice.Application):
    def run(self, argv):
        broker = Ice.initialize(argv)
        
        mainProxy = broker.stringToProxy(argv[1])
        mainService = IceFlix.MainPrx.checkedCast(mainProxy)

        if not mainService:
            raise RuntimeError('[ERROR] Invalid proxy for the main service')

        for i in range(3):
            try:
                authService = mainService.getAuthenticator()

                print('[INFO] Servicio de autenticación conectado.\n')
                break

            except IceFlix.TemporaryUnavailable:
                print('[ERROR] Ha ocurrido un error al conectar con el servicio de autenticación.\n')
                for x in range(10, 0, -1):
                    print(f'[ERROR] Reintentando en {x} segundos. [{i+1}/3]', end='\r')
                    time.sleep(1)
        
        for i in range(3):
            try:
                catalogService = mainService.getCatalog()
                print('[INFO] Servicio de catálogo conectado.\n')
                break

            except IceFlix.TemporaryUnavailable:
                print('[ERROR] Ha ocurrido un error al conectar con el servicio de catálogo.\n')
                for x in range(10, 0, -1):
                    print(f'[ERROR] Reintentando en {x} segundos. [{i+1}/3]', end='\r')
                    time.sleep(1)

class IceFlixClient:
    def __init__(self, broker):
        self._communicator = broker
        self.adapter = self._communicator.createObjectAdapterWithEndpoints('IceFlix', 'tcp')
        self.adapter.activate()
        self.mainService = None
        self.catalogService = None
        self.authService = None
        self._user = None
        self._passwordHash = None
        self._iceflixPrx = None
        self._iceflix = None
        self._media = None
        self._player = None

    def run(self, argv):
        mainProxy = self._communicator.stringToProxy(argv[1])
        self.mainService = IceFlix.MainPrx.checkedCast(mainProxy)

        if not self.mainService:
            raise RuntimeError('[ERROR] Invalid proxy for the main service')

        for i in range(3):
            try:
                self.authService = self.mainService.getAuthenticator()
                print('[INFO] Servicio de autenticación conectado.\n')
                break

            except IceFlix.TemporaryUnavailable:
                print('[ERROR] Ha ocurrido un error al conectar con el servicio de autenticación.\n')
                for x in range(10, 0, -1):
                    print(f'[ERROR] Reintentando en {x} segundos. [{i+1}/3]', end='\r')
                    time.sleep(1)
        
        for i in range(3):
            try:
                self.catalogService = self.mainService.getCatalog()
                print('[INFO] Servicio de catálogo conectado.\n')
                break

            except IceFlix.TemporaryUnavailable:
                print('[ERROR] Ha ocurrido un error al conectar con el servicio de catálogo.\n')
                for x in range(10, 0, -1):
                    print(f'[ERROR] Reintentando en {x} segundos. [{i+1}/3]', end='\r')
                    time.sleep(1)


class IceFlixCLI(cmd.Cmd):
    '''IceFlix shell''' 
    def __init__(self, stdin=None, stdout=None): 
        if stdin is not None: 
            self.use_rawinput=False 
        super(IceFlixCLI, self).__init__(completekey='tab', stdin=stdin, stdout=stdout) 
        self.client = None 
        self._last_results_ = {} 

    prompt = '> '
    intro = ICEFLIX_BANNER + '\nEscribe \'help\' o \'?\' para mostrar los comandos disponibles.\n'
    username = None
    passwordHash = None
    userToken = None
    lastSearchResult = None
    logged = False
    admin = False
    selectedMedia = None

    def do_login(self, initial=None):
        'login - Inicia sesión una vez indicado un usuario y contraseña correctos. Se puede iniciar sesión como administrador utilizando el comando adminlogin.'
        if not self.logged:            
            self.username = input('Nombre de usuario:')
            self.passwordHash = getPasswordSHA256(getpass('Contraseña:'))
            try:
                self.userToken = self.client.authService.refreshAuthorization(self.username, self.passwordHash)
                self.logged = True
                print('\n[INFO] Se ha iniciado sesión correctamente.\n')
                self.prompt=f'{self.username}> '
            except:
                print('\n[ERROR] Error al introducir las credenciales.\n')
        else:
            print(f'\n[ERROR] Ya existe una sesión iniciada por {self.username}.\n')

    def do_adminlogin(self, initial=None):
        'adminlogin - Inicia sesión de administrador una vez indicado un admin token correcto.\n'
        if not self.logged:   
            self.userToken = input('Token de administrador: ')
            if self.client.mainService.isAdmin(self.userToken):
                self.logged = True
                self.admin = True
                self.username = None
                self.passwordHash = None
                print('\n[INFO] Se ha iniciado sesión de administrador correctamente.\n')
                self.prompt=f'[ADMIN]> '
            else:
                print('\n[ERROR] Error al introducir el token de administrador.\n')
        
        else:
            print(f'\n[ERROR] Ya existe una sesión iniciada por {self.username}.\n')            

    def do_logout(self, initial=None):
        if self.logged:
            self.username = None
            self.passwordHash = None
            self.userToken = None
            self.logged = False
            self.admin = False
            self.prompt = '> '
            print('\n[INFO] Se ha cerrado la sesión correctamente.\n')
        
        else:
            print('\n[ERROR] No hay ninguna sesión iniciada.\n')

    def do_search(self, arg, initial=None):
        '''search <mode> <name|tags> - Busca medios según el modo seleccionado.
            mode:   1 - Búsqueda por nombre exacto.
                    2 - Búsqueda por nombre incluído.
                    3 - Búsqueda por tags exactas (es necesario iniciar sesión).
                    4 - Búsqueda por tags incluídas (es necesario iniciar sesión).
                    *Las tags se indicarán separadas por \',\'.
        '''
        argv = arg.split(' ', 1)
        if len(argv) < 2:
            print('\n[ERROR] Error en el número de argumentos. Escribe \'help addtags\' para más información.\n')
            return
        
        mode = argv[0].strip()  
        if mode == '1' or mode == '2':
            name = argv[1].strip()
            self._last_results_ = self.client.catalogService.getTilesByName(name, (mode=='1'))
        
        elif mode == '3' or mode == '4':
            tags = [tag.strip() for tag in argv[1].split(',')]
            try: 
                self._last_results_ = self.client.catalogService\
                    .getTilesByTags(tags, (mode=='3'), self.userToken)
            except IceFlix.Unauthorized:
                print('\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
                return

        else:
            print(f'\n[ERROR] No se ha reconocido el modo \'{mode}\'. Escribe \'help addtags\' para más información.\n ')
            return

        self.do_lastsearch()
                
    def do_lastsearch(self, initial=None):
        'lastsearch - Muestra los resultados de la última búsqued realizada.\n'
        if self._last_results_:
            for i, mediaId in zip(range(len(self._last_results_)), self._last_results_):
                try:
                    mediaInfo = self.client.catalogService.getTile(mediaId)
                except IceFlix.WrongMediaId as wmid:
                    print(f'\n[ERROR] No se ha encontrado el medio con id {wmid.id}\n')
                    return
                except IceFlix.TemporaryUnavailable:
                    print(f'\n[ERROR] El medio {mediaId} no está disponible en este momento.\n')
                    return
                
                if self.admin or not self.userToken:
                    print(f'Resultado {i+1}:\n\tTítulo: {mediaInfo.info.name}\n\tID: {mediaId}\n')

                else:
                    print(f'Resultado {i+1}:\n\tTítulo: {mediaInfo.info.name}\n' + 
                    f'\tTags de {self.username}: {mediaInfo.info.tags}\n\tID: {mediaId}\n')

            print(f'\n[INFO] Se han encontrado {len(self._last_results_)} resultados.\n')
        
        else:
            print('\n[INFO] No se ha encontrado ningún resultado.\n')

    def do_select(self, arg, initial=None):
        'select <mediaId> - Indicando el ID de un medio disponible, se selecciona dicho medio para poder realizar operaciones con él.\n'
        if not self.userToken:
            print('\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return
        
        if not arg:
            print('\n[ERROR] Debe indicar un ID. Escriba \'help select\' para más información.\n')
            return

        mediaId = arg.strip()
        
        try:
            self.selectedMedia = self.client.catalogService.getTile(mediaId)
        except IceFlix.WrongMediaId as wmid:
            print(f'\n[ERROR] No se ha encontrado el medio con id \'{wmid.id}\'.\n')
            return
        except IceFlix.TemporaryUnavailable:
            print(f'\n[ERROR] El medio {mediaId} no está disponible en este momento.\n')
            return
        if self.admin:
            self.prompt = f'[ADMIN]\nSelección actual: {self.selectedMedia.id} ({self.selectedMedia.info.name})\n> '
        else:
            self.prompt = f'Usuario: {self.username}\nSelección actual: {self.selectedMedia.id} ({self.selectedMedia.info.name})\n> '

    def do_unselect(self, initial=None):
        'unselect - Desselecciona el elemento seleccionado.\n'
        if not self.userToken:
            print('\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return        
        self.selectedMedia = None
        self.prompt = f'{self.username}> '

    def do_rename(self, arg, initial=None):
        'rename <nuevo nombre> - Cambia el nombre de un medio por el valor <nuevo nombre>. Operación de administrador.\n'
        if not arg:
            print('\n[ERROR] Es necesario indicar un nuevo nombre.\n')
            return

        newname = arg.strip()

        if not self.selectedMedia:
            print('\n[ERROR] Debe seleccionar un medio antes. Escriba \'help select\' para más información.\n')
            return

        try: 
            self.client.catalogService.renameTile(self.selectedMedia.id, newname, self.userToken)
            self.selectedMedia = self.client.catalogService.getTile(self.selectedMedia.id)

            if self.admin:
                self.prompt = f'[ADMIN]\nSelección actual: {self.selectedMedia.id} ({self.selectedMedia.info.name})\n> '
            else:
                self.prompt = f'Usuario: {self.username}\nSelección actual: {self.selectedMedia.id} ({self.selectedMedia.info.name})\n> '
            print('\n[INFO] Título renombrado con éxito.\n')
        except IceFlix.Unauthorized:
            print('\n[ERROR] Para realizar esta operación debe ser un administrador.\n')
            return
        except IceFlix.WrongMediaId as wmid:
            print(f'\n[ERROR] El medio con id {wmid.id} no está disponible en este momento.\n')
            return
    
    def do_addtags(self, arg, initial=None):
        '''addtags tags - Añade una secuencia de tags al medio seleccionado si se ha iniciado sesión previamente.
            Ejemplo:
                Tags a añadir al medio seleccionado: Accion, Thriller, Romántica.
                Comando: addtags Accion,Thriller,Romántica
                *La lista de tags se indicará escribiendo las tags separadas por \',\'.
                **El nombre de los tags es sensible a mayúsculas.
        '''
        if not self.userToken:
            print('\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return

        if not self.selectedMedia:
            print('\n[ERROR] Debe seleccionar antes un medio.\n')
            return

        if not arg:
            print('\n[ERROR] Debe indicar al menos una tag. Escribe \'help addtags\' para más información.\n')
            return

        mediaId = self.selectedMedia.id
        tagList = [tag.strip() for tag in arg.split(',')]

        try:
            self.client.catalogService.addTags(mediaId, tagList, self.userToken)
            print('\n[INFO] Tags añadidas correctamente.\n')
        except IceFlix.Unauthorized:
            print('\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
            return
        except IceFlix.WrongMediaId:
            print(f'\n[ERROR] ID de medio {mediaId} no encontrado en el catálogo.\n')
            return
        
    def do_removetags(self, arg, initial=None):
        '''removetags tags - Elimina una secuencia de tags al medio seleccionado si se ha iniciado sesión previamente.
            Ejemplo:
                Tags a eliminar del medio seleccionado: Accion, Thriller, Romántica.
                Comando: removetags Accion,Thriller,Romántica
                *La lista de tags se indicará escribiendo las tags separadas por \',\'.
                **El nombre de los tags es sensible a mayúsculas.
        '''
        if not self.userToken:
            print('\n[ERROR] Para realizar esta operación debe iniciar sesión antes.\n')
            return

        if not self.selectedMedia:
            print('\n[ERROR] Debe seleccionar antes un medio.\n')
            return

        if self.admin:
            print('\n[ERROR] No puede realizar esta operación como administrador.\n')
            return

        if not arg:
            print('\n[ERROR] Debe indicar al menos una tag. Escribe \'help addtags\' para más información.\n')
            return

        mediaId = self.selectedMedia.id
        tagList = [tag.strip() for tag in arg.split(',')]

        try:
            self.client.catalogService.removeTags(mediaId, tagList, self.userToken)
            print('\n[INFO] Tags eliminadas correctamente.\n')
        except IceFlix.Unauthorized:
            print('\n[ERROR] Token de usuario no válido. Es necesario iniciar sesión.\n')
            return
        except IceFlix.WrongMediaId:
            print(f'\n[ERROR] ID de medio {mediaId} no encontrado en el catálogo.\n')
            return

    def do_q(self, initial=None):
        return True

    def start(self):
        self.cmdloop()

    # If uncommented need change on search method for the name and tags input.
    # def precmd(self, line):
    #     line = line.lower()
    #     return line

    #BORRAR -- ONLY DEBUG
    def do_autologin(self, line):
        self.username = 'Gago'
        self.passwordHash = getPasswordSHA256('mipass')
        self.userToken = self.client.authService.refreshAuthorization(self.username, self.passwordHash)
        self.logged = True
        print('\n[INFO] Se ha iniciado sesión correctamente.\n')
        self.prompt=f'{self.username}> '
            
class Client(Ice.Application): 
    def run(self, argv): 
        self.shell = IceFlixCLI() 
        self.shell.client = IceFlixClient(self.communicator()) 
        self.shell.client.run(argv)
        self.shutdownOnInterrupt() 
        self.shell.start() 


if __name__ == '__main__':
    cli = Client() 
    sys.exit(cli.main(sys.argv)) 