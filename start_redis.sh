#!/bin/bash

set -e

if [ ! -f .env ]; then
    echo ".env no encontrado"
    exit 1
fi

set -a
source .env
set +a

echo "Levantando Redis en puerto ${REDIS_PORT}..."

docker compose up -d

echo "Redis inicializado correctamente."