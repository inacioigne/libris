# M06 — Catalogação utilizável (Fase 1)

Entregar o primeiro fluxo operacional do Libris: catalogar uma monografia ponta a ponta pela interface (Work → Instance → Item), com validação, ciclo editorial e importação/exportação MARC 21. Critério de saída: um catalogador autenticado cria, valida, publica e consulta uma monografia pela UI, e importa/exporta o mesmo registro em MARC 21, com evidências documentadas.

**Estimativas:** M ≈ 3–5 dias, L ≈ 1–2 semanas (uma pessoa).

## Ordem sugerida

```
M06.01 ─┬─ M06.02 ──┐
        └─ M06.09 ─┬─ M06.10
M06.03 ─── M06.04 ─┼─ M06.05 ─┬─ M06.06
                   │          └─ M06.08
                   └─ M06.07
M06.09 + M06.05 ── M06.11
Todas ──────────── M06.12
```

Trilhas paralelas: **A** (M06.01, 02) · **B** (M06.03, 04, 07) · **C** (M06.09, 10).

## Fora do escopo

Elasticsearch/outbox, OPAC público de busca, reconciliação de autoridades, circulação, periódicos, estatísticas.

## Convenções

Código em inglês, documentação em português; ADR para mudanças estruturais; migrações incrementais com testes upgrade/downgrade; `scripts/check.sh` ao final de cada issue.

---

## M06.01 — ADR e congelamento do esquema persistente (saída do modo experimental)

**Labels:** `area:api`, `type:adr`, `type:migration` · **Depende de:** — · **Estimativa:** M

**Contexto.** Os dados bibliográficos vivem em tabelas `experimental_semantic_*` (migrações 0001–0004). Módulos novos não devem depender de esquema experimental.

**Critérios de aceite**

- [ ] ADR 0039 define o esquema persistente canônico, o que muda em relação ao experimental e a estratégia de preservação de dados.
- [ ] Migração Alembic incremental `0006` (sem `create_all`, sem execução no startup), preservando legado e snapshots.
- [ ] Índices necessários às consultas de listagem (M06.02): tipo, estado editorial, atualizado em, rótulo principal.
- [ ] Testes de upgrade/downgrade em PostgreSQL descartável e isolado.
- [ ] Documento de verificação datado, sem sobrescrever relatórios anteriores.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

**Notas.** Bloqueia M06.02 e M06.09.

---

## M06.02 — API de listagem e consulta do catálogo (Postgres)

**Labels:** `area:api` · **Depende de:** M06.01 · **Estimativa:** M

**Contexto.** Hoje só há `GET /api/v1/catalog/{collection}/{id}`. O editor e o OPAC precisam listar e localizar registros.

**Critérios de aceite**

- [ ] `GET /api/v1/catalog/{collection}` com paginação por cursor, ordenação estável e limites validados.
- [ ] Filtros: estado editorial, texto no rótulo/título (prefixo e `ILIKE` indexado), tipo de agente/assunto, atualizado desde.
- [ ] Autocomplete leve de Agent e Subject locais (`/agents?q=`, `/subjects?q=`) para uso nos vínculos.
- [ ] Permissões deny-by-default por coleção, coerentes com `security-access-matrix`.
- [ ] Contrato OpenAPI, Problem Details e testes de unidade + integração PostgreSQL.
- [ ] Documentado como solução transitória: a descoberta definitiva é o Elasticsearch (Fase 2, ADR 0003).
- [ ] `bash scripts/check.sh` executado e resultado registrado.

**Notas.** Não introduzir Elasticsearch nesta milestone.

---

## M06.03 — Cliente TypeScript do OpenAPI e camada BFF autenticada

**Labels:** `area:web`, `type:adr` · **Depende de:** — · **Estimativa:** M

**Contexto.** A web ainda não consome a API de catalogação. O token OIDC não pode chegar ao navegador (AGENTS.md).

**Critérios de aceite**

- [ ] Script versionado que gera tipos/cliente a partir do OpenAPI e falha no CI quando há divergência.
- [ ] Route handlers/server actions no Next.js que chamam a API com o token da sessão do lado servidor; nada em `localStorage`, URL pública ou `NEXT_PUBLIC_*`.
- [ ] Tratamento central de Problem Details, `X-Request-ID` e ETag/`If-Match` (conflito 412/409 tipado).
- [ ] Proteção CSRF nas mutações, reaproveitando `http-security`.
- [ ] Testes (`npm run typecheck`, `npm run build`, testes de BFF) e ADR curto da decisão de geração do cliente.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

