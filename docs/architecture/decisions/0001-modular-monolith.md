# ADR 0001 — Monólito modular como arquitetura inicial

- **Status:** Proposto — pendente de aprovação
- **Data:** 2026-10-22
- **Escopo:** Backend, fronteiras de domínio e implantação

## Contexto

O Libris pretende oferecer catalogação, autoridades, circulação, aquisições, periódicos, descoberta e administração. A implementação atual contém uma aplicação FastAPI mínima e contratos iniciais de títulos BIBFRAME. Não existe evidência de necessidade operacional de microsserviços neste estágio.

## Decisão proposta

Adotar **monólito modular** no backend FastAPI, com implantação inicial como uma única aplicação e fronteiras explícitas entre domínios. Organizar código por capacidades, e não apenas por camadas técnicas globais.

Módulos previstos: `catalog`, `authorities`, `holdings`, `circulation`, `acquisitions`, `serials`, `discovery` e `identity`. Os nomes são ilustrativos, não exigem criação imediata. O frontend Next.js consumirá APIs públicas versionadas e não acessará bancos diretamente.

Cada módulo deverá possuir seus contratos, casos de uso e interfaces de persistência. Dependências entre módulos devem passar por interfaces públicas ou eventos de domínio; evitar importações de modelos internos de outros módulos, ciclos e acesso direto às tabelas alheias. Infraestrutura compartilhada deve permanecer pequena e não concentrar regras de negócio.

A separação bibliográfico/operacional é obrigatória: circulação referencia identificadores de exemplares, mas não define o significado de `bf:Work`, `bf:Instance` ou `bf:Item`.

## Alternativas consideradas

1. **Microsserviços desde o início:** isolamento de implantação, porém maior custo de rede, observabilidade, consistência e operação; rejeitado para o estágio atual.
2. **Monólito sem limites internos:** simples inicialmente, mas facilita acoplamento entre regras bibliográficas e administrativas; rejeitado.
3. **Monólito modular:** menor custo inicial e possibilidade de extração posterior; recomendado.

## Consequências

**Positivas:** testes e depuração mais simples, transações locais, menor sobrecarga de infraestrutura e evolução incremental.

**Riscos:** acoplamento progressivo e gargalos de implantação se as fronteiras não forem respeitadas. Mitigar com testes de arquitetura, interfaces explícitas, revisões de dependências e métricas.

## Critérios de adoção

- API HTTP isolada dos casos de uso e do domínio.
- Testes de regras bibliográficas sem subir FastAPI ou banco.
- Sem dependências circulares entre módulos.
- Alterações em circulação não exigem modificar os contratos semânticos de Work/Instance.
- Estrutura documentada no `docs/architecture/overview.md` após aprovação.

## Pontos ainda em aberto

Estratégia de autenticação/autorização, limites multi-instituição, implantação e eventual extração de serviços exigem decisões futuras.

## Relações

Complementa `0002-bibliographic-model.md` e `0003-persistence-strategy.md`. Não afirma que os módulos previstos já existem.
