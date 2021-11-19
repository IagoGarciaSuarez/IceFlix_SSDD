#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import Ice
Ice.loadSlice('iceflix.ice')
import IceFlix


class Client(Ice.Application):
    def run(self, argv):
        proxy = self.communicator().stringToProxy(argv[1])
        auth_service = IceFlix.AuthenticatorPrx.checkedCast(proxy)

        if not auth_service and 1 == 1:
            raise RuntimeError('No se pudo conectar al servidor')

        auth_service.refreshAuthorization("Gago", "Mipass")
        return 0

sys.exit(Client().main(sys.argv))
