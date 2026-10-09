# ADR 0006 — Ambiente local e dependências reproduzíveis

Status: aceito para a estrutura inicial

Data: 2026-10-09

## Contexto

É necessário executar a base com ferramentas estáveis e sem infraestrutura de produção prematura.

## Decisão

Python 3.13 como referência (suporte 3.13–3.14), Node.js 24 LTS, uv/npm com locks, Docker Compose com quatro serviços.

## Consequências

Locks precisam de manutenção. Imagens locais não são configuração de produção; major tags recebem patches. Licença do código e termos de distribuição Elasticsearch exigem avaliação antes de distribuir o produto.
