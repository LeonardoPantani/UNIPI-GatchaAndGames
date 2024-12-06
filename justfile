allowed_services := "admin auction auth currency feedback gacha inventory profile pvp"
allowed_db_types := "primary replica proxy"

default: up

on:
    #!/bin/bash
    if $(systemctl --quiet is-active docker); then
        echo "Docker daemon is already active..."
    else
        echo "Starting Docker daemon..."
        sudo systemctl start docker
        echo "Docker daemon started."
    fi

off: down
    #!/bin/bash
    read -p "Turn off Docker daemon? [Y/n] " res 
    if [ -z "$res" ] || [ "$res" == "Y" ]; then
        sudo systemctl stop docker docker.socket
    fi

up: on
    #!/bin/bash
    find . -name "proxysql_stats.db" -type f -delete
    find . -name "proxysql.db" -type f -delete
    echo "Starting containers..."
    docker compose up -d

down:
    #!/bin/bash
    if [ $(docker compose ps | wc -l) -ne 1 ]; then
        echo "Removing containers and resetting volumes..."
        docker compose down -v
        docker compose down -v
    else
        echo "Containers are stopped..."
    fi

start: on
    #!/bin/bash
    find . -name "proxysql_stats.db" -type f -delete
    find . -name "proxysql.db" -type f -delete
    echo "Starting containers and building..."
    docker compose up --build -d

stop:
    #!/bin/bash
    if [ $(docker compose ps | wc -l) -ne 1 ]; then
        echo "Stopping containers..."
        docker compose stop
    else
        echo "Containers are stopped..."
    fi

ps:
    #!/bin/bash
    if systemctl --quiet is-active docker; then
        docker ps --format "table {{{{.ID}}\t{{{{.Names}}\t{{{{.Status}}"
    else
        echo "Docker daemon is stopped."
    fi

status:
    #!/bin/bash
    if systemctl --quiet is-active docker; then
        docker ps --format "table {{{{.ID}}\t{{{{.Names}}\t{{{{.Status}}"
    else
        echo "Docker daemon is stopped."
    fi

db service_name db_type='primary':
    #!/bin/bash
    allowed_services="{{allowed_services}}"
    allowed_db_types="{{allowed_db_types}}"
    service_name="{{service_name}}"
    db_type="{{db_type}}"

    if [[ "$service_name" == "redis" ]]; then
        container_name="unipi-gatchaandgames-redis"
        echo "Connecting to Redis at $container_name..."
        docker exec -it $container_name redis-cli
    elif [[ " $allowed_services " =~ (^|[[:space:]])"$service_name"($|[[:space:]]) ]] && \
         [[ " $allowed_db_types " =~ (^|[[:space:]])"$db_type"($|[[:space:]]) ]]; then
        container_name="unipi-gatchaandgames-service_${service_name}_db_${db_type}"
        if [[ "$db_type" == "proxy" ]]; then
            echo "Connecting to database $container_name with proxy credentials..."
            docker exec -it $container_name mysql -u radmin -h 127.0.0.1 -P 6032 -pradmin
        else
            echo "Connecting to database $container_name..."
            docker exec -it $container_name mysql -u root -h 0.0.0.0 gacha_test_db -P 3306 -proot
        fi
    else
        echo "Invalid service name or database type. Services: $allowed_services, DB Types: $allowed_db_types"
        exit 1
    fi


logs service_name db_type='' replica_number='1':
    #!/bin/bash
    allowed_services="{{allowed_services}}"
    allowed_db_types="{{allowed_db_types}}"
    service_name="{{service_name}}"
    db_type="{{db_type}}"
    replica_number="{{replica_number}}"

    if [[ "$service_name" == "redis" ]]; then
        container_name="unipi-gatchaandgames-redis"
        echo "Showing logs for Redis at $container_name..."
        docker logs -f $container_name
    elif [[ "$service_name" == "cdn" ]]; then
        container_name="unipi-gatchaandgames-cdn"
        echo "Showing logs for CDN..."
        docker logs -f $container_name
    elif [[ "$service_name" == "gwprivate" ]]; then
        container_name="unipi-gatchaandgames-api_gateway_private"
        echo "Showing logs for private api gateway..."
        docker logs -f $container_name
    elif [[ "$service_name" == "gwpublic" ]]; then
        container_name="unipi-gatchaandgames-api_gateway_public"
        echo "Showing logs for public api gateway..."
        docker logs -f $container_name
    elif [[ " $allowed_services " =~ (^|[[:space:]])"$service_name"($|[[:space:]]) ]]; then
        if [ -z "$db_type" ]; then
            container_name="unipi-gatchaandgames-service_${service_name}-${replica_number}"
        elif [[ " $allowed_db_types " =~ (^|[[:space:]])"$db_type"($|[[:space:]]) ]]; then
            container_name="unipi-gatchaandgames-service_${service_name}_db_${db_type}"
        else
            echo "Invalid database type. Allowed types are: $allowed_db_types"
            exit 1
        fi
        echo "Showing logs for $container_name..."
        docker logs -f $container_name
    else
        echo "Invalid service name. Must be one of: $allowed_services or 'redis'."
        exit 1
    fi


log service_name db_type='primary':
    #!/bin/bash
    allowed_services="{{allowed_services}}"
    allowed_db_types="{{allowed_db_types}}"
    service_name="{{service_name}}"
    db_type="{{db_type}}"

    if [[ " $allowed_services " =~ (^|[[:space:]])"$service_name"($|[[:space:]]) ]] && \
       [[ " $allowed_db_types " =~ (^|[[:space:]])"$db_type"($|[[:space:]]) ]]; then
        container_name="unipi-gatchaandgames-service_${service_name}_db_${db_type}"
        echo "Showing logs for $container_name..."
        docker logs -f $container_name
    else
        echo "Invalid service name or database type. Allowed services: $allowed_services, Allowed DB types: $allowed_db_types"
        exit 1
    fi
