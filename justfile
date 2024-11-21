db_container_name  := "mysql_db_gachaandgames"
allowed_services := "admin auctions auth currency feedback gacha inventory profile pvp dbmanager"

default: up

on:
	#!/bin/bash
	if $(systemctl --quiet is-active docker); then
		echo "Docker daemon is already active..."
	else
		echo "Starting Docker daemon..."
		sudo systemctl start docker
	fi

off: down
	#!/bin/bash
	read -p "Turn off Docker daemon? [Y/n] " res 
	if [ -z "$res" ] || [ "$res" == "Y" ]; then
		sudo systemctl stop docker docker.socket
	fi

up: on
	#!/bin/bash
	if [ $(docker compose ps | wc -l) -ne 13 ]; then
		echo "Starting containers..."
		docker compose up -d
	else
		echo "Containers are already running..."
	fi

down:
	#!/bin/bash
	if [ $(docker compose ps | wc -l) -le 13 ]; then
		echo "Stopping containers..."
		docker compose down
	else
		echo "Containers are stopped..."
	fi

start: on
	#!/bin/bash
	if [ $(docker compose ps | wc -l) -ne 13 ]; then
		echo "Starting containers..."
		docker compose start
	else
		echo "Containers are already running..."
	fi

stop:
	#!/bin/bash
	if [ $(docker compose ps | wc -l) -eq 13 ]; then
		echo "Stopping containers..."
		docker compose stop
	else
		echo "Containers are stopped..."
	fi

ps:
	#!/bin/bash
	if $(systemctl --quiet is-active docker); then
		docker compose ps -a
	else
		echo "Docker daemon is stopped."
	fi

@db: up
	echo "Get into {{db_container_name}}..."
	docker exec -it {{db_container_name}} mysql -u root -h 0.0.0.0 -P 3306 -p

build: on
	docker compose build

config: on
	docker compose config

logs service_name replica_number='1':
	#!/bin/bash
	allowed_services="{{allowed_services}}"
	service_name="{{service_name}}"
	replica_number="{{replica_number}}"
	if [[ " $allowed_services " =~ (^|[[:space:]])"$service_name"($|[[:space:]]) ]]; then
		if [[ "$service_name" == "dbmanager" ]]; then
			container_name="unipi-gatchaandgames-db_manager-${replica_number}"
		else
			container_name="unipi-gatchaandgames-service_${service_name}-${replica_number}"
		fi
		echo "Showing logs for $container_name..."
		docker logs -f $container_name
	else
		echo "Invalid service name. Must be one of: $allowed_services"
		exit 1
	fi
