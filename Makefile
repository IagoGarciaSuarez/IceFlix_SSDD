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

clean:
	$(RM) *.out
	$(RM) -r __pycache__ IceStorm


# run-registry:
# 		icegridregistry --Ice.Config=configurations/registry.config

# # run-server:
# # 		./server.py --Ice.Config=configurations/Server.config | tee proxy.out

# run-catalog:
# 		./catalog.py --Ice.Config=configurations/Catalog.config '$(shell head -1 proxy.out)'

# run-auth:
# 		./authenticator.py --Ice.Config=configurations/Auth.config '$(shell head -1 proxy.out)'

# run-streaming:
# 		./streaming.py --Ice.Config=configurations/Provider.config '$(shell head -1 proxy.out)'

# run-client:
# 		./client.py

# clean:
# 		$(RM) *~ proxy.out
# 		$(RM) -rf dist
