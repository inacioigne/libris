# ADR 0026 — Estado editorial separado do conteúdo e da identidade

Status: implementado tecnicamente para #27; adaptador PostgreSQL e homologação institucional pendentes

Data: 2026-10-12

## Contexto

As issues #26/#27 exigem estados, publicação validada e edição pós-publicação.
ADRs 0011/0015 protegem snapshots imutáveis e CAS de conteúdo; 0016 fornece ator
OIDC e permissões. ADR 0019 reserva identidades retiradas. ADRs 0021/0022 fornecem
perfis e SHACL, mas URI-only histórica não prova localidade ou integridade.
Os seis estados sozinhos não expressam publicação anterior e candidata simultâneas.

## Decisão

Implementar `EditorialRecord` imutável, matriz fechada de oito transições e versão
editorial própria, sem migração. `current_revision`, `published_revision` e
`approved_revision` são ponteiros de conteúdo; `version` protege mudanças editoriais.
`public_revision` só é visível em published. Retirada conserva o ponteiro histórico.

Após publicação, nova revisão abre `candidate_state=draft` e conserva published e
a revisão pública anterior. A candidata usa draft/in_review/approved e a mesma
matriz para aprovação/publicação, com escopo explícito. Sua publicação substitui
somente o ponteiro público, fecha a candidata e mantém UUID/URI e snapshots.
Retirada/republicação operam sobre a revisão previamente publicada, mesmo com
candidata pendente; republicação a revalida. Candidata de registro retirado precisa
republicar a revisão anterior antes de substituí-la. Arquivamento encerra a candidata
sem apagar conteúdo. Edição em revisão/aprovação exige devolução; retirados e
arquivados não recebem novas revisões nesta política inicial.

Permissões editoriais explícitas separam submissão, revisão e publicação.
Catalogador recebe submissão; reviewer aprova/devolve; publisher publica/retira/
republica/arquiva. Authority-manager conserva permissões anteriores; precisa de
papel editorial adicional para participar. Admin recebe o enum completo conforme
contrato vigente; system:admin não vira bypass. Não exigir atores humanos diferentes:
a separação é de capacidades e atribuição de papéis, sem regra de quatro olhos.

`EditorialService` coordena autorização, validação e CAS por `EditorialTransaction`,
contrato obrigatório de unidade transacional, sem adaptador concreto nesta entrega.
Publicação exige snapshot exato, perfil local aplicável, SHACL executado e conforme,
classificação completa das relações e resolução de referências locais. Sem contexto,
classificação ou validação, bloquear. Não inferir localidade de prefixos nem buscar
contextos/imports remotos. Reutilizar os validadores existentes, sem regras paralelas.

`prepare_content_revision` prepara metadados a salvar junto do próximo snapshot;
não escreve nem chama o serviço legado. O adaptador futuro deve integrar ambos na
mesma transação PostgreSQL e manter o CAS de RevisionStore. Transições devem comparar
versão editorial e revisão corrente, proteger dependências locais e confirmar ou
reverter tudo. Não usar observação seguida de UPDATE sem condição.

Ciclo da identidade é outro contrato: active → discontinued/replaced/merged,
com decisão explícita, sucessor distinto quando aplicável e evidência para fusão.
Conservar par e histórico; encerramentos são terminais nesta entrega. Não gerar
owl:sameAs, redirects, tombstone ou reassociação automática de vínculos.

Eventos são **preparados**, com estados/escopo, ator, instante, revisão, versões e
justificativa. Não representam auditoria persistida. #28 definirá envelope, histórico
completo, armazenamento e garantias duráveis na mesma transação.

## Alternativas e consequências

- Rebaixar published para draft perderia a distinção de visibilidade; manter candidata.
- Publicar toda revisão ou usar current_revision como versão editorial permitiria
  publicação silenciosa ou aprovações concorrentes; ponteiros e versão independentes.
- Máquina genérica, filas e novas tabelas definitivas não são necessárias para #27.
- Um repositório em memória de produção esconderia a ausência de persistência; há
  apenas doubles de testes para verificar o protocolo, sem promessa multiprocesso.

BibliographicService/RevisionStore e migrações permanecem intactos; não há workflow
operacional persistido. A arquitetura descreve a futura persistência separada dos
snapshots e os limites de integridade global. Ver [contrato](../architecture/editorial-lifecycle.md).
