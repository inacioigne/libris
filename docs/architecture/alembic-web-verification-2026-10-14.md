# Verificação da centralização Alembic — 2026-10-14

Decisão: [ADR 0034](../decisions/0034-alembic-web-schema.md).
Issues M04 consultadas, em especial #40. Nenhuma issue foi alterada.

## Execução

PostgreSQL 17-bookworm descartável em container próprio, armazenamento tmpfs e
porta efêmera publicada somente em loopback. Cada harness recebeu banco exclusivo
inicialmente vazio. Nenhum comando de migração foi aplicado ao banco de trabalho.
Node 24.16.0; Python 3.13.15. Não foram alteradas dependências ou locks.

| Verificação | Resultado |
| --- | --- |
| `bash scripts/check.sh` | Passou fora do sandbox, com PATH do Node 24 e cache uv em `/tmp` |
| API `uv run pytest` | 1578 passaram; 476 warnings de depreciação |
| API Ruff e mypy strict | Passaram; mypy em 79 arquivos |
| Web `npm test` | 120 passaram |
| Web build e typecheck | Passaram |
| Compose config pelo script | Passou; não iniciou serviços de trabalho |
| `test_web_migrations_postgres.py` | Passou na versão final: banco novo, adoção SQL 0001 e 0001/0002, dados preservados, downgrade não destrutivo, re-upgrade, estruturas divergentes e rollback atômico |
| `test_audit_migrations_postgres.py` | Passou com upgrade até a nova head e downgrade/re-upgrade bibliográfico |
| `test_editorial_migrations_postgres.py` | Passou, incluindo recusa de downgrade incompatível com eventos editoriais |
| Web `npm run test:integration` | Passou com preparação Alembic e PostgreSQL real |
| Web `npm run test:http` | Harness HTTP passou; administrativo foi inicialmente skip por variável ausente e executado separadamente depois |
| Web `tests/admin-api.e2e.ts` | Passou com PostgreSQL, Next e FastAPI reais; emissor simulado |
| Alembic `heads` | Única head `0005_web_auth` |
| Alembic `upgrade head --sql` | Gerado e aplicado com sucesso em banco descartável vazio |
| `git diff --check` | Passou |

## Ocorrências e limites

A primeira tentativa do script no sandbox foi bloqueada por `snap-confine`;
a execução autorizada fora do sandbox completou. A fixture inicial de legado
incluía uma tabela extra em `public`, corretamente detectada pelo `alembic check`;
foi movida para schema próprio de teste e a suíte repetida em banco vazio.
Um ensaio administrativo concorrente ao rebuild do Next falhou ao iniciar o
servidor; a repetição após o build, em outro banco vazio, passou.

O arquivo Next gerado pelo build foi restaurado ao conteúdo anterior para não
incluir alteração incidental. SQL históricos e relatórios anteriores foram
preservados. O container temporário foi encerrado após os testes; nenhum volume
de trabalho foi removido.

Não houve novo ensaio com Keycloak real, navegador, TLS público ou produção.
O harness Keycloak foi atualizado para usar Alembic, mas não foi executado.
O ambiente de trabalho continua dependendo da execução administrativa explícita
da migração após reconstruir a imagem API; esta verificação não declara o login
desse ambiente corrigido operacionalmente.
