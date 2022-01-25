'''Implementación de las clases Media y MediaInfo de IceFlix.'''

import Ice # pylint: disable=import-error,wrong-import-position
Ice.loadSlice('iceflix.ice')
import IceFlix # pylint: disable=import-error,wrong-import-position

class Media(IceFlix.Media):
    'Clase para el objeto Media de IceFlix.'
    def __init__(self, mediaId, provider, info):
        self.mediaId = mediaId
        self.provider = provider
        self.info = info

class MediaInfo(IceFlix.MediaInfo):
    'Clase para el objeto MediaInfo que forma parte del objeto Media de IceFlix.'
    def __init__(self, name, tags=[]):
        self.name = name
        self.tags = tags

class MediaDB(IceFlix.MediaDB):
    'Clase para el objeto MediaDB'
    def __init__(self, mediaId, name, tagsPerUser):
        self.mediaId = mediaId
        self.name = name
        self.tagsPerUser = tagsPerUser
