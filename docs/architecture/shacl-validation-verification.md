# Verificação e relatório técnico — #21

Data: 2026-10-12. Branch: `feat/21-shacl-validation`.
Issue original lida no GitHub, atualizada em 2026-10-12, sem comentários na consulta.
Interfaces #14–#20 conferidas com issues e contratos/código locais.

## Resumo executivo

Consolidado o validador existente: resolução única de artefatos, meta-SHACL local,
falhas específicas, termos RDF completos no diagnóstico e correlação sem colisões.
Políticas declarativas 2.0 que não tinham equivalente nas fontes recebem constraints
suplementares determinísticas, no mesmo pySHACL, conforme ADR 0022.
Nenhum arquivo publicado, modelo de persistência, dependência ou endpoint mudou.

## Diagnóstico inicial e matriz de requisitos

| Requisito da issue | Estado inicial | Lacuna / tratamento / evidência final |
| --- | --- | --- |
| Inventário e contrato técnico | Parcialmente implementado | Fontes/documentos existentes; inventário completo em shacl-inventory.md e contrato em shacl-validation.md |
| Work, Instance, Item e auxiliares | Implementado | Reutilizadas shapes 1.1, inclusive títulos não variantes, Local qualificado e publicação; testes parametrizados novos |
| Agent, Person, Organization e SKOS Concept | Implementado | authority-v1.ttl, corpus de autoridades; ampliados tipos, labels e ausência de scheme |
| Opcionais, datatypes e idiomas | Parcialmente implementado | Regras básicas existentes; políticas adicionais 2.0 não executadas; suplemento e testes de idiomas/enum/datatype |
| Snapshot/composed, URI não descrita | Implementado | Preservados ownership/compose_snapshots e alternativas sem tipo; novas fixtures de URI local/externa |
| Raiz/vazio e responsabilidade transacional | Implementado | prepare_document/check_snapshot separados de SHACL; teste de conformidade vazia e escrita rejeitada |
| Associação por release/contexto | Parcialmente implementado | Dois mapas de infraestrutura independentes; PROFILE_SHAPES agora derivado de SHAPE_RELEASE_FILES via aliases |
| Correspondência policy/shapes | Não implementado integralmente | ADR 0021 atribuía complementação à #21; rejeição de contradições e constraints de especializações |
| Revisões históricas e imutabilidade | Implementado | Hashes legados, release-lock da #20, previous.profile em revise; sem migração |
| Severidades e relatório RDF | Implementado | allow_warnings/allow_infos já existentes; novos testes de cada severidade e combinações/preparação |
| Diagnóstico sourceShape/component/value e identidade de termos | Parcialmente implementado | Só quatro campos string antes; ampliado ValidationIssue, preservada construção legada |
| Correlação com formulário | Parcialmente implementado | Comparação textual podia misturar blank node e IRI; agora usa termo exato; caminhos complexos continuam explícitos sem campo |
| Falhas locais/internas distinguíveis | Parcialmente implementado | Exceptions sem classificação e retorno não-Graph genérico; ProfileError e ShaclValidationError com code |
| Segurança local e isolamento | Implementado na base, evidência parcial | Flags preservadas e ampliadas explicitamente; testes de rede, shapes injetadas, imutabilidade e cache |
| Cache/desempenho | Não implementado, nem necessário antes de meta-SHACL | Necessidade medida na verificação adicional; cache imutável limitado, benchmark e teste de reutilização |
| Contrato HTTP definitivo | Dependente de outra issue (#22) | Contrato interno preparado; nenhum DTO HTTP/endpoint antecipado |
| Vocabulários/ontologias/homologação | Dependente de #24/#25 e avaliação humana | Extensibilidade aberta preservada; não comprova autoridade externa nem pertinência remota |

Problemas foram registrados antes das correções nas atualizações da execução e
consolidados nesta matriz. A diferença Item.identifiedBy (descritor exclui Isbn,
shape admite Isbn adicional) foi conservada/documentada, sem corrigir regra histórica.

## Arquivos e justificativas

| Arquivo / grupo | Alteração |
| --- | --- |
| infrastructure/validation.py | Aliases derivados, leitura restrita, cache de termos, meta-SHACL, códigos de erro e diagnóstico exato |
| infrastructure/validation_policy.py | Suplemento das políticas 2.0 não cobertas; core gera zero constraints adicionais (832 triplas antes/depois, isomorfismo) |
| tests/api/test_shacl_validation.py | Entidades, auxiliares, severidades, falhas, configuração, idioma, diagnóstico, segurança, isolamento e serviço sem banco |
| tests/fixtures/bibliographic/institutional/ | Quatro fixtures novas e manifest explícito; dez válidas e quatorze inválidas anteriores preservadas |
| tests/integration/test_semantic_postgres.py | Caso de Violation mantendo raiz e verificação de release após rollback; exige PostgreSQL dedicado |
| shacl-inventory.md / shacl-validation.md | Inventário integral e especificação com exemplos Turtle/JSON-LD |
| ADR 0022 / catalog-profiles.md / README.md | Justificativa da tradução limitada e links de integração |

## Regras e compatibilidade

As cinco entidades e as constraints originais estão organizadas por entidade na
[especificação](shacl-validation.md) e por cada shape no [inventário](shacl-inventory.md).
Work exige título não variante; Instance uma Work; Item uma Instance e Local;
Agent labels e Subject prefLabel/inScheme. As cardinalidades são institucionais.
Títulos de Instance/ISBN são opcionais; não há checksum nem título copiado.

Suplemento 2.0 traduz apenas min/max, nodeKind, datatype, texto, idiomas e enum/destinos
simples novos. Não duplica constraints existentes, não implementa consultas remotas,
não aplica default/presentation e não redefine classes históricas. Configurações
contraditórias produzem erro explícito. Core preserva integralmente o conjunto local.
Os testes de hashes dos JSON/TTL históricos e schemas/release-lock continuam ativos.
O serviço mantém a release originalmente armazenada; não adota v2 implicitamente.

## Testes e evidências de execução

Python do ambiente: 3.13.15, `.venv` existente em apps/api; dependências sem alterações.
Comandos abaixo usam `.venv/bin` porque uv/Snap não executou no sandbox.

| Diretório | Comando | Resultado |
| --- | --- | --- |
| apps/api, antes de editar | `.venv/bin/pytest ../../tests/api/test_catalogographic_contract.py ../../tests/api/test_declarative_profiles.py -q` | 176 aprovados, 264 avisos, 32,37 s |
| apps/api, primeira regressão ampliada | testes SHACL + dois contratos | 229 aprovados, 1 falhou na fixture nova: blank node criado não era o produzido pelo parser; corrigido sem mudar resultado esperado |
| apps/api, testes específicos após correções | `.venv/bin/pytest ../../tests/api/test_shacl_validation.py -q` | 64 aprovados, 28,26 s antes da última ampliação de regressão |
| apps/api, suíte completa intermediária | `.venv/bin/pytest -q` | 784 aprovados, 347 avisos, 67,59 s; fora do sandbox para TestClient/threads |
| apps/api, suíte final | `.venv/bin/pytest -q` | **788 aprovados, 0 reprovados**, 349 avisos, 54,99 s; inclui 67 casos do novo arquivo SHACL |
| apps/api | `.venv/bin/ruff check . ../../tests` | Sem erros após correção de lint/imports |
| apps/api | `.venv/bin/mypy src` | Sem erros em 53 arquivos após correção de tipos; não usa Any para contornar tipagem |
| apps/api | `.venv/bin/python ../../scripts/generate_profile_artifacts.py --check` | 10 artefatos verificados |
| apps/api | `.venv/bin/pytest -c pyproject.toml ../../tests/integration -q` | 5 ignorados: TEST_DATABASE_URL ausente; nenhum banco existente acessado |
| raiz | `bash scripts/check.sh` | Interrompido pelo uv/Snap (snap-confine/AppArmor); partes executadas separadamente |
| apps/web | `npm run build`, PATH com Node NVM 24.16.0 | Aprovado fora do sandbox; build restrito antes falhou em saída TypeScript --showConfig |
| apps/web | `npm run typecheck`, mesmo PATH | Aprovado |
| raiz | `docker compose --env-file .env.example config --quiet` | Aprovado; apenas validação de configuração, sem comprovar saúde de serviços |
| raiz | `git diff --check` | Sem erro de whitespace |

A tentativa completa restrita ficou sem progresso nos testes com threads e foi
interrompida; não contabilizada como aprovação. Rodadas intermediárias anteriores
à introdução do cache foram interrompidas para evitar meta-validação redundante.
Primeiro teste PostgreSQL executado isoladamente foi skipped com aviso de marker
por falta de `-c`; a coleta explícita final acima usa a configuração correta.
Não confundir testes com doubles com prova de rollback físico PostgreSQL.

Medição local de validação institucional simples: cache frio 3,103 s; quente 0,040 s.
Parsing: 2 misses/2 hits; meta-verificação: 1 miss/1 hit. Cada chamada relê fontes e
reconstrói Graph privado. Essa medição demonstra o benefício do cache neste exemplo,
sem estabelecer SLA/benchmark de produção.

## Decisões arquiteturais

ADR 0022 registra a única decisão nova: suplemento limitado para políticas que as
fontes locais não expressam. Mantidos monólito modular, domínio sem FastAPI/RDFLib,
pySHACL único, PostgreSQL fonte de verdade e Elasticsearch fora da validação.
Rejeitadas substituição de motor, geração total do núcleo e reescrita de releases.
Cache conserva conteúdo imutável e é limitado; Graph jamais é compartilhado.

## Limitações e pendências

Não foi executada integração física PostgreSQL: falta banco de testes dedicado.
Os cinco testes foram coletados e ignorados, sem SQLite nem acesso destrutivo.
A #20 fornece configuração/resolução; publicação administrativa e escrita v2 ficam
para integração futura. #22 define contratos HTTP; #24 pertença a vocabulários e
reconciliação; #25 novos componentes/ontologias; #30 corpus e medidas adicionais.
Deadline/quotas de CPU de endpoint futuro não estão implementados. Aprovação técnica
não substitui homologação catalográfica, prova de identidade externa ou equivalência.

## Avaliação de todos os critérios de aceitação originais

| Critério original (ordem da issue) | Avaliação | Evidência |
| --- | --- | --- |
| 1. Especificação e associação explícita a perfis versionados | Atendido | shacl-validation.md; inventário; SHAPE_RELEASE_FILES |
| 2. Reuso do validador existente sem motor paralelo | Atendido | _validate_shapes e mesmo pyshacl.validate |
| 3. Conjuntos identificáveis, executáveis e compatíveis | Atendido | aliases derivados; hashes legados; core sem suplemento redundante |
| 4. Cobertura Work/Instance/Item/Agent/Subject | Atendido | corpus e test_entities_and_auxiliaries |
| 5. Separação estrutural/semântica/referencial/operacional | Atendido | matriz de responsabilidades; prepare_document/ownership/service preservados |
| 6. Modos snapshot/composed explícitos e coerentes | Atendido | ProfileValidationContext; testes de composição/inversas |
| 7. URI sem descrição não confundida com inexistência | Atendido | duas fixtures novas, teste de referência/sem rede |
| 8. Violation/Warning/Info documentados e testados | Atendido | testes isolados/mistos e preparação não bloqueante |
| 9. Diagnóstico localizável/preparado para #22 | Atendido | termos exatos, shape/component/value; testes de colisão e inversePath |
| 10. Sem download ou regra não confiável | Atendido | registro fechado e flags; socket bloqueado e dados SHACL injetados sem efeito |
| 11. Fixtures positivas/negativas/limites e ontologias extras | Atendido | corpus de 28 cenários e casos parametrizados |
| 12. Testes/documentação com decisões, limites e evidências | Atendido com limite de execução | verificações acima; integração PostgreSQL preparada, mas ignorada; não comprovada fisicamente nesta sessão |
| 13. Sem migração/endpoints/armazenamento/indexação novos | Atendido | diff; nenhum JSON/TTL histórico alterado, sem dependências ou migrações |

A aprovação final e homologação continuam humanas. A issue não foi fechada nem
houve merge automático. Descrição do PR preparada para revisão e referenciando #21.
