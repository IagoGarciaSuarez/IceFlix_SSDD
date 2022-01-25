'''Implementación del topic de sincronización de stream.'''
import threading
import Ice  # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class StreamSync(IceFlix.StreamSync): # pylint: disable=too-few-public-methods
    """StreamSync object for the stream sync topic."""
    def __init__(self, servant):
        """Initialize StreamSync."""
        self.servant = servant

    def requestAuthentication(self, current=None): # pylint: disable=unused-argument, invalid-name
        """Request authentication event when token is revoked."""
        if self.servant.token_refreshed:
            self.servant.controller.refreshAuthentication(self.servant.user_token)
        else:
            refresh_thread = threading.Timer(
                0.5, self.servant.controller.refreshAuthentication, [self.servant.user_token])
            refresh_thread.start()
