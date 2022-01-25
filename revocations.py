from utils import read_cred_db, write_cred_db
import Ice  # pylint: disable=import-error,wrong-import-position
try:
    import IceFlix # pylint: disable=import-error,wrong-import-position
except ImportError:
    Ice.loadSlice('iceflix.ice')
    import IceFlix # pylint: disable=import-error,wrong-import-position

class Revocations(IceFlix.Revocations):
    """UserUpdates class to listen to user updates events from other auth services."""
    def __init__(self, service_servant, service):
        """Initialize the UserUpdates object."""
        self._service_servant = service_servant
        self._service = service
        self.publisher = None

    def revokeToken(self, userToken, srvId, current=None): # pylint: disable=unused-argument
        """Revokes a token."""
        if srvId == self._service_servant.service_id:
            return
        
        credentials = read_cred_db(self._service_servant.credentials_db)
        credentials[user] = passwordHash
        write_cred_db(credentials, self._service_servant.credentials_db)

    def revokeUser(self, user, srvId, current=None):  # pylint: disable=unused-argument
        """Removes a user."""
        if srvId == self._service_servant.service_id:
            return

        credentials = read_cred_db(self._service_servant.credentials_db)
        credentials.pop(user)
        write_cred_db(credentials, self._service_servant.credentials_db)