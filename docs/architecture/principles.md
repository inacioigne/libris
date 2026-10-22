# Princípios arquiteturais — Libris

**Status:** diretrizes propostas para orientar o desenvolvimento; decisões específicas devem ser registradas em ADRs.  
**Escopo:** backend, frontend, dados bibliográficos, integrações e infraestrutura.  
**Última revisão:** 2026-10-22.

## 1. Propósito e fontes de referência

O Libris é um Sistema Integrado de Gestão de Bibliotecas (ILS) de código aberto, modular e orientado à Web Semântica e a Dados Abertos Conectados. Sua visão contempla catalogação, autoridades, circulação, aquisições, periódicos, usuários, relatórios e estatísticas. BIBFRAME é o modelo bibliográfico principal, com extensibilidade para outras ontologias e vocabulários.

As tecnologias-alvo definidas na visão do projeto são **FastAPI/Python**, **Next.js/React** e **Elasticsearch**. A adoção de PostgreSQL e de um repositório RDF dedicado é uma proposta arquitetural a ser confirmada, não uma implementação comprovada.

Este documento traduz essa visão em princípios verificáveis. Para comportamentos efetivos, consultar o código, os testes, os perfis SHACL e `docs/api/openapi.yaml`. Divergências entre propostas e implementação devem ser registradas, não ocultadas.

## 2. Princípios fundamentais

### P01 — Modularidade por domínio

- Organizar componentes segundo capacidades bibliotecárias: catalogação, autoridades, circulação, aquisições, periódicos e descoberta.
- Definir responsabilidades e interfaces explícitas entre módulos.
- Evitar dependências circulares e acesso direto a detalhes internos de outros domínios.
- **Critério de revisão:** uma mudança em um domínio não deve exigir alterações injustificadas em vários outros.

A opção por **monólito modular** está indicada no nome do ADR `0001-modular-monolith.md`, mas sua aprovação e seus limites devem ser documentados antes de tratá-la como decisão definitiva.

### P02 — Modelo bibliográfico orientado a entidades

- Tratar **BIBFRAME Work, Instance e Item** como conceitos distintos.
- Representar agentes, assuntos, instituições e relações bibliográficas por identificadores e vínculos explícitos.
- Não confundir uma obra intelectual, uma publicação específica e um exemplar.
- **Critério de revisão:** as operações preservam identidade e relações entre entidades.

### P03 — Interoperabilidade semântica por padrão

- Usar BIBFRAME como vocabulário bibliográfico principal, sem impedir extensões justificadas.
- Planejar interoperabilidade com MARC 21, RDA, SKOS, Schema.org e fontes de autoridades externas quando aplicável.
- Preservar IRIs e a semântica dos predicados nas transformações RDF/JSON-LD.
- **Critério de revisão:** conversões não descartam silenciosamente propriedades desconhecidas ou não suportadas.

### P04 — Contratos explícitos e versionados

- Definir contratos de API, esquemas de validação e perfis de metadados de maneira verificável.
- Considerar `docs/api/openapi.yaml`, modelos Pydantic e shapes SHACL como artefatos de contrato, observando seu status e eventuais divergências.
- Documentar alterações incompatíveis, migrações e versionamento.
- **Critério de revisão:** mudanças de comportamento vêm acompanhadas de testes e atualização dos contratos afetados.

### P05 — Validação na fronteira e integridade dos dados

- Validar entradas de API e dados bibliográficos antes de persistir ou publicar.
- Aplicar regras de domínio, cardinalidade e perfis SHACL apropriados.
- Retornar erros explicativos; não normalizar ou corrigir dados de maneira silenciosa quando isso alterar seu significado.
- **Critério de revisão:** entradas inválidas têm resultados previsíveis e cobertos por testes.

### P06 — Separação entre dados bibliográficos e operações

- Manter a descrição semântica de obras e instâncias desacoplada das regras de empréstimo, reservas, multas e disponibilidade.
- Relacionar registros operacionais a entidades bibliográficas por identificadores estáveis.
- **Critério de revisão:** políticas de circulação não alteram a identidade ou o significado de uma Work ou Instance.

### P07 — Persistência e busca com responsabilidades claras

