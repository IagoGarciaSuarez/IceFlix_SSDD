#!/usr/bin/make -f
# -*- mode:makefile -*-

run-registry:
		icegridregistry --Ice.Config=configurations/registry.config

run-server:
		./server.py --Ice.Config=configurations/Server.config | tee proxy.out

run-catalog:
		./catalog.py --Ice.Config=configurations/Catalog.config '$(shell head -1 proxy.out)'

run-auth:
		./authenticator.py --Ice.Config=configurations/Auth.config '$(shell head -1 proxy.out)'

run-streaming:
		./streaming.py --Ice.Config=configurations/Provider.config '$(shell head -1 proxy.out)'

run-client:
		./client.py '$(shell head -1 proxy.out)'

clean:
		$(RM) *~ proxy.out
		$(RM) -rf dist
