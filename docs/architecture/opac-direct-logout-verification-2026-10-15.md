# Logout com retorno direto ao OPAC

Data: 2026-10-15 (America/Manaus).

A implementação anterior usava as entradas legadas `/pt` e `/en` no parâmetro
`post_logout_redirect_uri`, seguidas por redirect local ao OPAC. Esta correção
remove essa adaptação: o parâmetro passa a enviar diretamente `/pt/opac` ou
`/en/opac`, conforme o destino validado do formulário. As evidências anteriores
permanecem históricas; a política de retorno descrita nelas foi substituída aqui.

O JSON do realm e o preparador de integração isolada agora registram também as
URIs OPAC. As entradas antigas são preservadas. O harness HTTP e o teste Keycloak
real opcional passam a verificar explicitamente o parâmetro direto `/en/opac`.

## Aplicação local

- Cliente `libris-web` do realm `libris` atualizado pela API administrativa:
  adicionadas apenas `http://localhost:3000/pt/opac` e
  `http://localhost:3000/en/opac` aos destinos de logout permitidos.
- Atributos e destinos anteriores preservados e conferidos por leitura posterior.
  Nenhum usuário, sessão, papel, segredo ou volume foi removido/recriado.
- `docker compose build web` e `docker compose up -d --no-deps web` aprovados.
  Somente o container web foi substituído; serviço saudável após atualização.
- Endpoint real do Keycloak aceitou as duas URLs de logout com retorno OPAC
  (HTTP 200, sem autenticação de usuário ou cookies enviados).
- `http://localhost:3000/pt/opac` respondeu HTTP 200.

As credenciais administrativas existentes foram usadas apenas em memória e não
foram registradas. O import de startup não atualiza realms persistidos; por isso,
a alteração administrativa local foi necessária além da mudança no JSON.
A aceitação das URIs pelo provedor não equivale a homologação integral de SSO
com usuário real ou de produção.

## Regressão

`bash scripts/check.sh` concluído com código 0 após a correção:

| Verificação | Resultado |
| --- | --- |
| API pytest | 1.668 aprovados, 477 warnings |
| Ruff | Aprovado |
| mypy | Aprovado, 86 arquivos |
| Frontend `npm test` | 167 aprovados, sem skips |
| Frontend build/typecheck | Aprovados |
| Configuração Compose | Aprovada |

O ensaio `tests/http.e2e.ts` também passou (1 teste, sem skips), com Next construído,
OIDC simulado assinado, API simulada, PostgreSQL descartável e Chromium habilitado.
A nova asserção confirmou `post_logout_redirect_uri=<origem>/en/opac` na resposta
do logout. Login, CSRF, callback, autorização, idiomas e CSP continuaram aprovados.
O container PostgreSQL do ensaio foi encerrado; volumes de trabalho preservados.
