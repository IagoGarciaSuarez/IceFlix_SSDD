import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Media(IceFlix.Media):
    def __init__(self, mediaId, provider, info):
        self.mediaId = mediaId
        self.provider = provider
        self.info = info

class MediaInfo(IceFlix.MediaInfo):
    def __init__(self, name, tags=[]):
        self.name = name
        self.tags = tags