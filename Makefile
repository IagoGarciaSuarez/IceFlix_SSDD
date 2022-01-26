#!/usr/bin/make -f
# -*- mode:makefile -*-

DIRCONFIG := configurations/

all: 
	$(MAKE) clean
	$(MAKE) start
	sleep 1
	$(MAKE) run-auth

start:
	$(MAKE) run-icestorm
	sleep 1
	$(MAKE) run-auth
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

run-streaming:
	gnome-terminal -- bash -c \
	"./streaming.py --Ice.Config=$(DIRCONFIG)Provider.config; bash"

clean:
	$(RM) *.out
	$(RM) -r __pycache__ IceStorm
	$(MAKE) cleandb
	
cleandb:
	bash -c "./cleandb.sh"

run-client:
	./client.py