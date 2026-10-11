# ADR 0017 — Contratos JSON tipados de edição catalográfica

Status: aceito para implementação técnica da M03.01.02; homologação institucional pendente

Data: 2026-10-11

## Contexto

Os perfis candidatos locais e os ADRs 0009–0015 já definem propriedades,
cardinalidades, identidade e propriedade de snapshots. Não há endpoints de
catálogo. As issues de relacionamentos, identificadores e serialização permanecem
abertas. A API precisa de DTOs sem criar outra fonte bibliográfica canônica.

## Decisão

Implementar Create/Read/Update em bibliographic/api/schemas, com nomes snake_case,
auxiliares estruturados e referências exclusivamente por URI. Read acrescenta
somente UUID e URI armazenada. Não embutir autoridades/entidades relacionadas,
aceitar inversas graváveis ou expor automaticamente metadados técnicos.

Create/Read representam propriedades opcionais multivaloradas com listas vazias,
sem null. Update preserva campos omitidos, null explícito e listas; null remove
somente propriedades opcionais, e listas substituem integralmente a propriedade.
Auxiliares são substituídos completos. Identidade e tipo de agente são imutáveis.
Validar o estado completo após aplicar o PATCH será obrigação da aplicação.

Os DTOs representam os campos dos perfis locais. Graph/SHACL continuam canônicos.
Não criar representação genérica de extensões antes da M03.01.05. Campos extras
são rejeitados, e a edição futura deverá preservar propriedades RDF fora da
superfície tipada. Ver [documentação](../architecture/catalogographic-schemas.md).

## Alternativas e consequências

JSON-LD como único body dependeria da M03.01.05; dicionários arbitrários perderiam
tipagem; repetir classes no domínio ou acoplar ORM duplicaria responsabilidades.
Usar DTOs explícitos permite OpenAPI/clientes e testes sem serviços. O contrato
não oferece exportação RDF lossless, UUID-only em relações, validação referencial,
CAS HTTP ou CRUD persistente. Esses pontos exigem as entregas correspondentes.
Não há novas tabelas, dependências, infraestrutura ou alteração de releases.
