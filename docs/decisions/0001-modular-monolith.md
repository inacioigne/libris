# ADR 0001 — Monólito modular

Status: aceito para a estrutura inicial

Data: 2026-10-09

## Contexto

O ILS possui muitos domínios, mas ainda não possui carga ou equipes que justifiquem distribuição.

## Decisão

Manter um backend FastAPI com módulos de negócio e contratos explícitos. Separar frontend e infraestrutura por processos.

## Consequências

Simplifica desenvolvimento e transações. Exige disciplina de fronteiras; extração futura depende de evidência. Microsserviços e Kubernetes ficam descartados nesta etapa.
