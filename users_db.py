'''Implementación de la clase correspondiente a los datos de userDB de IceFlix.'''

import Ice # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class UsersDB(IceFlix.UsersDB):
    'Clase para el objeto UsersDB de IceFlix.'
    def __init__(self, users_passwords={}, users_token={}):
        self.userPasswords = users_passwords
        self.usersToken = users_token