# Verificação — M03.03.01 / issue #24

Data: 2026-10-12. Trabalho local, sem commit, push, PR, merge ou mudança de issues.

## A. Diagnóstico inicial

Branch main; HEAD `b26aa48b9f55d4d3b3b71d968d47b076fb76fbaf`; working tree sem
alterações versionadas no início. `.env` local existente preservado integralmente.
As issues [#23](https://github.com/inacioigne/libris/issues/23),
[#24](https://github.com/inacioigne/libris/issues/24) e
[#25](https://github.com/inacioigne/libris/issues/25) foram lidas pelo conector GitHub.
AGENTS.md, README, arquitetura, ADRs relacionados e implementações #15–#22 foram
examinados antes das alterações.

Reutilizados: IRIs sem normalização/rede; ResourceIdentity/ResourceURI;
ResourceReference/EntityReference; LocalizedText/unique_languages/disjoint_labels;
ReferenceValue.vocabulary e DeclarativeField.check_value; registro/resolução de
perfis 2.0; validação SHACL e suplemento; Diagnostic/CatalogCode; mapeador de
referências e serializadores/parser restrito com isomorfismo.

Já atendidos parcialmente: formato URI, idiomas, referências de entidades,
configuração de vocabulário e serialização segura. Lacunas efetivas: quatro valores
operacionais discriminados, metadados de conceito, estados/evidência de resolução,
provedores por URI, preservação de transcrição, cache e pertença verificável.

## B. Implementação e arquivos

Os caminhos de código abaixo são relativos a
`apps/api/src/libris/modules/bibliographic/`.

| Arquivo criado/modificado | Responsabilidade |
| --- | --- |
| application/controlled_values.py (novo) | Envelope 1.0, quatro variantes, coerência e projeção URI-only explícita |
| api/schemas/controlled_values.py (novo) | Reexportação pública sem endpoints |
| application/vocabulary_resolution.py (novo) | Protocolo async, proveniência, respostas definitivas/transitórias, enriquecimento separado e política de cache |
| domain/vocabularies.py (novo) | Evidência por release, membros exatos e conjuntos completos/parciais |
| application/vocabulary_validation.py (novo) | Compatibilidade com campos/perfis, enums/pertença/estados e Diagnostic existentes |
| domain/errors.py (modificado) | Cinco códigos aditivos, sem novo formato de erro |
| infrastructure/serialization/controlled_values.py (novo) | Valores → RDF e descrição SKOS local separada |
| infrastructure/serialization/mapping.py (modificado) | Extração de reference_to_uri, conservando lógica do mapeador histórico |
| resources/controlled-values-v1/*.schema.json (quatro novos) | Schemas do valor, enriquecimento/resolução, política de cache e registry |
| scripts/generate_controlled_value_artifacts.py (novo, raiz) | Geração/check de oito artefatos novos; RDF comparado por isomorfismo |
| tests/api/test_controlled_vocabularies.py (novo, raiz) | 61 testes determinísticos, inclusive exemplos/OpenAPI isolado e compatibilidade |
| docs/examples/controlled-vocabularies/* (seis novos, raiz) | JSON operacional, JSON-LD e Turtle locais/externos |
| docs/architecture/controlled-vocabularies.md (novo, raiz) | Especificação, política, fronteiras, exemplos e limites |
| docs/decisions/0024-controlled-vocabularies.md (novo, raiz) | Decisões estruturais aditivas e alternativas |
| README.md (modificado) | Referência à entrega |
| Este documento (novo) | Evidências, checklist e limites de revisão |

## C. Decisões

[ADR 0024](../decisions/0024-controlled-vocabularies.md): extensão aditiva sem
substituir contratos existentes; identidade por URI e label localizado; literais
lexicais sem coerção; evidência separada do original; pertença por URI com evidência
selecionada; cache contratual; RDF local próprio e link externo sem enriquecimento.

Preferenciais mantêm um valor por idioma, reutilizando a validação de UniqueTexts.
A lista vazia permite uso URI-only não verificado. Rótulos alternativos podem ter
mesmo idioma, mas não pares duplicados/interseção com preferenciais. Casos
resolved/invalid/deprecated exigem fonte, sem afirmar confiança pela mera string.
Permanente da consulta não equivale automaticamente a invalid do conceito.

## D. Testes e ambiente

Comandos executados em apps/api, com `.venv/bin/` substituindo uv:

```bash
APP_ENV=test DATABASE_URL=postgresql+asyncpg://libris:test@localhost:5432/libris \
  .venv/bin/pytest ../../tests/api/test_controlled_vocabularies.py -q
.venv/bin/ruff check . ../../tests ../../scripts/generate_controlled_value_artifacts.py
.venv/bin/mypy src
APP_ENV=test DATABASE_URL=postgresql+asyncpg://libris:test@localhost:5432/libris \
  .venv/bin/python ../../scripts/generate_controlled_value_artifacts.py --check
.venv/bin/python ../../scripts/generate_profile_artifacts.py --check
APP_ENV=test DATABASE_URL=postgresql+asyncpg://libris:test@localhost:5432/libris \
  .venv/bin/python ../../scripts/generate_diagnostic_examples.py --check
```

- Suíte nova: **61 passed**, 20 avisos de depreciação RDFLib, 11,18s.
- Suíte integral: **921 passed**, 369 avisos de depreciação FastAPI/Starlette e
  RDFLib, 89,66s, fora do sandbox. Comando: `APP_ENV=test
  DATABASE_URL=postgresql+asyncpg://libris:test@localhost:5432/libris
  .venv/bin/pytest ../../tests/api -q`. Essa coleta incluía 57 testes novos; os
  quatro testes adicionais finais estão incluídos na execução isolada de 61.
  São 925 testes distintos aprovados nas duas execuções, sem somar duplicatas.
- Ruff: aprovado, incluindo scripts novos.
- Mypy: aprovado, 66 arquivos de fonte, sem Any ou ignores introduzidos.
- Artefatos novos: oito verificados; artefatos de perfis históricos: dez verificados.
- Exemplos de diagnósticos existentes: verificador executado com exit code 0.
- `git diff --check`: aprovado.
- `docker compose --env-file .env.example config --quiet`: aprovado.

Na raiz, `bash scripts/check.sh` foi executado e interrompido na primeira chamada
uv: Snap/snap-confine recusa execução pelo estado de confinamento/AppArmor.
`uv --version` também falhou pelo mesmo motivo; não foi reinstalado.
O `.venv` existente usa Python 3.13. Há entradas malformadas no `.env` local:
execução inicial do gerador falhou na configuração; execuções posteriores usaram
APP_ENV e DATABASE_URL de teste explícitos, sem conexão com banco e sem editar `.env`.
Avisos python-dotenv permanecem somente no ambiente local.

A execução integral da API dentro do sandbox travou após 35 testes em um teste
preexistente de autenticação (`TestClient.__enter__`, portal AnyIO entre threads).
Faulthandler documentou o bloqueio; execução interrompida e repetida fora do sandbox.
Não se atribuiu o bloqueio à implementação nem se declarou essa execução aprovada.

`npm run build` e `npm run typecheck` foram tentados e falharam porque npm não está
instalado/disponível no PATH (exit 127). Nenhum frontend foi modificado.
PostgreSQL/Elasticsearch e testes de integração persistente não foram executados;
a alteração não acrescenta infraestrutura/persistência.

## E. Critérios de aceitação

| Critério #24 / pedido | Situação | Evidência |
| --- | --- | --- |
| Schema Pydantic documentado | Atendido | CatalogValueDocument, quatro schemas e gerador/check |
| Literais, conceitos e entidades inequívocos | Atendido | CatalogValue discriminado, rejeição de extras/ambiguidade nos testes |
| URI como identidade principal | Atendido | validate_iri, ResourceURI, URIRef e testes de preservação |
| Rótulos multilíngues/alternativos/notation | Atendido | LocalizedText, coerência por idioma e exemplos JSON/SKOS |
| Conceitos locais/externos semanticamente compatíveis | Atendido | Base ConceptValue e identidade institucional armazenada |
| Resolução/obsolescência explícitas | Atendido | Cinco status, source, replacement e testes de estados |
| Indisponibilidade sem invalidação automática | Atendido | EnrichedConcept preserva cataloged/previous_success, teste de outage |
| Política de atualização e cache | Atendido | ResolutionCachePolicy, fresh/usable_stale e explicit_revision |
| Reutilização por catalogação/autoridades | Atendido | Application sem HTTP e reexportação API; entidades via contrato existente |
| JSON, JSON-LD e RDF preservam identidade | Atendido | Exemplos executáveis, link URIRef e round-trip isomórfico |
| Testes válidos/inválidos/obsoletos/não resolvidos | Atendido | Suíte nova com fixtures locais/provedores determinísticos |
| Integração com perfis | Atendido | Campo de ResolvedProfile, enum/check_value e evidência de membership |
| Fronteira SHACL corretamente delimitada | Atendido | Teste nodeKind/perfil; pertença suplementar declarada como aplicação |
| Componentes existentes reutilizados | Atendido | Inventário A e refatoração mínima reference_to_uri |
| Contratos/releases históricos preservados | Atendido | DTOs/fixtures/releases/contextos/locks intactos, checks históricos |
| Arquitetura/documentação atualizadas | Atendido | Especificação, ADR 0024, README e este relatório |

Não há critério funcional #24 parcialmente atendido ou pendente no escopo pedido.
A verificação global de frontend está limitada pelo ambiente; não é entrega desta
issue. A homologação institucional e integrações futuras não são simuladas como
implementadas.

## F. Compatibilidade

Work/Instance/Item/Agent/Subject, ResourceReference e EntityReference conservam
schemas e representações; payload URI-only continua aceito. Conceitos ricos não
passam a ser aceitos nos campos históricos silenciosamente. as_reference é
projeção explícita, com redução de metadados documentada.

Releases, shapes, contexto bibframe-v1, fixtures e release-lock não foram
modificados. Catálogo persistente não adota automaticamente novos perfis/políticas.
CatalogCode recebe valores novos aditivos conforme ADR 0023. Não há nova tabela,
fonte semântica paralela ou regra de rede para aceitar um registro.

#25 pode reutilizar ReferenceValue.vocabulary, IRI e a separação dos registries,
sem ampliar arbitrariamente a superfície de SemanticRegistry. A exportação integral
de Graph permanece existente. Registro de namespaces/ontologias adicionais,
governança abrangente e mapeamentos novos de DTO pertencem à #25; #23 não está completa.

## G. Pendências institucionais e futuras

Escolher fontes confiáveis, releases e política de publicação dos vocabulários,
domínio institucional, retenção/proveniência e homologar TTLs. Conectores reais,
cache persistente, armazenamento de evidência/revisões de autoridades, API/editor,
reconciliação e implementação #25 pertencem às entregas futuras. Nenhuma destas
pendências foi transformada em funcionalidade fictícia nesta tarefa.

A issue #24 está **tecnicamente pronta para revisão e eventual fechamento**,
considerando o escopo contratual solicitado e os limites de ferramentas registrados.
O fechamento permanece decisão do mantenedor; nenhuma issue foi alterada.
