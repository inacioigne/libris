# ADR 0004 — Sessões OIDC no BFF web

- **Status:** Implementação local; armazenamento de produção pendente de aprovação
- **Data:** 2026-10-23
- **Escopo:** Autenticação do frontend e integração com a API

## Contexto

O frontend obtém tokens OIDC pelo fluxo Authorization Code com PKCE. Guardar os
tokens completos em cookies do navegador amplia o impacto de vazamentos de logs,
configuração incorreta de cookies e futuras rotas que manipulem esses valores.

## Direção implementada

O Next.js atua como BFF. O callback guarda access e refresh tokens em uma sessão
server-side e entrega ao navegador somente um identificador aleatório de 256 bits
em cookie `HttpOnly`, `SameSite=Lax` e `Secure` sob HTTPS. Somente o hash SHA-256
do identificador é usado como chave interna.

O BFF renova o access token antes de expirar, serializa refreshes concorrentes na
mesma sessão, remove a sessão quando refresh ou validação na API falham e oferece
logout que também tenta encerrar a sessão no provedor OIDC. A API continua sendo
a autoridade para autenticação do access token e autorização.

As páginas administrativas aplicam guards no servidor antes de renderizar seu
conteúdo. Esses guards usam as permissões efetivas retornadas por
`GET /api/v1/identity/me`, e não nomes de papéis do provedor, mantendo o
mapeamento papel–permissão sob responsabilidade da API. Ausência de sessão inicia
o fluxo OIDC com retorno à rota solicitada; permissão insuficiente e falha ao
consultar a API são tratadas como estados distintos. Esse guard melhora a
experiência e evita renderização indevida, mas não substitui a autorização dos
endpoints da API.

## Limite atual

O registro disponível é propositalmente apenas em memória e recusa execução em
`NODE_ENV=production`. Isso permite validar o contrato sem escolher silenciosamente
a infraestrutura definitiva. Ele perde sessões ao reiniciar e não atende múltiplas
instâncias.

Antes de produção, este ADR deve ser concluído com um `SessionStore` compartilhado,
TTL, criptografia em repouso, limpeza de expirados, rotação de chaves e coordenação
atômica de refresh. PostgreSQL e Redis permanecem alternativas em avaliação.

## Consequências

- Tokens OIDC deixam de ser armazenados no navegador.
- Rotas administrativas podem exigir permissões no servidor sem expor tokens ao
  navegador.
- Reiniciar o servidor web encerra sessões locais.
- Uma implantação de produção falha explicitamente até receber um store aprovado.
- Cookies legados de tokens são apagados no próximo callback ou logout.
