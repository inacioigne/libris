# Verificação M06.04 — integração catalog BFF/Next.js — 2026-10-17

## Contexto

Esta execução conclui a integração do catálogo no BFF Next.js utilizando a sessão OIDC e o modelo de autorização já existentes no projeto, sem expor segredos ao cliente. A implementação respeita a fronteira de segurança do projeto: a API FastAPI continua sendo autoridade de authz, enquanto o BFF apenas resgata a sessão autenticada do lado do servidor, valida permissões e encaminha o access token no cabeçalho `Authorization` para a API catalográfica.

## Implementação

- Adaptação server-side em `apps/web/src/server/catalog/index.ts`
  - resolução da sessão a partir do cookie seguro do BFF
  - validação deny-by-default de permissões do catálogo
  - uso do `accessToken` retornado pela sessão resolvida
  - encaminhamento de `X-Request-ID`, `Cache-Control: no-store, private` e `Accept: application/json`
  - suporte a leitura, criação e atualização de Work com ETag obrigatório em PATCH
- Extensão de `apps/web/src/server/auth/service.ts`
  - novo `resolveSession()` que devolve também o `accessToken` quando a sessão está autenticada
  - preservação da política de refresh e revogação existente
  - normalização do payload de identidade para não incluir `csrf` indefinido em resultados de sessão expiradas ou indisponíveis
- Ajuste em `apps/web/src/server/admin/access.ts`
  - remoção de propriedades opcionais indefinidas em resultados de acesso para preservar o contrato de teste e evitar falsos positivos em comparações estritas

## Decisão técnica

- Reaproveitamos a infraestrutura existente de autenticação do BFF em vez de introduzir um sistema paralelo.
- A autenticação continua sendo resolvida no servidor; o browser nunca recebe token de API ou credencial de sessão.
- Os contratos gerados em `apps/web/src/generated/catalogographic-client.ts` e `catalogographic-openapi.ts` foram considerados fonte de verdade, inclusive para o cabeçalho `if-match` exigido em updates.
- O acesso é validado pela identidade obtida no `/api/v1/identity/me` com permissões declaradas e `deny-by-default` no nível da operação.

## Execuções realizadas

Todos os comandos foram executados com Node 24 em `/home/inacio/.nvm/versions/node/v24.16.0/bin` e a raiz do repositório em `/home/inacio/dev/libris`.

1. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH node --conditions=react-server --import tsx --test tests/auth.test.ts`
   - Resultado: passou.

2. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH node --conditions=react-server --import tsx --test tests/openapi-client.test.ts`
   - Resultado: passou.

3. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH node --conditions=react-server --import tsx --test tests/http-security.test.ts --test-reporter=spec`
   - Resultado: passou após correção do contrato de resposta de `identity()`.

4. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm test -- --test-reporter=tap`
   - Resultado: 168 testes aprovados, 0 falhas.

## Observações finais

- A integração M06.04 ficou alinhada com a arquitetura de segurança do repositório e com os contratos catalográficos já validados em M06.01–M06.03.
- A checagem final de regressão da suíte web foi executada com sucesso.
- O BFF continua sem vazar `accessToken`, `subject` ou quaisquer segredos para o navegador.
