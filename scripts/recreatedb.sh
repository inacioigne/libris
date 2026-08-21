#!/bin/bash

set -e

CONTAINER="mariadb"
DATABASE="libris_db"
MARIADB_ROOT_PASSWORD="RizctJ7"

echo "⚠️  ATENÇÃO: o banco '$DATABASE' será completamente apagado."
read -p "Digite 'SIM' para continuar: " CONFIRM

if [ "$CONFIRM" != "SIM" ]; then
    echo "Operação cancelada."
    exit 0
fi

echo "Removendo banco '$DATABASE'..."

docker exec mariadb mariadb \
    -u root \
    -pRizctJ7 \
    -e "DROP DATABASE IF EXISTS \`$DATABASE\`;"

echo "Criando banco '$DATABASE'..."

docker exec "$CONTAINER" mariadb \
    -u root \
    -pRizctJ7 \
    -e "CREATE DATABASE \`$DATABASE\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "Banco '$DATABASE' recriado com sucesso."