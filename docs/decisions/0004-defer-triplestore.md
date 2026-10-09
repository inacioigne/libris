# ADR 0004 — Adiar triplestore dedicado

Status: aceito para a estrutura inicial

Data: 2026-10-09

## Contexto

RDF é obrigatório, mas não existem consultas SPARQL e volume medidos que exijam outro banco.

## Decisão

Prototipar persistência semântica em PostgreSQL e ferramentas RDF antes de escolher triplestore.

## Consequências

Reduz serviços locais; PostgreSQL não passa a oferecer SPARQL. Reavaliar por travessias/federação, desempenho e custo operacional medidos.
