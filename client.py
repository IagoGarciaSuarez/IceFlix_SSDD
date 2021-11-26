#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import cmd

from utils import getPasswordSHA256
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

        return (mainService, authService, catalogService)
        while True:    
            username = None
            password = None
            opt = input('Escriba el número correspondiente a una de las siguientes opciones:'+
                        '\n1. Iniciar sesión.\n2. Buscar en el catálogo.\n3. Salir.>')
            if opt == '1':
                username = input('Nombre de usuario:')
                password = getPasswordSHA256(getpass('Contraseña:'))
                userToken = authService.refreshAuthorization(username, password)
                if mainService.isAdmin(userToken):
                    self.adminMenu()
                
                else:
                    self.userMenu()
            
            elif opt == '2':
                self.catalogMenu()
            
            elif opt == '3':
                break
            else:
                print('No se ha reconocido la opción elegida. Inténtelo de nuevo.\n')

        
        return 0
    
    # def catalogMenu(self):
    #     pass
    # def adminMenu(self):
    #     pass
    # def userMenu(self, username):
    #     opt = input(f'{username} > Escriba el número correspondiente a una de las siguientes ' +
    #                 'opciones:\n1. Cerrar sesión.\n2. Buscar en el catálogo.\n3. >')
    #     if opt == '1':
    #         return
    #     if opt == '2':
    #         catalog_opt = input(f'{username} > \n1. Buscar por nombre exacto.' +
    #                     '\n2. Buscar títulos que incluyan el nombre.\n' + 
    #                     '3. Buscar por tags.\n>')
    
class IceFlixCLI(cmd.Cmd):
    prompt = '> '
    intro = 'ICEFLIX_BANNER' + '\nEscribe \'help\' o \'?\' para mostrar los comandos disponibles.\n'
    mainService, authService, catalogService = Client().main(sys.argv)
    userToken = None
    lastSearchResult = None
    state = 'init'

    def do_login(self, initial=None):
        'login - Inicia sesión una vez indicado un usuario y contraseña correctos.\n'
        if self.state == 'init':            
            username = input('Nombre de usuario:')
            password = getPasswordSHA256(getpass('Contraseña:'))
            try:
                self.userToken = self.authService.refreshAuthorization(username, password)
                print('\n[INFO] Se ha iniciado sesión correctamente.\n')
                self.prompt=f'{username}> '
            except:
                print('\n[ERROR] Error al introducir las credenciales.\n')
    def do_search(self, mode, name, initial=None):
        '''search <mode> <name> - Busca medios según el modo seleccionado.
            mode:   1 - Búsqueda por nombre exacto.
                    2 - Búsqueda por nombre incluído.
                    3 - Búsqueda por tags exactas (es necesario iniciar sesión).
                    4 - Búsqueda por tags incluídas (es necesario iniciar sesión).
        '''
        if mode == '1':
            self.lastSearchResult = self.catalogService.getTilesByName(name, True)
            if not self.lastSearchResult:
                print('[INFO] No se ha encontrado ningún resultado.\n')
                return
            


#sys.exit(Client().main(sys.argv))
if __name__ == "__main__":
    wt = IceFlixCLI()
    try:
        wt.cmdloop()
    except KeyboardInterrupt:
        wt.close()
