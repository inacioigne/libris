# Verificação da unificação do Compose

Data: 2026-10-13.

`docker-compose.yml` incorpora o serviço Keycloak, seu alias de rede, importação
do realm e volume persistente antes definidos em `docker-compose.oidc.yml`.
O arquivo separado foi removido. OIDC fica habilitado por padrão no Compose e
em `.env.example`, com issuer `http://keycloak.localhost:8081/realms/libris`.
As credenciais administrativas continuam obrigatórias pelo ambiente, sem valores
fixos versionados. Configurações explícitas do ambiente prevalecem.

Os comandos operacionais e referências atuais foram atualizados; ADRs e relatórios
históricos permanecem como evidência das configurações de suas respectivas datas.

## Execução e resultados

| Verificação | Resultado |
| --- | --- |
| Comparação dos JSON resolvidos por `docker compose config --format json` | Equivalentes: arquivos anteriores recuperados de `HEAD`, combinados, versus arquivo unificado; mesmo diretório de projeto e `.env.example`, com credenciais administrativas efêmeras no ambiente |
| `bash scripts/check.sh` | Passou fora do sandbox, com Node 24.16.0 e `UV_CACHE_DIR=/tmp/libris-uv-cache` |
| API: `uv run pytest` | 1260 testes passaram; 465 warnings de depreciação |
| API: `uv run ruff check . ../../tests` | Passou |
| API: `uv run mypy src` | Passou, 76 arquivos |
| Web: `npm test` | 53 testes passaram |
| Web: `npm run build` | Passou |
| Web: `npm run typecheck` | Passou |
| `docker compose --env-file .env.example config --quiet` | Passou pelo script, com credenciais administrativas aleatórias apenas para validação estática |
| `bash -n scripts/check.sh` e `git diff --check` | Passaram |

A tentativa inicial no sandbox parou no `uv` via Snap (`snap-confine`). As
tentativas separadas tiveram limitação de subprocessos: pytest foi interrompido,
`npm test` falhou e o build não conseguiu interpretar `tsc --showConfig`; Ruff,
mypy e typecheck passaram. A execução completa posterior fora do sandbox passou.

Nenhum serviço foi iniciado, nenhum volume foi removido e nenhuma migração foi
executada. A equivalência é de configuração, sem nova homologação de Keycloak,
login de navegador ou produção. Issues abertas M04 (#37–#42) foram consultadas;
esta alteração permanece restrita à infraestrutura local existente.
