# Libris

**Sistema Integrado de Gestão de Bibliotecas orientado a dados conectados**

O **Libris** é um projeto de software livre para desenvolver um Sistema Integrado de Gestão de Bibliotecas (*Integrated Library System*, ILS) moderno, modular e de nível corporativo. Seu objetivo é reunir as operações tradicionais de bibliotecas e as possibilidades da Web Semântica e dos Dados Abertos Conectados (*Linked Open Data*).

O principal diferencial proposto é a adoção nativa do **BIBFRAME** para descrição bibliográfica, com suporte à interoperabilidade com outras ontologias e vocabulários. O projeto busca facilitar a gestão de acervos físicos e digitais e a descoberta de obras, autores, instituições e assuntos por meio de entidades relacionadas.

> **Estado do projeto:** desenvolvimento inicial. A arquitetura e os módulos descritos como *planejados* são objetivos do projeto, não funcionalidades disponíveis na versão atual.

## Objetivos

- Construir um ILS de código aberto, modular e extensível.
- Integrar catalogação, circulação, autoridades, aquisições, periódicos, usuários, relatórios e estatísticas.
- Utilizar BIBFRAME como modelo bibliográfico principal e permitir integração com outras ontologias.
- Oferecer descoberta de acervos com pesquisa, navegação por entidades e relacionamentos semânticos.
- Favorecer interoperabilidade, acessibilidade, qualidade dos metadados e manutenção sustentável.

## Estado atual do repositório

Na estrutura examinada da branch `main`, encontram-se:

- Um backend inicial em **Python/FastAPI**, com endpoint de verificação de saúde.
- Modelos de títulos bibliográficos para **Work** e **Instance**, utilizando Pydantic.
- Transformações entre modelos de aplicação e representações **RDF/JSON-LD**, com RDFLib.
- Um perfil de validação **SHACL** para títulos.
- Testes de API e de contratos bibliográficos.
- Uma proposta de contrato de API em [`docs/api/openapi.yaml`](docs/api/openapi.yaml).

Ainda não há, nessa estrutura, uma implementação completa do ILS nem um frontend Next.js. Alguns documentos de arquitetura e domínio já possuem caminhos reservados, mas ainda precisam ser desenvolvidos.

## Arquitetura tecnológica

| Camada | Tecnologia | Situação |
| --- | --- | --- |
| API e regras de negócio | Python 3.12+, FastAPI, Pydantic | Base inicial presente |
| Metadados semânticos | BIBFRAME, RDFLib, JSON-LD, SHACL | Contratos iniciais presentes |
| Interface web | Next.js, React, TypeScript | Planejada |
| Busca e descoberta | Elasticsearch | Planejada |
| Dados operacionais | Estratégia de persistência a consolidar | Planejada |
| Armazenamento e consulta RDF | Estratégia a decidir | Em avaliação |

A arquitetura deve manter separadas as responsabilidades bibliográficas (obras, instâncias, autoridades e relacionamentos) e as operações administrativas (empréstimos, reservas, aquisições e outras rotinas).

### Modelo bibliográfico

O Libris adota como orientação as entidades BIBFRAME:

- **Work:** conteúdo intelectual ou artístico de uma obra.
- **Instance:** materialização ou publicação de uma obra.
- **Item:** exemplar individual associado a uma instância.

O código atual contempla contratos iniciais de títulos de Work e Instance. O suporte abrangente às entidades e seus relacionamentos será desenvolvido progressivamente.

## Módulos previstos

| Módulo | Escopo planejado |
| --- | --- |
| Catalogação | Descrição de recursos e perfis de metadados baseados em BIBFRAME |
| Autoridades | Controle e vinculação de pessoas, organizações e assuntos |
| Circulação | Empréstimos, devoluções, reservas e políticas de circulação |
| Aquisições | Gestão de solicitações e processos de aquisição |
| Periódicos | Controle de publicações seriadas |
| Usuários | Gestão de usuários e permissões |
| Descoberta | Catálogo público, busca, facetas e navegação por entidades |
| Relatórios e estatísticas | Indicadores e acompanhamento das operações bibliotecárias |

