#!/bin/bash

set -e

ELASTICSEARCH_URL="http://localhost:9200"

INDEX_NAME="works"

echo "=========================================="
echo " Elasticsearch - Reset do índice"
echo "=========================================="

echo
echo "Verificando conexão com Elasticsearch..."

curl -fsS "$ELASTICSEARCH_URL" > /dev/null

echo "Elasticsearch disponível."

echo
echo "Removendo índice '$INDEX_NAME'..."

curl -fsS -X DELETE \
    "$ELASTICSEARCH_URL/$INDEX_NAME" \
    -H "Content-Type: application/json" \
    || true

echo "Índice removido."

echo
echo "Criando índice '$INDEX_NAME'..."

curl -fsS -X PUT \
    "$ELASTICSEARCH_URL/$INDEX_NAME" \
    -H "Content-Type: application/json" \
    -d '{
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text"
                },
                "type": {
                    "type": "keyword"
                }
            }
        }
    }'

echo
echo
echo "Índice '$INDEX_NAME' recriado com sucesso."

echo
echo "Verificando índice..."

curl -fsS \
    "$ELASTICSEARCH_URL/$INDEX_NAME"

echo
echo
echo "=========================================="
echo " Processo concluído!"
echo "=========================================="
