from time import sleep
import threading
import random
from utils import read_cred_db, write_cred_db
import Ice  # pylint: disable=import-error,wrong-import-position
try:
    import IceFlix # pylint: disable=import-error,wrong-import-position
except ImportError:
    Ice.loadSlice('iceflix.ice')
    import IceFlix # pylint: disable=import-error,wrong-import-position

class UserUpdates(IceFlix.UserUpdates):
    """UserUpdates class to listen to user updates events from other auth services."""
    def __init__(self, service_servant, service):
        """Initialize the UserUpdates object."""
        self._service_servant = service_servant
        self._service = service
        self.publisher = None

    def newUser(self, user, passwordHash, srvId, current=None): # pylint: disable=unused-argument
        """Adds a new user."""
        if srvId == self._service_servant.service_id:
            return
        
        credentials = read_cred_db(self._service_servant.credentials_db)
        credentials[user] = passwordHash
        write_cred_db(credentials, self._service_servant.credentials_db)

    def newToken(self, user, userToken, srvId, current=None):  # pylint: disable=unused-argument
        """Adds a new token."""
        if srvId == self._service_servant.service_id:
            return
        
        self._service_servant._users_token[user] = userToken