**Notas.** Base de M06.04–M06.08.

---

## M06.04 — Formulários dinâmicos guiados pelos perfis declarativos

**Labels:** `area:web`, `area:api` · **Depende de:** M06.03 · **Estimativa:** L

**Contexto.** Os perfis 2.0 (core, work, instance, item, agent, subject, monograph) já descrevem campos, mas não há renderização.

**Critérios de aceite**

- [ ] Contrato de leitura do perfil resolvido para UI (usar `/profiles` e `/profiles/release`; estender só se necessário, com versão).
- [ ] Biblioteca de componentes de campo: literal com idioma, data, URI, valor controlado, referência a entidade, campos repetíveis, grupos.
- [ ] Rótulos e ajuda em pt/en vindos do perfil e de `i18n/messages.ts`.
- [ ] Acessibilidade: HTML semântico, foco, rótulos e mensagens de erro associadas (WCAG 2.2 AA como meta).
- [ ] Serialização do formulário para os DTOs Create/Update existentes, com testes de ida e volta usando as fixtures `tests/fixtures/bibliographic/contracts`.
- [ ] Prefira primitivas Radix; shadcn/ui só se justificado (ADR 0005).
- [ ] `bash scripts/check.sh` executado e resultado registrado.

**Notas.** Não implementar ontologia nova aqui; extensões seguem o mecanismo governado.

---

## M06.05 — Editor de Work com Agent e Subject vinculados

**Labels:** `area:web` · **Depende de:** M06.02,M06.04 · **Estimativa:** L

**Contexto.** Primeiro editor real: criar, editar e visualizar uma obra.

**Critérios de aceite**

- [ ] Telas em `/[locale]/admin/catalog/works`: lista (M06.02), criar, editar, detalhe.
- [ ] Edição de contribuições (agente + papel), assuntos e títulos (principal, variante, traduzido).
- [ ] Seletor de Agent/Subject locais com busca e criação rápida em painel lateral; referências externas e não reconciliadas permitidas conforme `relationships.md`.
- [ ] Edição otimista com ETag: conflito exibe diferença e permite recarregar.
- [ ] Navegação por permissões efetivas (reuso de `server/admin/navigation.ts`).
- [ ] Teste e2e do fluxo criar → editar → ver.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

---

## M06.06 — Editor de Instance e Item e gestão de vínculos

**Labels:** `area:web` · **Depende de:** M06.05 · **Estimativa:** L

**Contexto.** Completar a cadeia Work → Instance → Item na UI.

**Critérios de aceite**

- [ ] Telas de Instance (edição, ISBN, publicação, extensão) e Item (localização/cota, identificador local).
- [ ] Criar Instance a partir de um Work e Item a partir de uma Instance, usando as operações explícitas de relacionamento (`PATCH .../relationships`).
- [ ] Visão hierárquica do registro (Work → Instances → Items) com vínculos navegáveis.
- [ ] Item permanece descrição bibliográfica; não representa empréstimo nem disponibilidade (`AGENTS.md`).
- [ ] Testes de UI e de contrato para vínculos válidos e inválidos (usar fixtures `relationships/valid|invalid`).
- [ ] `bash scripts/check.sh` executado e resultado registrado.

---

## M06.07 — Validação SHACL e diagnósticos na UI

**Labels:** `area:web`, `area:api` · **Depende de:** M06.04 · **Estimativa:** M

**Contexto.** A API já devolve diagnósticos estáveis (catalogographic-errors 1.0) e há pré-validação de relacionamentos (ADR 0037).

**Critérios de aceite**

- [ ] Exposição de pré-validação do conteúdo (sem persistir) se ainda não houver rota pública; ADR se o contrato mudar.
- [ ] Mapeamento de código de diagnóstico → campo do formulário, com mensagem localizada.
- [ ] Painel de problemas (erros vs avisos), com navegação para o campo.
- [ ] Bloqueio de submissão/publicação com erros; avisos não bloqueiam.
- [ ] Testes com as fixtures `serialization/invalid` e `institutional/invalid-*`.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

---

## M06.08 — Fluxo editorial, histórico e restauração na UI

**Labels:** `area:web` · **Depende de:** M06.05 · **Estimativa:** L

**Contexto.** A API tem sete comandos editoriais, revisões, comparação, auditoria e restauração (M05.05). Falta interface.

**Critérios de aceite**

