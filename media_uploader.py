#!/usr/bin/env python3

"""Servidor de RemoteFile y RemoteFileSystem.

Implementación de los sirvientes de RemoteFile and RemoteFileSystem junto a
la instrumentación para ofrecerlos como servicio.
"""

import os
import sys

import Ice
from streaming import MediaUploader
from utils import CLIENT_MEDIA_DIR

Ice.loadSlice('iceflix.ice')
import IceFlix  # pylint: disable=import-error,wrong-import-position

class MediaUploader(IceFlix.MediaUploader):
    '''Clase que implementa la interfaz de IceFlix para el media uploader.'''
    def __init__(self, filename):
        self._filename = filename
        self._fd = open(filename, 'rb') # pylint: disable=consider-using-with

    def receive(self, size, current=None): # pylint: disable=invalid-name, unused-argument
        '''Recibe los datos.'''
        chunk = self._fd_.read(size)
        return chunk

    def close(self, current=None):
        '''Cierra el archivo.'''
        self._fd_.close()
        current.adapter.remove(current.id)

class UploaderServer(Ice.Application):
    """Implementacion del servidor."""
    def run(self, args):
        """Entry point."""
        args.pop()
        root_fs = CLIENT_MEDIA_DIR if not args else args.pop()
        servant = MediaUploader(root_fs)

        adapter = self.communicator().createObjectAdapterWithEndpoints("UploaderAdapter", "tcp -p 36000")
        proxy = adapter.add(servant, self.communicator().stringToIdentity('UploaderService'))
        print(proxy, flush=True)
        adapter.activate()

        self.shutdownOnInterrupt()
        self.communicator().waitForShutdown()

        return 0


if __name__ == '__main__':
    sys.exit(UploaderServer().main(sys.argv))