- Distinguir armazenamento transacional, representação semântica e índices de descoberta.
- Tratar Elasticsearch como mecanismo de busca e facetas, não automaticamente como fonte canônica dos dados.
- Definir sincronização, reindexação, consistência e recuperação antes de introduzir novos armazenamentos.
- **Critério de revisão:** cada dado possui fonte de verdade documentada e estratégia de atualização dos índices.

**Nota:** a escolha concreta de PostgreSQL, RDF Store e sincronização depende do ADR `0003-persistence-strategy.md`.

### P08 — APIs e componentes com responsabilidades limitadas

- Manter rotas HTTP focadas em transporte, autenticação, validação e tradução de erros.
- Isolar regras bibliotecárias e conversões semânticas em componentes testáveis.
- No frontend, separar apresentação, estado da interface e integração com APIs.
- **Critério de revisão:** lógica de negócio relevante pode ser testada sem inicializar toda a aplicação.

### P09 — Segurança, privacidade e auditabilidade

- Aplicar menor privilégio, autenticação e autorização adequadas a cada operação.
- Proteger credenciais, dados pessoais de leitores e histórico de circulação.
- Prever rastreabilidade de alterações em registros e proveniência de metadados.
- Não registrar segredos ou informações pessoais desnecessárias em logs.
- **Critério de revisão:** operações sensíveis têm controle de acesso e trilha de auditoria proporcionais ao risco.

### P10 — Qualidade, acessibilidade e evolução incremental

- Preferir implementações pequenas, testáveis e compatíveis com os contratos existentes.
- Priorizar fluxos de catalogação e interoperabilidade antes de recursos avançados de automação e IA.
- Construir interfaces acessíveis e compreensíveis para bibliotecários e usuários do catálogo.
- Medir desempenho com cenários representativos antes de otimizar.
- **Critério de revisão:** toda funcionalidade relevante tem critérios de aceite e evidências de validação.

## 3. Regras para agentes de IA

Antes de alterar o código, os agentes devem:

1. Ler `AGENTS.md` e as instruções específicas da área, quando existirem.
2. Inspecionar implementação, testes, contratos e documentação relacionados à tarefa.
3. Distinguir **implementado**, **aprovado** e **proposto**; nunca inferir que uma funcionalidade existe apenas porque aparece na visão do produto.
4. Preservar compatibilidade semântica e rejeitar perda de dados não autorizada.
5. Propor um ADR quando a alteração introduzir uma decisão estrutural, dependência estratégica ou mudança de fonte de verdade.
6. Implementar a menor mudança coerente, criar testes e executar as verificações disponíveis.
7. Relatar os testes efetivamente executados, limitações e impactos de compatibilidade; nunca declarar sucesso sem evidência.

## 4. Decisões que exigem ADR

Registrar contexto, alternativas, decisão, consequências e status em `docs/architecture/decisions/` para:

- Estilo de implantação e fronteiras de módulos (`0001-modular-monolith.md`).
- Representação canônica, identidade e extensões do modelo bibliográfico (`0002-bibliographic-model.md`).
- Persistência transacional, RDF, indexação e consistência (`0003-persistence-strategy.md`).
- Mudanças incompatíveis em contratos públicos, autenticação ou integração entre serviços.

Um arquivo ADR vazio ou apenas nomeado **não** comprova que a decisão foi tomada.

## 5. Hierarquia prática de referências

1. Requisitos explícitos e decisões aprovadas do projeto.
2. Contratos versionados e testes aplicáveis à funcionalidade.
3. Implementação existente, para determinar o comportamento real.
4. Documentação arquitetural e de domínio, respeitando seu status.
5. Propostas futuras, tratadas como hipóteses até aprovação.

Quando essas fontes entrarem em conflito, **não resolver silenciosamente**: registrar a divergência e solicitar decisão antes de alterar comportamento público ou dados persistidos.

## 6. Referências internas

- `docs/product/vision.md` — visão e escopo do produto.
- `docs/architecture/overview.md` — visão geral da arquitetura.
- `docs/architecture/decisions/` — registros de decisões arquiteturais.
- `docs/domain/bibliographic.md` — regras do domínio bibliográfico.
- `docs/api/openapi.yaml` — contrato proposto da API.
- `backend/app/catalog/shared/title/` — implementação atual de modelos e RDF para títulos.
- `backend/tests/` — testes e exemplos existentes.

> Este documento orienta o desenvolvimento; não substitui decisões arquiteturais aprovadas nem constitui evidência de que todos os componentes descritos já foram implementados.