## Estrutura do repositório

```text
libris/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   └── catalog/shared/title/
│   │       ├── models.py
│   │       ├── rdf.py
│   │       └── shapes/title-v1.ttl
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
└── docs/
    ├── api/
    │   ├── conventions.md
    │   └── openapi.yaml
    ├── architecture/
    │   ├── overview.md
    │   ├── principles.md
    │   └── decisions/
    └── domain/
```

Esta árvore resume os diretórios relevantes existentes na branch examinada; não representa necessariamente todas as funcionalidades implementadas.

## Executando o backend localmente

**Pré-requisitos:** Python 3.12 ou superior e Git.

```bash
# Clonar o repositório
git clone https://github.com/inacioigne/libris.git
cd libris/backend

# Criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instalar o projeto e as dependências de teste
python -m pip install -e '.[test]'

# Iniciar o servidor de desenvolvimento
fastapi dev app/main.py
```

No Windows (PowerShell), a ativação do ambiente virtual é feita com `.venv\Scripts\Activate.ps1`.

Após iniciar o servidor:

- Documentação interativa da API: <http://127.0.0.1:8000/docs>
- Verificação de saúde: <http://127.0.0.1:8000/health>

### Testes

A partir da pasta `backend/`:

```bash
python -m pytest tests/api
python -m pytest tests/contracts
```

> **Nota:** os comandos acima refletem a organização pretendida dos testes. A execução integral da suíte de contratos ainda deve ser verificada, especialmente os caminhos de importação e de fixtures. Não se afirma aqui que todos os testes passaram.

## Documentação e contratos

- [`docs/api/openapi.yaml`](docs/api/openapi.yaml): proposta inicial do contrato HTTP.
- [`docs/architecture/`](docs/architecture/): arquitetura, princípios e registros de decisões arquiteturais (ADRs).
- [`docs/domain/`](docs/domain/): documentação das regras bibliográficas e operacionais.
- [`backend/README.md`](backend/README.md): instruções específicas do backend.

**Importante:** a documentação de visão descreve objetivos; os contratos, testes e código existente determinam o comportamento efetivamente implementado. Arquivos de documentação vazios não devem ser tratados como decisões aprovadas.

## Desenvolvimento com agentes de IA

O projeto pretende utilizar agentes de programação no VS Code, como Codex e GitHub Copilot. Recomenda-se centralizar as instruções compartilhadas em um arquivo `AGENTS.md` na raiz e adicionar instruções específicas por diretório conforme necessário.

Ao contribuir com ajuda de agentes:

1. Inspecione os arquivos e contratos relevantes antes de alterar o código.
2. Preserve as distinções semânticas entre Work, Instance e Item.
3. Evite transformações RDF/JSON-LD que descartem propriedades silenciosamente.
4. Inclua testes para alterações de comportamento.
5. Registre decisões arquiteturais significativas em ADRs.
6. Informe quais verificações foram realmente executadas.

## Referências de inspiração

O Libris toma como referências de estudo sistemas de gestão bibliotecária como **FOLIO**, **Koha** e **Alma**; ferramentas de descoberta como **VuFind**, **Share-VDE** e **Primo**; e ambientes de catalogação orientados a dados conectados como **MARVA** e **Sinopia**. Essas referências orientam o estudo de processos e experiências, sem implicar dependência técnica ou reprodução integral dessas plataformas.

## Como contribuir

Contribuições são bem-vindas por meio de [issues](https://github.com/inacioigne/libris/issues) e pull requests. Antes de propor uma alteração, consulte os contratos e documentos existentes, descreva o problema e o comportamento esperado e inclua testes quando aplicável.

## Licença

A definição da licença do projeto deve ser documentada em um arquivo `LICENSE` na raiz do repositório. Até que isso seja feito, não se deve presumir uma licença específica para reutilização do código.
