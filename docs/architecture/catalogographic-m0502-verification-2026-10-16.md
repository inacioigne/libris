# Verificação M05.02 / issue #46 — 2026-10-16

## Estado inicial e escopo

Branch `main`; HEAD inicial `2038d49edbe596d3ebd7ecc3a1da772c2c219aad` (M05.01).
Foram executados, antes de editar: `git branch --show-current`, `git status --short`,
`git log -10 --oneline`, `git rev-parse HEAD`, `git diff --check`.
Staging inicialmente vazio. Alterações preexistentes preservadas:

- `apps/web/src/server/admin/shell.tsx`: duas classes Tailwind de quebra de palavras.
- `infrastructure/docker/web.Dockerfile`: cópia do diretório public para a imagem.

Issue #46 e dependências #15/#16/#18/#20/#25/#31 consultadas pelo conector GitHub,
somente em leitura. #46 aberta, milestone 5 (M05). Nenhum recurso remoto alterado.
Código, perfis, fixtures, contratos e ADRs pertinentes orientaram o escopo interno.
Não há novos endpoints, migrações, persistência alternativa ou alteração dos DTOs.

## Diagnóstico e decisões

`resource_to_graph` já cobria a superfície normativa dos cinco Read, com blank
nodes, idiomas, PublicationDate, papéis e resolução fornecida. Não havia leitura
inversa completa ou transformação parcial de snapshot. `BibliographicService.revise`
recebe Graph completo, reusa perfil/URI persistidos e mantém CAS, revisão, estado
editorial e auditoria na mesma transação. Não foi necessário alterar sua assinatura.

O contrato v1 define null como remoção apenas para propriedades opcionais.
Obrigatórios não aceitam null/lista vazia; omissão preserva. Projeção Read não é
snapshot integral. Referências reconstruídas usam URI-only, sem inferir UUID/localidade.
Metadados discriminados de reconciliação não são recuperáveis do RDF existente.

Create reaproveita o writer Read, com identidade fornecida e validação por perfil.
PATCH utiliza `exclude_unset=True`, revalida estado completo e copia o Graph
original. Remove apenas os predicados selecionados e auxiliares órfãos cuja descrição
foi integralmente reconhecida. Conteúdo compartilhado é preservado; anotação não
representável em auxiliar exclusivo impede a substituição. Registro/perfil autorizam
novas escritas; preservação de histórico não autoriza novas propriedades arbitrárias.

Estas são implementações dos ADRs existentes, sem nova fronteira arquitetural,
framework ou contrato público incompatível. Não houve alteração de release, contexto,
shape, fixture histórica, dependência/lock ou script de qualidade.

## Arquivos da entrega

| Arquivo | Responsabilidade |
| --- | --- |
| `infrastructure/serialization/mapping.py` (sob o módulo bibliográfico) | Writer reutilizado; valida evidência resolvida de tipo/subtipo e alias de identidade |
| `infrastructure/serialization/projection.py` | Graph → Read explícito e determinístico; rastreia triplas consumidas/fronteiras por campo |
| `infrastructure/serialization/adapters.py` | Create + identidade, PATCH em cópia, autorização e validação final |
| `infrastructure/serialization/__init__.py` | Exporta funções e uniões tipadas internas |
| `tests/api/test_dto_rdf_adapters.py` | 43 casos offline, incluindo matriz de campos e regressões |
| `docs/architecture/catalogographic-dto-rdf-adapters.md` | Interfaces, mapeamento, algoritmo, exemplo de serviço e limites |
| `docs/architecture/catalogographic-contract.md` | Atualiza a lacuna de adaptação resolvida |
| `docs/architecture/semantic-serialization.md` | Liga evolução M05.02 ao writer existente |
| `docs/architecture/catalogographic-http.md` | Atualiza estado interno de #46, mantendo CRUD futuro |
| Este relatório | Evidência nova; relatórios históricos preservados |

## Cobertura dos cinco tipos

| Entidade | Create → Graph | Graph → Read | Update parcial | Cobertura de conteúdo |
| --- | --- | --- | --- | --- |
| Work | Sim | Sim | Sim | 9 campos, títulos/variantes, contribuições/papéis, classificação, relações e notas |
| Instance | Sim | Sim | Sim | 8 campos, Work, publicação agrupada, datas tipadas, identificadores, extensão e notas |
| Item | Sim | Sim | Sim | 7 campos, Instance, Local, detentor, custódia, marca de estante e proveniência |
| Agent | Sim | Sim | Sim | 7 campos; kind Create/Read imutável no Update; Agent/Person/Organization |
| Subject | Sim | Sim | Sim | 7 campos; rótulos, esquema, hierarquia/associação, fontes e referências |

