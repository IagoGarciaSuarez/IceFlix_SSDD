import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix

class Media(IceFlix.Media):
    def __init__(self, id, provider, info):
        self.id = id
        self.provider = provider
        self.info = info

class MediaInfo(IceFlix.MediaInfo):
    def __init__(self, name, tags):
        self.name = name
        self.tags = tags