#!/usr/bin/make -f
# -*- mode:makefile -*-

DIRCONFIG := configurations/

all: 
	clean \
	start
	sleep 1
	$(MAKE) run-auth

start:
	$(MAKE) run-icestorm
	sleep 1
	$(MAKE) run-server

run-icestorm:
	mkdir -p IceStorm/
	gnome-terminal -- bash -c \
	"icebox --Ice.Config=icebox.config; bash"

run-server:
	gnome-terminal -- bash -c \
	"./server.py --Ice.Config=$(DIRCONFIG)Server.config | tee server.out; bash"

run-auth:
	gnome-terminal -- bash -c \
	"./authenticator.py --Ice.Config=$(DIRCONFIG)Auth.config; bash"

run-catalog:
	gnome-terminal -- bash -c \
	"./catalog.py --Ice.Config=$(DIRCONFIG)Catalog.config; bash"

cleandb:
	bash -c "rm -- persistence/catalogDB/!(catalog.db|tagsDB.json);"
	bash -c "rm -- persistence/credentialsDB/!(credentials.json)"
clean:
	$(RM) *.out
	$(RM) -r __pycache__ IceStorm


# run-registry:
# 		icegridregistry --Ice.Config=configurations/registry.config

# # run-server:
# # 		./server.py --Ice.Config=configurations/Server.config | tee proxy.out


# run-auth:
# 		./authenticator.py --Ice.Config=configurations/Auth.config '$(shell head -1 proxy.out)'

# run-streaming:
# 		./streaming.py --Ice.Config=configurations/Provider.config '$(shell head -1 proxy.out)'

# run-client:
# 		./client.py

# clean:
# 		$(RM) *~ proxy.out
# 		$(RM) -rf dist