UUID/URI são recebidos do chamador confiável. Agent/Subject não se confundem com
identidade autenticada. Item não implementa disponibilidade/circulação.

## Evidências semânticas

- `test_complete_roundtrips`: cada entidade passa por Create → Graph → Read → Graph,
  repetição Read e serialização JSON-LD/Turtle/expandida, com isomorfismo RDF.
- `test_each_public_field_is_replaced_independently` e
  `test_null_empty_and_omitted_fields`: percorrem cada campo Update dos cinco tipos,
  verificando substituição, remoção autorizada e integridade dos demais campos.
- `test_languages_lexical_dates_and_grouping`: múltiplos idiomas, ausência de idioma,
  gYear `0024`, date e data transcrita xsd:string; sem coerção de datas/identificadores.
- `test_extensions_and_historical_unknown_auxiliaries_survive`: dcterms:abstract
  pt-BR, auxiliar prov:Entity e literal xsd:string preservados; extensão histórica
  permanece em edição independente também sob perfil legado. Exportação integral
  isomorfa em ambos os formatos; Read explicitamente menor que o snapshot.
- `test_private_fragment_auxiliary_and_shared_nodes`: IRI privada compartilhada
  preservada com seu conteúdo quando o título é substituído.
- `test_annotated_auxiliary_replacement_rejected_without_mutation`: edição que
  apagaria anotação falha; grafo original fica intacto.
- Casos de referência verificam UUID-only resolvido, pares inconsistentes, tipo
  incompatível, Organization em held_by, autorreferência e não reconciliadas.
- Casos negativos cobrem cardinalidade, datatype, classe auxiliar, descrição alheia,
  Update de outro tipo, identidade/extras, objeto mutado e conflito de rótulos.
- `test_combined_state_validation_and_shacl_failure_are_atomic`: SHACL bloqueia
  extensão com violação sem modificar o original.
- `test_legacy_persistence_preparation_keeps_complete_patch`: `prepare_document`
  conserva o snapshot completo em JSON-LD expandido aceito pelo caminho existente.
- `test_explicit_string_datatype_is_a_projection_limit`: demonstra a limitação da
  projeção sem afirmar round-trip integral; PATCH independente preserva a tripla exata.

## Execução e resultados

Python 3.13 do `.venv` existente; Node **24.16.0** do NVM, sem instalação de dependências.
Os comandos `uv run pytest ../../tests/api -q`,
`uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py`,
`uv run mypy src` e `bash scripts/check.sh` foram tentados no sandbox: o wrapper
Snap de uv falhou com `snap-confine ... is not confined but should be`.
A suíte API iniciada diretamente pelo `.venv` no sandbox foi interrompida com
SIGINT após parar em TestClient/AnyIO; não foi contada como aprovação.

O frontend confinado apresentou `listen EPERM 127.0.0.1` no teste HTTP local
(70/71 casos do arquivo auth passaram quando diagnosticado sem isolamento) e
falha do subprocesso TypeScript no build. A execução fora do sandbox, autorizada
pelo ambiente, resolveu esses impedimentos sem modificar código de produto.
Nesse ambiente o próprio uv/Snap também executou o `check.sh` original.

| Verificação | Resultado |
| --- | --- |
| `uv run pytest ../../tests/api -q`, fora do sandbox, código final | **1.738 passed**, zero falhas/skips, 512 warnings, 171,73 s |
| `.venv/bin/python -m pytest ../../tests/api/test_dto_rdf_adapters.py -q` | **43 passed**, 35 warnings RDFLib; zero falhas |
| `.venv/bin/ruff check . ../../tests ../../scripts/verify-m04-integration.py`; depois o mesmo comando com `uv run` fora do sandbox | **All checks passed** |
| `.venv/bin/python -m mypy src`; depois `uv run mypy src` fora do sandbox | **Success**, 90 arquivos |
| `bash scripts/check.sh`, original, fora do sandbox | **Exit 0**: 1.734 testes API, lint/mypy, 167 testes web, build, typecheck e Compose estático aprovados |
| Node 24: `npm test`, fora do sandbox | **167 passed**, zero falhas/skips |
| Node 24: `npm run build`, fora do sandbox | Aprovado, Next.js 16.4.0 |
| Node 24: `npm run typecheck`, fora do sandbox | Aprovado |
| Integração PostgreSQL selecionada, `.venv/bin/python -m pytest` | **50 skipped** por ausência de TEST_DATABASE_URL; nenhuma integração física comprovada |

