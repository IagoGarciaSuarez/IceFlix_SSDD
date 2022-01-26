'''Clase para el topic de revocaciones.'''
import threading
import Ice  # pylint: disable=import-error,wrong-import-position
from utils import read_cred_db, write_cred_db
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class Revocations(IceFlix.Revocations):
    """Revocations class to listen to revocations of tokens and users."""
    def __init__(self, service_servant, service=None):
        """Initialize the Revocations object."""
        self._service_servant = service_servant
        self._service = service
        self.publisher = None

    def revokeToken(self, user_token, srv_id, current=None): # pylint: disable=unused-argument, invalid-name
        """Revokes a token."""
        if self._service and self._service.ice_isA('::IceFlix::Authenticator'):
            print(f'\n[AUTH SERVICE][INFO] Token revocation from {srv_id}')
            username = self._service_servant.whois(user_token)
            self._service_servant.users_token.pop(username)

        elif self._service and self._service.ice_isA('::IceFlix::StreamController'):
            if srv_id == self._service_servant.service_id:
                return
            print(
                f'\n[CONTROLLER SERVICE][WARNING] Token revocation from {srv_id}. ' +
                'Asking for refresh...')
            if self._service_servant.user_token == user_token:
                self._service_servant.stream_sync.requestAuthentication()
                self._service_servant.auth_timer = threading.Timer(5.0, self._service_servant.stop)
                self._service_servant.auth_timer.start()
        elif self._service_servant.logged:
            self._service_servant.token_refreshed = False
            try:
                auth_service = self._service_servant.client.main_service.getAuthenticator()
                new_token = auth_service.refreshAuthorization(
                    self._service_servant.username, self._service_servant.password_hash)
                self._service_servant.user_token = new_token
                self._service_servant.token_refreshed = True
            except IceFlix.Unauthorized:
                print('\n[ERROR] Las credenciales no son válidas.\n')
                self._service_servant.do_logout()
            except IceFlix.TemporaryUnavailable:
                print('\n[ERROR] No existe ningún servicio de autenticación disponible.\n')
                self._service_servant.do_logout()

    def revokeUser(self, user, srvId, current=None):  # pylint: disable=unused-argument, invalid-name
        """Removes a user."""
        if self._service and self._service.ice_isA('::IceFlix::Authenticator'):
            if srvId == self._service_servant.service_id:
                return
            print(f'\n[AUTH SERVICE][INFO] User revocation from {srvId}')
            credentials = read_cred_db(self._service_servant.credentials_db)
            credentials.pop(user)
            write_cred_db(credentials, self._service_servant.credentials_db)
