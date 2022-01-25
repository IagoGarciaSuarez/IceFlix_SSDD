'''Clase para el topic de los anuncios de stream.'''
import Ice  # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class StreamAnnouncements(IceFlix.StreamAnnouncements):
    """Stream announcements class to announce new media and media removal."""
    def __init__(self, service_servant):
        """Initialize the StreamAnnouncements object."""
        self._service_servant = service_servant

    def newMedia(self, media_id, initial_name, srv_id, current=None): # pylint: disable=unused-argument, invalid-name
        """Adds new media to the catalog."""
        if srv_id not in self._service_servant.discover_subscriber.known_services:
            return
        if not self._service_servant.catalog.is_in_catalog(media_id):
            self._service_servant.catalog.add_media(media_id, initial_name)
        if srv_id in self._service_servant.discover_subscriber.provider_services.keys():
            self._service_servant.media_with_proxy[media_id] = self._service_servant \
                .discover_subscriber.provider_services[srv_id]

    def removedMedia(self, media_id, srv_id, current=None):  # pylint: disable=unused-argument, invalid-name
        """Removes a media entry in the catalog."""
        if srv_id not in self._service_servant.discover_subscriber.known_services:
            return
        if self._service_servant.catalog.is_in_catalog(media_id):
            self._service_servant.catalog.remove_media(media_id)
        if media_id in self._service_servant.media_with_proxy.keys():
            self._service_servant.media_with_proxy.pop(media_id)
