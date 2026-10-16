# Verificação dos redirecionamentos OPAC

Data: 2026-10-15 (America/Manaus).

## Alterações verificadas

- Página inicial em `/pt/opac` e `/en/opac`; `/` encaminha para `/pt/opac`.
- Entradas legadas `/pt` e `/en` preservam query, parâmetros repetidos e feedback
  ao encaminhar para o OPAC. Idiomas não suportados continuam retornando 404.
- Destinos de autenticação aceitam somente as entradas canônicas existentes,
  OPAC e admin; URLs externas e caminhos codificados/adulterados continuam negados.
- Login administrativo preserva seu destino. Login público, logout e erros sem
  transação confiável usam o OPAC.
- Logout via provedor conserva `/pt` e `/en` registrados nos realms existentes;
  as entradas legadas encaminham ao OPAC. Falha do provedor permite retorno local
  depois da revogação, sem reativar a sessão.
- Layout comum restaura idioma HTML e providers de tema/sidebar em ambas as áreas.
  Dashboard administrativo fica dentro da guarda server-side, sem menu administrativo
  nas respostas anônimas, expiradas ou negadas. Links de início preservam o idioma.
- Tradução inglesa `authority` completa o dicionário usado pela sidebar.

## Execução

Node.js 24.16.0 e Python 3.13.15. `bash scripts/check.sh` concluiu com código 0:

| Verificação | Resultado |
| --- | --- |
| `uv run pytest` | 1.668 aprovados; 477 warnings |
| `uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py` | Aprovado |
| `uv run mypy src` | Aprovado; 86 arquivos |
| `npm test` | 167 aprovados, sem skips |
| `npm run build` | Aprovado |
| `npm run typecheck` | Aprovado |
| `docker compose --env-file .env.example config --quiet` | Aprovado pelo script |

As primeiras tentativas dentro do sandbox foram bloqueadas por restrições de
processos Node, portas locais e snap/uv. A execução completa acima foi refeita
fora dessas restrições. A tentativa API redundante no sandbox foi encerrada.

O primeiro ensaio HTTP com Next construído, OIDC simulado e PostgreSQL descartável
identificou menu administrativo renderizado fora da guarda; a renderização foi
movida para o callback autorizado antes da execução final. O build também detectou
a tradução inglesa ausente, corrigida antes da execução final.
O ensaio Chromium seguinte detectou `style-src-attr` no avatar autenticado;
a imagem estática passou a usar HTML nativo, sem estilo inline gerado,
preservando a CSP com nonce. Os testes frontend/build/typecheck foram repetidos
após essa correção.

Não foram alterados realms, credenciais, bancos ou volumes de trabalho.
Keycloak real e homologação de produção não fazem parte desta verificação.

## Ensaio HTTP e Chromium final

Aprovado: 1 teste HTTP de integração, sem skips, com Next.js construído,
OIDC simulado com JWTs assinados, API simulada e PostgreSQL 17 novo em tmpfs.
`TEST_WEB_ISOLATED=1` e `TEST_WEB_BROWSER_ENABLED=1` habilitaram o harness
`tests/http.e2e.ts` e o Chromium real. O container criado para o ensaio foi
encerrado pelo próprio script; nenhum volume persistente foi usado.

O harness verificou redirects legados/canônicos, 404 para idioma inválido,
HTML e cookies sem tokens, CSP com nonce, proteção CSRF, replay de callback,
sessão expirada, falhas de API, permissões administrativas e logout.
No navegador, troca de idioma via Link preservou navegação sem reload e o idioma
HTML; login/callback/logout funcionaram com CSP aplicada, sem violações.
Uma página hostil com script inline foi bloqueada pela mesma CSP.

Após a última correção, `npm test` (167 aprovados), `npm run build` e
`npm run typecheck` também foram repetidos com sucesso.
Esse ensaio usa provedor simulado e não equivale a homologação Keycloak real.
