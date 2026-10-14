# Diagnóstico do login no Compose — 2026-10-14

Consulta às issues #36 e #40 e inspeção dos serviços locais existentes, sem
alterar configuração ou aplicar migrações no banco de trabalho.

## Evidências desta execução

- `docker compose ps`: API, web, PostgreSQL e Elasticsearch saudáveis;
  Keycloak em execução.
- `POST http://localhost:3000/oidc/login`, com Origin e formulário válidos:
  HTTP 503. Confirmado também pela rede interna do container web.
- Variáveis de conexão, keyring e chave ativa presentes no container web;
  valores secretos não foram impressos.
- Descoberta OIDC a partir do container web: HTTP 200 e issuer correspondente
  ao configurado.
- Consulta `to_regclass` pela conexão efetiva do frontend: `libris_web.sessions`
  e `libris_web.auth_transactions` existem; `libris_web.auth_quotas` retorna NULL.

## Causa e encaminhamento

A migração incremental `apps/web/migrations/0002_auth_quotas.up.sql` está pendente.
O admission check em `apps/web/src/server/auth/handlers.ts` consulta a quota
antes de iniciar OIDC e responde 503 quando o banco não consegue atendê-la.
O healthcheck web usa a página pública `/pt`, portanto não detecta essa pendência.
`docker compose up --build -d` reconstrói imagens e inicia serviços, mas não aplica
migrações, conforme ADR 0033.

Aplicar explicitamente somente 0002 no banco de sessões, com papel administrativo,
conforme `identity-web.md`. A migração 0001 já está instalada e não deve ser repetida.
Nenhuma migração foi executada neste diagnóstico. Login completo, callback e
autorização após essa aplicação permanecem sem nova validação.

Não houve alteração de código; suítes de build/testes não foram executadas.