A seleção de integração abrangeu `test_semantic_postgres.py`,
`test_entity_revisions_postgres.py`, `test_audit_postgres.py`,
`test_editorial_postgres.py` e `test_diagnostic_transactions_postgres.py`.
Nenhuma base foi configurada, migrada ou modificada. Os skips já pertencem aos
contratos de teste existentes; não foram introduzidos skips nesta entrega.

O check completo coletou 39 casos de adaptadores; os quatro casos acrescentados
na revisão final foram incluídos nos 43 casos da execução específica final. A
reexecução integral final pelo comando exato solicitado coletou e aprovou os
**1.738 casos**, incluindo os 43 novos. Nenhuma alteração de código ocorreu depois
dessa execução final.

Durante o desenvolvimento, falhas de caminho de fixture, ordem variável de auxiliares
e entrada de data fora da forma lexical contratual foram corrigidas. A ordenação
Read passou a depender do conteúdo, sem identidade artificial para blank nodes.
A revisão acrescentou rejeição de rdf:langString sem tag de idioma, que RDFLib
permite construir sem marcar como ill_typed. Lint e tipagem também foram corrigidos
e reexecutados. Warnings finais de JSON-LD são a depreciação de ConjunctiveGraph na biblioteca, sem perda silenciosa aceita.

## Limites e próxima entrega

O Read não conserva extensões, IRIs/compartilhamento de auxiliares, classes extras,
discriminadores de referências ou a distinção sintática literal simples/xsd:string
em campos textuais. PublicationDate conserva seu datatype explícito. RDF é conjunto:
sem ordem e sem duplicatas idênticas de termos; auxiliares distintos são preservados.
Projeção de RDF válido mas incompatível com os invariantes v1 é recusada. Um PATCH
que necessite apagar extensão de auxiliar exclusivo é recusado conservadoramente.
Não há edição genérica de ontologias ou migração automática de snapshots históricos.

#47 precisa carregar identidade/revisão/perfil confiáveis, aplicar If-Match,
resolver referências pelos contratos existentes e passar o Graph completo a revise.
CAS permanece árbitro final de concorrência. Perfis 2.0 continuam fora da persistência
legada; esta entrega apenas permite validação interna com ResolvedProfile confiável.
Existência/ciclo de vida de alvos, fecho transitivo de ciclos e atomicidade física
PostgreSQL não são comprovados pelos mappers ou por SHACL isolado.

Homologação institucional, PostgreSQL/OIDC reais e integração HTTP não são anunciados.
Nenhum endpoint M05.03–M05.06 foi antecipado.


## Critérios de aceite da #46

| Critério | Evidência / resultado |
| --- | --- |
| Cinco Create e Graph → Read funcionais | Matriz parametrizada das cinco entidades; todos os campos normativos e auxiliares |
| Reversibilidade normativa | Isomorfismo do corpus gerado pelo writer e repetição de Read determinística |
| Identidade estável, referências, idiomas/datatypes | Testes de identidade, resolução, tipos/subtipos, múltiplos idiomas e datas lexicais |
| PATCH preserva omissão/extensões | Matriz campo a campo e casos com extensão na raiz, prov:Entity, IRI privada e auxiliar compartilhado |
| null/lista vazia conforme v1 | Percurso de todos os campos Update e rejeições obrigatórias |
| Falha sem mutação/escrita parcial | Entradas inválidas, anotações exclusivas, conflito entre rótulos e SHACL; funções sem persistência |
| Propriedades autorizadas por release | Registros fixados, perfil mínimo rejeitando campo não editável e extras rejeitados pelo DTO |
| JSON-LD/Turtle/fixtures v1 | Corpus existente e suíte completa; artefatos históricos intactos |
| Uma fonte canônica, sem quebra versionada | Graph/JSONB existentes; nenhum DTO, contexto, shape, lock ou esquema alterado |
| Serviço/revisão/CAS preservados | Nenhuma assinatura transacional alterada; grafo completo compatível com prepare_document |
| Testes/tipagem/lint documentados | Resultados acima; PostgreSQL real explicitamente não verificado |
| Git preservado | Conferência final abaixo |

## Estado Git final

Branch `main`; HEAD `2038d49edbe596d3ebd7ecc3a1da772c2c219aad`, idêntico ao inicial.
Sem branch nova, checkout, commit, PR, push, staging ou alteração de configuração Git.
`git diff --check` sem erros e `git diff --cached --quiet` com exit 0.
Arquivos novos foram revisados separadamente; não aparecem no diff dos rastreados.
O `next-env.d.ts` regenerado pelo build foi restaurado ao conteúdo inicial, sem
interferir nos dois arquivos previamente modificados. A preservação destes foi
conferida contra HEAD mais as alterações iniciais exatas, não apenas pelo status.
Alterações desta entrega ficam somente no workspace para revisão humana.
