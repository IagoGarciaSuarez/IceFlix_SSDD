#!/usr/bin/make -f
# -*- mode:makefile -*-

run-server:
		./server.py --Ice.Config=Server.config | tee proxy.out

run-catalog:
		./catalog.py --Ice.Config=Catalog.config '$(shell head -1 proxy.out)'

run-auth:
		./authenticator.py --Ice.Config=Auth.config '$(shell head -1 proxy.out)'

run-streaming:
		./streaming.py --Ice.Config=Provider.config '$(shell head -1 proxy.out)'

run-client:
		./client.py '$(shell head -1 proxy.out)'

clean:
		$(RM) *~ proxy.out
		$(RM) -rf dist
