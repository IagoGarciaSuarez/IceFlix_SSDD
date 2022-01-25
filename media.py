'''Implementación de las clases Media y MediaInfo de IceFlix.'''
import Ice # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class Media(IceFlix.Media): # pylint: disable=too-few-public-methods
    'Clase para el objeto Media de IceFlix.'
    def __init__(self, media_id, provider, info):
        self.mediaId = media_id # pylint: disable=invalid-name
        self.provider = provider
        self.info = info

class MediaInfo(IceFlix.MediaInfo): # pylint: disable=too-few-public-methods
    'Clase para el objeto MediaInfo que forma parte del objeto Media de IceFlix.'
    def __init__(self, name, tags):
        self.name = name
        self.tags = tags

class MediaDB(IceFlix.MediaDB): # pylint: disable=too-few-public-methods
    'Clase para el objeto MediaDB'
    def __init__(self, media_id, name, tags_per_user):
        self.mediaId = media_id # pylint: disable=invalid-name
        self.name = name
        self.tagsPerUser = tags_per_user # pylint: disable=invalid-name
