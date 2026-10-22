# Visão do produto — Libris

> **Status:** visão e direcionamento do produto. Este documento descreve objetivos e capacidades pretendidas, não uma declaração de funcionalidades já implementadas.

## 1. Visão

O **Libris** é um projeto de **Sistema Integrado de Gestão de Bibliotecas (ILS)** de código aberto, moderno, modular e de nível corporativo. Seu propósito é integrar as operações bibliotecárias a tecnologias de **Web Semântica** e **Dados Abertos Conectados (Linked Open Data)**, facilitando a organização, descrição, conexão e descoberta de acervos físicos e digitais.

O diferencial central do Libris é a adoção **nativa do BIBFRAME** como modelo principal de descrição bibliográfica, com suporte à utilização de outras ontologias e vocabulários para representar obras, autores, instituições, assuntos e demais entidades de forma estruturada, extensível e interoperável.

## 2. Problema e oportunidade

Sistemas bibliotecários precisam atender simultaneamente a processos operacionais — como catalogação, circulação e aquisições — e a expectativas de descoberta, interoperabilidade e reutilização de metadados. O Libris busca unir a robustez funcional de um ILS tradicional a uma arquitetura bibliográfica orientada a entidades e relacionamentos.

A oportunidade é permitir que usuários não apenas encontrem registros isolados, mas naveguem por conexões entre obras, edições, agentes, instituições e assuntos, preservando fluxos de trabalho acessíveis aos profissionais de biblioteca.

## 3. Objetivos do produto

1. Oferecer gestão integrada de acervos físicos e digitais.
2. Disponibilizar módulos de catalogação, circulação, autoridades, aquisições, periódicos, usuários, relatórios e estatísticas.
3. Adotar BIBFRAME como modelo bibliográfico principal, com interoperabilidade semântica e extensibilidade por ontologias e vocabulários.
4. Promover descoberta moderna, intuitiva e acessível, incluindo navegação por entidades relacionadas.
5. Facilitar integração com fontes externas de conhecimento e ecossistemas de dados bibliográficos.
6. Estabelecer uma base tecnológica sustentável para futuras capacidades de automação e inteligência artificial.

## 4. Públicos e necessidades

| Público | Necessidade principal |
| --- | --- |
| Bibliotecários e catalogadores | Descrever recursos, controlar autoridades e aplicar regras bibliográficas com consistência. |
| Equipes de circulação e gestão | Administrar usuários, empréstimos, reservas, acervos e processos operacionais. |
| Leitores e pesquisadores | Encontrar recursos, explorar relações bibliográficas e verificar disponibilidade. |
| Administradores e instituições | Configurar políticas, acompanhar operações, obter relatórios e integrar sistemas. |
| Desenvolvedores e integradores | Utilizar interfaces e dados interoperáveis com contratos documentados. |

Esses perfis orientam o desenho do produto; não representam funcionalidades já entregues.

## 5. Escopo funcional pretendido

### 5.1 Núcleo bibliográfico e catalogação

- Descrição de obras, instâncias e exemplares, preservando suas diferenças conceituais.
- Edição de metadados orientada a entidades e relacionamentos BIBFRAME.
- Suporte a outras ontologias, vocabulários e perfis de catalogação.
- Importação e interoperabilidade com formatos bibliográficos existentes, a serem detalhadas em requisitos e contratos específicos.

### 5.2 Autoridades

- Gestão e reutilização de entidades de pessoas, instituições e assuntos.
- Associação consistente de identificadores e relacionamentos entre entidades.
- Possibilidade de integração e reconciliação com fontes externas, conforme evolução do projeto.

### 5.3 Operações bibliotecárias

- Circulação, usuários, empréstimos e reservas.
- Aquisições e gestão de periódicos.
- Relatórios, estatísticas e funções administrativas.

### 5.4 Catálogo público e descoberta

- Busca e navegação intuitivas por recursos e entidades.
- Descoberta de relações entre obras, autores, assuntos, edições e instituições.
- Experiência contemporânea, visualmente clara e acessível.

## 6. Princípios orientadores

**Semântica desde a origem.** A representação bibliográfica deve preservar identidades e relações, não apenas campos textuais isolados.

