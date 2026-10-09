# ADR 0014 — Evolução dos perfis catalográficos

Status: aceito para implementação técnica do Incremento 1; aprovação institucional pendente

Data: 2026-10-09

## Contexto

O perfil v1 experimental está referenciado por revisões existentes. Substituir seus arquivos mudaria a validação histórica. JSON declarativo e SHACL têm responsabilidades distintas.

## Decisão

Preservar monograph-v1.json/ttl e seu identificador. Adicionar monograph-v1.1, urn:libris:profile:monograph:v1:1, como candidato institucional, e authority-v1. Cada release identifica artefatos locais imutáveis; mudanças posteriores exigem outro release/ID. JSON Schema local descreve os formulários, Pydantic verifica estrutura/invariantes e SHACL verifica RDF. Título de Instance é opcional; Item exige identificador bf:Local; Work exige título não variante.

## Alternativas consideradas

Sobrescrever v1 é simples, mas invalida rastreabilidade. Criar uma nova família desconectada dificultaria continuidade. Fechar todo o grafo com sh:closed bloquearia extensões; mantemos shapes abertas, com restrições explícitas nas propriedades conhecidas.

## Consequências

Campos opcionais ausentes omitem triplas. Não preencher strings vazias ou autoridades fictícias. Cardinalidades são escolhas institucionais, não limites universais de BIBFRAME. Papéis e agentes são obrigatórios quando uma contribuição é declarada. ISBN é opcional e valor transcrito não vazio; checksum/reconciliação não são implementados. Serviço conserva profile por revisão e rejeita troca implícita. Adoção/catalogação institucional depende de revisão humana dos exemplos; implementação técnica autorizada não significa homologação institucional.

## Estado e evidências

As diretrizes foram revisadas e autorizadas pelo solicitante após o diagnóstico
(Momentos A/B). A homologação institucional dos perfis e das regras catalográficas
continua pendente. A aprovação técnica não define domínio público nem aprova
vocabulários institucionais. Ver [contrato](../architecture/catalogographic-contract.md),
[diagnóstico](../architecture/catalogographic-contract-diagnosis.md) e
[verificação](../architecture/catalogographic-contract-verification.md).