- [ ] Barra de estado editorial com apenas as ações permitidas para o usuário e o estado atual.
- [ ] Comandos submit/approve/publish/return/withdraw/republish/archive, com justificativa obrigatória onde a API exige.
- [ ] Linha do tempo (`/history`), visualização de revisão, comparação semântica (`/revisions/compare`) e restauração (`/revisions/restore`) com confirmação.
- [ ] Pré-visualização do registro público (`/public`).
- [ ] Estados de erro e conflito (ETag de edição) tratados sem perda do que o usuário digitou.
- [ ] Testes e2e do ciclo rascunho → publicado → republicado → restaurado.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

---

## M06.09 — Importação MARC 21 → BIBFRAME (monografia)

**Labels:** `area:interop`, `type:adr` · **Depende de:** M06.01 · **Estimativa:** L

**Contexto.** ADR 0002 define MARC como adaptador, não modelo interno. Esta issue entrega o mapeamento de entrada.

**Critérios de aceite**

- [ ] ADR 0040: mapeamento MARC 21 → perfil monográfico, lacunas, perdas e regras de falha.
- [ ] Adaptador em `infrastructure` para MARCXML e ISO 2709 (avaliar `pymarc`; dependência exige atualizar `uv.lock`).
- [ ] Campos cobertos de início: 001/003, 020, 040, 041, 100/110/700, 245, 250, 264, 300, 490/8xx, 6xx, 856; relatório de campos não mapeados.
- [ ] Resultado devolvido como DTOs Create + diagnósticos, nunca gravado direto; confirmação humana na UI (prévia).
- [ ] Corpus de teste com registros reais anonimizados/livres e casos inválidos; comparação por isomorfismo de grafos.
- [ ] Rota `POST /api/v1/catalog/import/marc` com limites de tamanho e permissão própria.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

**Notas.** Referência: conversor MARC→BIBFRAME da Library of Congress, só para validar o mapeamento.

---

## M06.10 — Exportação BIBFRAME → MARC 21 e formatos RDF na UI

**Labels:** `area:interop`, `area:web` · **Depende de:** M06.09 · **Estimativa:** M

**Contexto.** Fechar o ciclo de interoperabilidade para registros publicados.

**Critérios de aceite**

- [ ] Exportação MARCXML (e ISO 2709 se viável) de Work+Instance(s) publicados, com relatório de perdas.
- [ ] Botões de exportação (JSON-LD, Turtle, MARCXML) no detalhe do registro, respeitando visibilidade pública.
- [ ] Teste de ida e volta: importar → exportar → comparar campos essenciais.
- [ ] Documentação das limitações da conversão inversa.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

---

## M06.11 — Importação de registros por SRU (cópia de catalogação)

**Labels:** `area:interop` · **Depende de:** M06.09,M06.05 · **Estimativa:** M

**Contexto.** Reduz digitação: buscar registro em catálogos externos e importar com revisão.

**Critérios de aceite**

- [ ] Cliente SRU assíncrono (`httpx`), com lista configurável de fontes, timeouts, limites e sem seguir redirecionamentos para hosts não permitidos.
- [ ] UI: busca por ISBN/título/autor, prévia do registro convertido (M06.09) e confirmação.
- [ ] Detecção simples de duplicidade por ISBN/identificador antes de gravar.
- [ ] Z39.50 fica fora do escopo; registrar ADR de decisão e follow-up.
- [ ] Testes com servidor SRU simulado; nenhum teste depende de rede externa.
- [ ] `bash scripts/check.sh` executado e resultado registrado.

**Notas.** Atenção a SSRF e a termos de uso das fontes.

---

## M06.12 — E2E, homologação e critérios de saída da M06

**Labels:** `area:qa`, `type:docs` · **Depende de:** M06.05,M06.06,M06.07,M06.08,M06.10,M06.11 · **Estimativa:** M

**Contexto.** Comprovar a entrega com execução real, no estilo dos relatórios de verificação do projeto.

**Critérios de aceite**

- [ ] Suíte e2e (Playwright): login → criar Work/Instance/Item → validar → publicar → ver no `/public` → exportar MARC.
- [ ] Execução documentada de `bash scripts/check.sh`, pytest (incl. integração PostgreSQL), mypy, ruff, typecheck e build; registrar o que ficou bloqueado.
- [ ] Relatório `docs/architecture/catalog-ui-m06-verification-<data>.md`.
- [ ] Atualização do README e de `AGENTS.md` com o novo estado (sem declarar homologação institucional não feita).
- [ ] Backlog da Fase 2 (outbox + Elasticsearch) registrado em nova milestone.
- [ ] `bash scripts/check.sh` executado e resultado registrado.