**Interoperabilidade.** Dados e integrações devem favorecer padrões abertos e reutilização por outros sistemas.

**Modularidade.** As capacidades funcionais devem ter limites e responsabilidades claros, evitando acoplamento desnecessário.

**Usabilidade bibliotecária.** A complexidade do modelo semântico não deve ser transferida integralmente ao catalogador; interfaces devem apoiar tarefas reais de trabalho.

**Acessibilidade e descoberta.** A experiência pública deve ser simples para leitores e suficientemente rica para pesquisadores e profissionais.

**Qualidade e rastreabilidade.** Validação, consistência e evolução controlada de contratos e metadados são requisitos de projeto.

**Evolução incremental.** Funcionalidades devem ser priorizadas em entregas verificáveis, sem confundir intenção, protótipo e produção.

## 7. Direção tecnológica

A arquitetura tecnológica definida como objetivo utiliza:

- **Backend:** Python e FastAPI.
- **Frontend:** Next.js e React.
- **Busca e descoberta:** Elasticsearch.
- **Modelo bibliográfico:** BIBFRAME, com RDF e tecnologias de Linked Data.

O uso de PostgreSQL para dados operacionais e de um armazenamento RDF dedicado é uma **proposta arquitetural** presente nas referências do projeto; sua adoção e desenho definitivo dependem de decisões técnicas documentadas. O mesmo vale para estratégias específicas de persistência, implantação e integração.

## 8. Referências de produto e experiência

As referências abaixo orientam estudos, sem implicar reprodução integral de suas arquiteturas ou interfaces:

| Referência | Principal aprendizado pretendido |
| --- | --- |
| FOLIO | Modularidade e processos administrativos. |
| Koha | Abrangência e regras de negócio bibliotecárias. |
| Alma | Operações corporativas e fluxos de gestão. |
| MARVA e Sinopia | Catalogação BIBFRAME e formulários baseados em perfis. |
| Share-VDE | Descoberta por entidades e dados conectados. |
| VuFind e Primo NDE | Busca, facetas e experiência de descoberta. |

## 9. Evolução proposta

A seguinte sequência é uma **recomendação de planejamento**, sujeita a revisão e priorização:

1. **Fundação semântica:** modelo bibliográfico, identificadores, perfis, validação e contratos.
2. **Catalogação e autoridades:** criação e manutenção de entidades bibliográficas, relacionamentos e integrações essenciais.
3. **Catálogo público:** busca, descoberta, navegação por entidades e apresentação de recursos.
4. **Gestão bibliotecária ampliada:** circulação, aquisições, periódicos, usuários, relatórios e estatísticas.

Funcionalidades adicionais, como assistência de catalogação com IA, reconciliação automática e deduplicação semântica, são oportunidades futuras e não compromissos de entrega nesta visão.

## 10. Limites e decisões em aberto

Este documento **não** define cronograma, equipe, orçamento, indicadores quantitativos, política de licenciamento específica, modelo de implantação, requisitos não funcionais mensuráveis ou detalhes definitivos de persistência. Esses pontos exigem decisões próprias e não devem ser inferidos por agentes de IA.

Também não deve ser usado para afirmar que módulos descritos já estão implementados. Para verificar o estado real do produto, consulte o código, os testes, os contratos e o roadmap atualizado.

## 11. Relação com a documentação técnica

- `README.md`: apresentação geral e instruções de entrada no repositório.
- `AGENTS.md`: orientações de trabalho para agentes de IA.
- `docs/architecture/overview.md`: arquitetura efetiva e seus limites.
- `docs/architecture/decisions/`: decisões arquiteturais registradas.
- `docs/domain/bibliographic.md`: regras e entidades do domínio bibliográfico.
- `docs/api/openapi.yaml`: contrato proposto/documentado da API.
- `docs/product/roadmap.md`: priorização e situação das entregas, quando disponível.

Em caso de divergência, esta visão expressa a **intenção do produto**; o comportamento efetivamente implementado deve ser verificado nos contratos aplicáveis, no código e nos testes.

---

**Fontes de orientação:** *Objetivo do Projeto Libris* e *Referências de softwares e catálogos para o projeto Libris*. As seções de públicos, princípios, etapas e limites organizam e desenvolvem essas diretrizes, sem substituir decisões formais do projeto.
