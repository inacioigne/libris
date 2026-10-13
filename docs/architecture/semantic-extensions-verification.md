# Verificação — extensibilidade semântica (#25)

Data: 2026-10-12. Estado inicial: `main`, HEAD
`180f45aeddd06b469cca2394ffb0203fbaf8fd32`, workspace limpo.
Issue #25 lida integralmente; consultadas #15, #16, #17, #18, #20, #21, #22 e #24.

## Entregas e compatibilidade

| Entrega | Arquivos | Decisão e justificativa |
| --- | --- | --- |
| Governança de namespace/classe/propriedade | domain/profile_registry.py | Metadados aditivos; autorização distinta de reconhecimento; identidade canônica protegida |
| Registro imutável e associação por perfil | infrastructure/profiles.py; semantics-v2.json; semantic-release-lock.json; semantic-profile-releases.json | Reutiliza registries; mantém os perfis históricos em 1.0; descendentes herdam associação |
| Perfil candidato misto | work-extensions-2.0.0.json; release-lock.json | Herda Work/core; resumo opcional com idiomas e cardinalidade; fingerprint novo sem mudar antigos |
| Contrato estrutural e geração | semantics-1.1.schema.json; scripts/generate_profile_artifacts.py | Novo schema, sem sobrescrever schema semântico histórico; gerador reconhece associações novas |
| Interoperabilidade | fixtures/extensions/work.ttl e work.jsonld | Mesmo grafo com BIBFRAME/DCTERMS/PROV; auxiliares, idioma e data tipada |
| Testes | tests/api/test_semantic_extensions.py | Casos positivos/negativos e revisão real do serviço com repositório simulado |
| Arquitetura e governança | semantic-extensions.md; ADR 0025; README.md | Inventário inicial, API, frontend futuro, versionamento, migração e mapeamentos sem inferência |

Componentes reutilizados: SemanticRegistry/NamespaceDefinition/ClassDefinition/
PropertyDefinition; ProfileRegistry/ProfileDefinition/ResolvedProfile;
ShapeRegistry; validate_profile/validate_resolved_profile;
add_profile_constraints; parse_representation/serialize_graph; ownership;
prepare_document/BibliographicService; contratos de valores e diagnósticos.

Preservados: semantics-v1.json, contexto bibframe-v1.jsonld, shapes e perfis
históricos, schemas públicos Create/Read/Update, locks de dependências,
identidade de recursos, banco e fronteiras transacionais. Nenhuma dependência,
endpoint, alteração Next.js, tabela ou migração acrescentada.

## Comandos e resultados

Da pasta `apps/api`, ferramentas do ambiente `.venv`:

- `.venv/bin/pytest -q`, fora do sandbox: **979 aprovados, zero falhas**,
  385 avisos de depreciação RDFLib/Starlette, em 119,95 segundos. Suíte completa
  executada após as alterações finais de código; nenhuma regressão restante.

- `.venv/bin/pytest ../../tests/api/test_semantic_extensions.py -q`:
  **54 aprovados**, 16 avisos RDFLib de depreciação de ConjunctiveGraph.
- Testes de extensão/perfis históricos em execução intermediária:
  **163 aprovados** (47 de extensão e 116 declarativos, antes de acrescentar
  sete casos de governança e manifesto).
- `.venv/bin/ruff check . ../../tests`: aprovado.
- `.venv/bin/mypy src`: aprovado; 66 arquivos fonte.
- `UV_CACHE_DIR=/tmp/libris-uv-cache uv run --locked ruff check . ../../tests` e
  `uv run --locked mypy src`: aprovados fora do sandbox, com o uv via Snap.
- `.venv/bin/python ../../scripts/generate_profile_artifacts.py --check`:
  aprovado; 10 artefatos conferidos. O comando sem `--check` também foi executado
  para gerar o schema 1.1; os artefatos históricos não mudaram.
- `docker compose --env-file .env.example config --quiet`: aprovado.
- `git diff --check`: aprovado.
- `git branch --show-current`, `git status --short`, `git rev-parse HEAD` e
  `git diff --stat`: executados no início/fim; branch e HEAD preservados.

A execução inicial específica detectou três erros dos novos testes (IRI de
termo desconhecido construída com DefinedNamespace, controle textarea usado
para um datatype numérico e comparação de compatibilidade entre famílias
históricas diferentes). Corrigidos os testes para exercitar os contratos reais.
A suíte histórica detectou perda da associação semântica na transição de estado;
correção aplicada também a add_release/replace_draft. Testes de lifecycle,
herança e cópias destacadas cobrem a regressão. Mypy detectou inferência inadequada
de união de contratos; corrigida com tipos explícitos, sem Any. O padrão inicial
de nome do manifesto não admitia pontos em releases; ajustado, mantendo caminhos
com barras rejeitados. Uma invocação Ruff a partir da raiz aplicou regras diferentes
das declaradas em apps/api/pyproject.toml e reportou 46 problemas; a verificação
obrigatória foi repetida a partir de apps/api e passou, sem modificar arquivos
alheios à entrega.

`bash scripts/check.sh` foi tentado e falhou no início pelo confinamento de Snap
(`snap-confine`/AppArmor). A tentativa inicial `uv run` falhou pelo mesmo motivo.
A suíte completa dentro do sandbox ficou sem progresso no primeiro teste FastAPI
TestClient após 35 testes; interrompida e repetida fora do sandbox com aprovação
automática. Não é contabilizada como sucesso. Shell no sandbox emitiu mensagens
`Failed to create stream fd: Operation not permitted`.

`npm run build` e `npm run typecheck` foram tentados e retornaram comando não
encontrado. A inspeção fora do sandbox também não encontrou npm/node. Sem mudança
web, não foram instaladas ferramentas ou dependências só para esta verificação.

Não foram executados testes PostgreSQL: não houve alteração transacional ou de
persistência; o teste de revisão usa o serviço com repositório simulado e não
pretende comprovar integração com banco real. SQLite não foi usado.

## Critérios e limites

Os dez critérios funcionais/arquiteturais da issue #25 estão tecnicamente
atendidos pelas evidências; build/typecheck web permanecem verificações
indisponíveis no ambiente. A matriz dos dez critérios da issue está em
[semantic-extensions.md](semantic-extensions.md#matriz-dos-critérios-de-aceitação).
O contrato de extensão e o exemplo DCTERMS são executáveis. Homologação
institucional, ingestão HTTP, edição de extensões nos DTOs/Next.js e adoção dos
perfis 2.0 pelo serviço transacional são trabalhos futuros documentados;
a issue #25 não exige criar essas superfícies. Mapeamentos permanecem
especificações revisadas, conforme o escopo, sem motor de inferência.

Nenhuma branch criada/trocada, staging, commit, push, PR, merge, rebase ou reset.
A issue não foi alterada. Todos os arquivos ficam no workspace para revisão.
