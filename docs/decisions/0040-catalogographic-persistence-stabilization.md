# ADR 0040 — Estabilização incremental da persistência catalográfica

Data: 2026-10-17. Status: aceito para implementação técnica da M06.02 / #54.
Homologação institucional, dimensionamento e operação de produção permanecem separados.

## Contexto e estado atual

M03 estabeleceu identidade, snapshots, CAS, proveniência e metadados editoriais;
M05 concretizou operações/consultas HTTP sobre esses mesmos serviços PostgreSQL.
O prefixo `experimental_semantic_` registra a origem do armazenamento, mas não deve
obrigar sua substituição para cada nova entrega. ADRs 0008–0015, 0019, 0026–0029,
0034, 0036 e 0039 continuam definindo suas garantias e limitações específicas.

O [inventário e a política operacional](../architecture/catalogographic-persistence.md)
identificam quatro tabelas em public, modelos/stores, constraints, índices e triggers.
A cadeia é 0001_semantic → 0002_revision_actor → 0003_semantic_audit →
0004_semantic_editorial → **0005_web_auth**. O head só cria/adota o schema separado
libris_web; não transforma dados bibliográficos. Não há consumidor público de nomes
físicos. As consultas M05 já usam as PKs/UNIQUE existentes; o EXPLAIN M05.06 não
justifica uma renomeação ou índice adicional por si só.

## Alternativas avaliadas

| Alternativa | Integridade, dados e contratos | Operação, reversão e manutenção |
| --- | --- | --- |
| A — Preservar estrutura física e consolidar política | Preserva FKs, UUID/URI, JSONB, revisões, estados e eventos sem transformação; v1 permanece igual | Nenhum DDL/lock de renomeação, nenhuma indisponibilidade adicional; rollback desta entrega é documental/testes; mantém nomes históricos |
| B — Renomeação incremental motivada por problema concreto | Exigiria revisar FKs, índices/constraints, triggers, SQL de testes, ORM e compatibilidade de versões implantadas | Locks DDL e coordenação de deploy/rollback sem ganho funcional demonstrado; justificável futuramente apenas com consumidor/problema comprovado |
| C — Camada de compatibilidade para consumidores concretos | Views/aliases poderiam manter SQL antigo, mas precisam preservar escrita, CAS, constraints e permissões | Acrescenta objetos e obrigações de suporte sem consumidor atual que as justifique; não adotada |

## Decisão e justificativa

Adotar **A**, sem nova migração, view, alias, adaptador ou renomeação cosmética.
Os nomes existentes passam a ser nomes físicos históricos suportados da persistência
catalográfica M03–M05. A estabilidade operacional é um compromisso de evolução
compatível e verificada; não significa esquema bibliográfico definitivo, validação
universal de RDF, capacidade de produção ou homologação institucional de perfis.

Novos casos catalográficos podem reutilizar os serviços e contratos atuais sem
condição prévia de remover o prefixo. Mantêm-se as limitações semânticas do perfil
experimental legado, inclusive grafos agregados, sem conversão/publicação implícita.
Nenhuma API depende de nomes SQL; consumidores futuros usam contratos de aplicação.

## Compatibilidade e limites de domínio

O domínio bibliográfico/catalográfico conserva Work, Instance, Item semântico,
Agent/Subject, relacionamentos, identificadores, conteúdo RDF, propriedade dos nós,
revisões/snapshots, proveniência e estados/eventos editoriais. Propriedade de um
snapshot não é tenancy; heldBy referencia instituição bibliográfica e não concede
permissões sobre uma organização. Não há coluna institucional de ownership/tenant.

Inventário físico, localização operacional de exemplares, circulação, empréstimos,
reservas, multas, aquisições e disponibilidade pertencem a domínios futuros com
identidade e transações próprias. **bf:Item não é o agregado de inventário/circulação**.
Não são criadas tabelas futuras nem permitidos acessos diretos entre módulos.
Esses módulos referenciarão identidades por contratos explícitos. Elasticsearch
continua projeção reconstruível; sua primeira integração exige decisão de
consistência/outbox, sem escrita dupla antecipada.

## Política de evolução do esquema

1. Toda alteração física deve demonstrar necessidade, consumidores, impacto nos
   dados/locks/deploy, compatibilidade e reversão. Mudanças estruturais exigem ADR.
2. Acrescentar revisão incremental ao head efetivo; nunca editar 0001–0005, usar
   create_all, migrar no startup ou criar revisão vazia para sinalizar uma entrega.
3. Preservar UUID/URI armazenados, snapshots/revisões/release, histórico, atores nulos,
   eventos e ponteiros de publicação. Mudança da base de URIs só afeta alocações novas.
4. Preferir expansão compatível; transformação necessária requer mapeamento,
   validação e evidência em banco isolado antes de eventual contração. Não alterar
   snapshots históricos, inventar backfill de autoria ou perder extensões RDF.
5. Reutilizar session.begin, stores com flush, gate transacional e ambos os CAS.
   Atualizar ORM e migração juntos, conferir alembic check e testar falhas/rollback.
6. DTOs/Problem Details/OpenAPI v1, perfis, SHACL e revisão do registro são dimensões
   independentes (ADR 0029). Mudança física não autoriza quebra pública ou semântica.
7. Medir consultas/carga antes de materializar tipo, criar índices ou substituir o
   gate conservador. Documentar índices e efeitos na escrita, histórico e legado.

## Upgrade, downgrade e reversibilidade

Nenhum upgrade/downgrade novo é necessário para adotar esta decisão. Instalação
nova continua usando explicitamente alembic upgrade head. A regressão ampliada
exercita head idempotente e **0005 → 0004 → 0005** com dados bibliográficos
representativos, comparando todas as colunas das quatro tabelas e leituras semânticas.
0005 preserva inclusive as tabelas web no downgrade, conforme ADR 0034.

Isso não torna segura toda a cadeia histórica: 0004 → 0003 perde metadados
editoriais e recusa RETURN/ARCHIVE; 0003 → 0002 perde eventos/reason; 0002 → 0001
remove actor_id; 0001 → base remove recursos/revisões. Os testes desses limites
usam somente bancos inicialmente vazios e descartáveis. Não executar esses
procedimentos em bancos de trabalho como rollback desta estabilização. Para uma
alteração futura não reversível sem perdas, preferir correção progressiva e plano
explícito de recuperação validado; nunca prometer reversão por apagar histórico.

## Consequências, riscos e decisões futuras

Benefícios: nenhum dado migrado, menor risco de indisponibilidade, compatibilidade
imediata M05 e menor custo de manutenção. Custo: nomes históricos menos expressivos,
necessidade de manter inventário/política e limites de desempenho ainda não medidos.

Advisory gate serializa decisões e escritas DTO; relações JSONB não têm FK SQL
universal; integridade depende dos serviços e da classificação de referências.
Triggers não protegem contra administradores que os removam; o par UUID/URI não tem
trigger de imutabilidade. Grants de produção, backup/restauração, retenção, fusão/
tombstones, perfis institucionais e carga exigem decisões/verificações próprias.
Não há promessa de tenancy ou proteção contra SQL privilegiado fora do protocolo.

Mitigações atuais: autorização existente, CAS no banco, transação única, FKs/CHECKs,
triggers append-only, parsing limitado e regressões reais PostgreSQL/M05.
[Evidências datadas desta entrega](../architecture/catalogographic-persistence-m0602-verification-2026-10-17.md).
