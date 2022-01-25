'''Catalog updates topic class'''
import Ice # pylint: disable=import-error,wrong-import-position
from utils import read_tags_db, write_tags_db
try:
    import IceFlix # pylint: disable=import-error,wrong-import-position
except ImportError:
    Ice.loadSlice('iceflix.ice')
    import IceFlix # pylint: disable=import-error,wrong-import-position

class CatalogUpdates(IceFlix.CatalogUpdates):
    """CatalogUpdates class to listen to catalog updates events from other catalog services."""
    def __init__(self, service_servant):
        """Initialize the CatalogUpdates object."""
        self._service_servant = service_servant
        self.publisher = None

    def renameTile(self, media_id, name, srv_id, current=None): # pylint: disable=unused-argument, invalid-name
        """Renames a tile."""
        if srv_id == self._service_servant.service_id \
            or not self._service_servant.catalog.is_in_catalog(media_id):
            return

        self._service_servant.catalog.rename_media(media_id, name)

    def addTags(self, media_id, tags, user, srv_id, current=None):  # pylint: disable=unused-argument, invalid-name, too-many-arguments
        """Adds new tags."""
        if srv_id == self._service_servant.service_id:
            return

        tags_db = read_tags_db(self._service_servant.tags_db)

        if user in tags_db and media_id in tags_db[user]:
            for tag in tags:
                tags_db[user][media_id].append(tag)
        else:
            tags_dic = {}
            tags_dic[media_id] = tags
            tags_db[user] = tags_dic

        write_tags_db(tags_db, self._service_servant.tags_db)

    def removeTags(self, media_id, tags, user, srv_id, current=None): # pylint: disable=unused-argument, invalid-name, too-many-arguments
        """Remove tags from a given media."""
        if srv_id == self._service_servant.service_id:
            return

        tags_db = read_tags_db(self._service_servant.tags_db)
        if user in tags_db and media_id in tags_db[user]:
            tags_db[user][media_id] = [tag for tag in tags_db[user][media_id] if tag not in tags]

        write_tags_db(tags_db, self._service_servant.tags_db)
