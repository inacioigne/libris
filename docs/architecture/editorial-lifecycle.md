# Estados e transições catalográficas — M03.04.01

Implementação de domínio e coordenação de aplicação da [issue #27](https://github.com/inacioigne/libris/issues/27),
no escopo da [issue #26](https://github.com/inacioigne/libris/issues/26).
Decisão: [ADR 0026](../decisions/0026-editorial-lifecycle.md).
Não há persistência editorial concreta, endpoint ou workflow operacional completo.

## Estados, matriz e autorização

Estado inicial: draft. `EditorialState` é StrEnum; estados desconhecidos e qualquer
aresta ausente (incluindo transições para si mesmo) produzem CatalogError com código
estável. archived é terminal. A máquina não representa BIBFRAME, inventário,
reconciliação ou ciclo de identidade.

| Origem | Destino | Operação | Permissão | Pré-condições adicionais |
| --- | --- | --- | --- | --- |
| draft | in_review | submit | editorial:submit | revisão corrente selecionada |
| in_review | approved | approve | editorial:approve | aprovação vinculada à revisão corrente |
| in_review | draft | return | editorial:return | justificativa; remove aprovação |
| approved | draft | return | editorial:return | justificativa; remove aprovação |
| approved | published | publish | editorial:publish | revisão aprovada exata; perfil/SHACL/referências válidos |
| published | withdrawn | withdraw | editorial:withdraw | justificativa; revisão pública selecionada |
| withdrawn | published | republish | editorial:republish | revisão anteriormente publicada; nova validação completa |
| withdrawn | archived | archive | editorial:archive | justificativa; revisão anteriormente publicada |

Todas exigem ator autenticado, instante com timezone, versão editorial esperada e
revisão corrente esperada. O serviço obtém instante UTC; o ator vem de IdentityService
ou dependência autenticada do servidor, nunca de um DTO enviado pelo cliente.
`authorize` é reutilizado e PermissionDenied adaptado para editorial.permission_denied.

| Papel | Capacidade editorial acrescentada |
| --- | --- |
| libris-reader | nenhuma |
| libris-cataloger | submeter |
| libris-authority-manager | nenhuma; combinar com papel editorial explícito |
| libris-reviewer | aprovar e devolver |
| libris-publisher | publicar, retirar, republicar e arquivar |
| libris-admin | todas, pelo mapeamento existente do enum completo |

Papéis acumulam capacidades; catalogador não publica por possuir bibliographic:update.
Permissões editoriais são comuns a bibliografia e autoridades, com alcance atribuído
explicitamente pelo provedor. Reviewer/publisher recebem leitura para examinar
conteúdo; não recebem edição. Não há proibição de uma pessoa acumular papéis.
Provisionamento desses papéis no OIDC é externo; o realm demonstrativo não foi alterado.

## Conteúdo corrente, aprovação e publicação

`EditorialRecord` reutiliza ResourceIdentity e contém:

- current_revision: último snapshot imutável.
- published_revision: snapshot publicado mais recentemente, conservado na retirada.
- editorial_state: ciclo do registro e visibilidade pública.
- version: inteiro positivo independente do número de revisão.
- approved_revision: revisão aprovada do ciclo em curso.
- candidate_state: ciclo de alterações pendentes, quando já existe publicação anterior.

`public_revision` devolve published_revision somente em published; withdrawn e
archived não disponibilizam conteúdo. Mudanças editoriais incrementam version e
não criam snapshots. Aprovação aponta para current_revision, sem revisão nova.
Tipos inconsistentes, ponteiros fora do histórico e aprovação obsoleta são rejeitados.

Exemplo verificável: conteúdo r1 aprovado/publicado; edição prepara r2 e candidata
draft, mantendo editorial_state=published e public_revision=1. Submissão e aprovação
com scope=candidate deixam r1 pública. Publicação da candidata r2 muda somente
published_revision para 2 e fecha candidate_state; r1 permanece imutável e recuperável.
A URI não muda. O ciclo candidato reutiliza apenas as arestas draft/in_review/approved
até sua publicação; não é uma segunda máquina genérica.

Nova edição só é aceita no ciclo draft. Conteúdo em revisão/aprovação exige
return antes de editar; devolução remove aprovação. Retirada suspende visibilidade e
preserva candidata e ponteiro público histórico. Republicação revalida r1 mesmo
quando current_revision=2; não publica automaticamente r2. Candidata só substitui
conteúdo quando o registro está published. Arquivamento encerra candidata, conserva
current_revision/published_revision e todos os snapshots. Edição de withdrawn ou
archived é recusada nesta política inicial.

`prepare_content_revision` exige a próxima Revision sequencial e identidade exata;
retorna metadados imutáveis para gravação junto do snapshot. **Não persiste conteúdo**.
BibliographicService ainda não chama essa política: adoção operacional requer o
adaptador e integração transacional futuros, sem duas gravações independentes.
A criação futura deve gravar snapshot r1 e EditorialRecord draft no mesmo commit.

## Validação de publicação

`PublicationContext` é um contrato interno obrigatório fornecido pela unidade
transacional: Revision exata, Graph completo, RelationshipCreate com referências
classificadas e ReferenceResolver. None bloqueia publicação. Não é entrada de cliente.

O coordenador verifica identidade/número, propriedade do snapshot por check_snapshot,
classe de raiz e aplicabilidade do perfil. Resolve release no registro local confiável
ou reutiliza descritor legado. Usa validate_catalog e os mesmos validadores SHACL,
incluindo políticas declarativas 2.0. Violation bloqueia; Warning/Info seguem a política
existente. Falha técnica não vira conformidade; o erro conserva o diagnóstico.

validate_references verifica existência, UUID/URI, tipo e regras dos vínculos;
pendências não reconciliadas são rejeitadas. A cobertura das relações RDF do registro
local é comparada à coleção classificada para impedir omissão de referências.
Classificação URI-only exige conhecimento explícito; prefixos não provam localidade.
Não se exige consultar fontes externas. Bibliografia e Agent/Person/Organization/
Subject usam seus perfis próprios, com diferenças SHACL preservadas.

O provedor deve fornecer classificação completa de todos os vínculos aplicáveis,
inclusive extensões governadas; extensão não suportada pelo adaptador de relações
exige evolução explícita desse contrato, sem alegar integridade automática. Ausência
de adaptador/classificação deve devolver None. O protótipo legado com múltiplas
entidades no mesmo grafo não é um snapshot proprietário: não é convertido nem
publicado implicitamente. Publicação não revalida todos os snapshots históricos.

Existência local observada não garante ausência global de ciclos nem estabilidade
até o commit. O adaptador futuro deverá verificar fechos transitivos quando exigidos
pelo contrato de relações e proteger versões/locks de dependências consultadas,
sem acesso a tabelas de outro módulo. Não há essa garantia física nesta entrega.

## Concorrência e persistência futura

O domínio verifica expectativas antes de preparar mudanças. `EditorialService`
delimita a unidade transacional por async context manager; autoriza/valida antes de
compare_and_set. O adaptador deve comparar before.version **e** before.current_revision
atomicamente, salvar after e confirmar ao sair; falhas devem reverter tudo.
Não há locks globais, filas ou alteração do CAS existente de RevisionStore.

Persistência proposta: metadados editoriais separados dos JSONB imutáveis, associados
por UUID ao recurso experimental. Ponteiros de aprovação/publicação referenciam
(resource_id, number) nas revisões; CHECKs para estados/versões e FKs devem ser
revistos na migração futura. Editorial version será incrementada por transições e
escritas de conteúdo, junto do CAS+INSERT de RevisionStore, no mesmo PostgreSQL.
Uma transição editorial não chama advance nem save nas revisões.

Reserva/ciclo da identidade e decisões também precisarão de persistência separada,
reserva permanente de UUID/URI, sucessor existente/ativo, ausência de ciclos e decisão
transacional. Não apagar recursos ou atualizar snapshots para encerrar identidades.

Os testes usam doubles locais, com duas tarefas observando a mesma versão: somente
um CAS vence. Também rejeitam conteúdo alterado durante validação. Demonstram o
protocolo e a política, **não** atomicidade PostgreSQL, rollback físico ou proteção
multiprocesso. Nenhum adaptador em memória é fornecido como fonte de verdade.

## Identidade e interface para #28

IdentityLifecycle é independente de EditorialRecord. active pode encerrar como
discontinued, replaced ou merged; decisão exige ator, instante e justificativa.
Substituição exige sucessor distinto, sem presumir equivalência. Fusão exige
sobrevivente distinto e evidência. Nem UUID nem URI podem coincidir com o destino.
O par original permanece em reserved_identity e no histórico da decisão; encerramento
não permite reativação ou nova destinação nesta entrega. Não há exclusão, owl:sameAs,
redirecionamento 308, tombstone ou serviço público de resolução.

Isso garante invariantes de objetos, não a reserva física contra administradores ou
outros serviços; existência/estado do sucessor e proteção de cadeias exigem serviço
transacional futuro. O contrato não reescreve vínculos ou grafos.

PreparedEditorialEvent acompanha cada proposta: identidade, estado anterior/posterior,
operação, escopo, ator, instante, revisão relacionada, versões anterior/posterior e
justificativa (obrigatória para return/withdraw/archive). Evento preparado não é
evento gravado. A #28 acrescenta [envelopes e armazenamento de auditoria](provenance-audit-versioning.md),
com identificador, proveniência completa e adaptação explícita desses eventos preparados.
A gravação junto do CAS de estado editorial continua pendente do adaptador PostgreSQL.
RETURN/ARCHIVE precisam de extensão governada da taxonomia. Não há publicação de
eventos, outbox ou sistema paralelo de logs.

## Evidências e critérios

Os testes em tests/api/test_editorial.py cobrem a matriz completa, estados desconhecidos,
permissões, validação real por perfil, dependências ausentes, referências locais,
edição/candidata, aprovação obsoleta, retirada/republicação/arquivamento, identidade e
CAS concorrente com doubles. A suíte preexistente continua verificando snapshots,
serialização, permissões e revisões; integração PostgreSQL fica separada.

Os critérios de #27 têm comportamento em domínio/aplicação e testes. Persistência
editorial operacional, integração com escrita de conteúdo e auditoria durável não
fazem parte desta entrega sem migração, e permanecem dependências explícitas.

## Verificação executada em 2026-10-12

- `uv run pytest`: 1.070 testes passaram; 91 pertencem à nova suíte editorial.
- `uv run ruff check . ../../tests`: passou.
- `uv run mypy src`: passou, 69 arquivos de código.
- Suíte editorial isolada pelo `.venv/bin/pytest`: 91 passaram, sem serviços externos.

Os 385 avisos da suíte completa são depreciações existentes de Starlette/httpx e
RDFLib/ConjunctiveGraph. O uv via Snap foi bloqueado no sandbox e executado com
escalonamento; nenhuma dependência ou lock foi alterado. Não houve teste de
persistência editorial PostgreSQL porque nenhum adaptador ou migração foi entregue.

`bash scripts/check.sh` passou completo na execução final: os mesmos 1.070 testes,
Ruff, mypy, build Next.js, TypeScript e validação Compose. A primeira execução fora
do sandbox parou em `npm: command not found`; a execução final acrescentou ao PATH
somente o Node.js 24.16.0 já instalado via NVM. Não houve instalação de ferramentas
ou mudanças de infraestrutura. `git diff --check` passou. Alterações ficaram no
working tree da branch corrente, sem commits, troca de branch ou pull request.
