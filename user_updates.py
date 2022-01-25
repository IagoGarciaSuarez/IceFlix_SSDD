'''Implementación de la clase para el topic de actualizaciones de usuarios.'''
import Ice  # pylint: disable=import-error,wrong-import-position
from utils import read_cred_db, write_cred_db
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class UserUpdates(IceFlix.UserUpdates):
    """UserUpdates class to listen to user updates events from other auth services."""
    def __init__(self, service_servant, service):
        """Initialize the UserUpdates object."""
        self._service_servant = service_servant
        self._service = service
        self.publisher = None

    def newUser(self, user, password_hash, srv_id, current=None): # pylint: disable=unused-argument, invalid-name
        """Adds a new user."""
        if srv_id == self._service_servant.service_id:
            return

        credentials = read_cred_db(self._service_servant.credentials_db)
        credentials[user] = password_hash
        write_cred_db(credentials, self._service_servant.credentials_db)

    def newToken(self, user, user_token, srv_id, current=None):  # pylint: disable=unused-argument, invalid-name
        """Adds a new token."""
        if srv_id == self._service_servant.service_id:
            return
        self._service_servant.users_token[user] = user_token
