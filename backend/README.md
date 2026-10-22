# Libris API

## Ambiente local

Ative o ambiente virtual e inicie a API a partir desta pasta:

```bash
source .venv/bin/activate
fastapi dev app/main.py
```

A documentação interativa fica disponível em `http://127.0.0.1:8000/docs` e o
health check em `http://127.0.0.1:8000/health`.

Para executar os testes da API:

```bash
python -m pytest tests/api
```
