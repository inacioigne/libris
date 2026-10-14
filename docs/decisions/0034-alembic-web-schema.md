# ADR 0034 — Alembic como executor único de migrações

Data: 2026-10-14. Estado: aceito para implementação local.
Atualiza a execução de migrações definida nos ADRs 0030 e 0033; não altera os
contratos de sessão, OIDC ou os modelos bibliográficos experimentais.

## Contexto

Dois executores administrativos deixaram a migração de quotas web pendente em um
ambiente Compose com serviços saudáveis. O build não instala tabelas, e o BFF
recusa login quando a tabela de quotas não existe. Alguns bancos já receberam
os SQL web 0001 ou 0001/0002, sem histórico Alembic para essas tabelas.

## Decisão

O comando explícito `uv run alembic upgrade head`, em `apps/api`, passa a preparar
também o BFF. A revisão incremental 0005, após 0004_semantic_editorial, cria/adota
`auth_transactions`, `sessions` e `auth_quotas` no schema separado `libris_web`.
As definições ficam congeladas na revisão, sem importar código ou arquivos web.
Não há migrações no startup nem modelos ORM de sessões na API.

Tabelas existentes são comparadas com definições de referência temporárias no
próprio PostgreSQL: colunas/tipos/nullability/defaults, constraints e índices.
Objetos incompatíveis, RLS e triggers de usuário abortam a transação; a revisão
não é marcada como aplicada. Índices de expiração ausentes são criados. Tabelas
compatíveis são preservadas, incluindo ciphertext, prazos e contadores; não há
reescrita de dados ou mudança de grants/proprietários de objetos existentes.
Os SQL históricos ficam apenas como fixtures dos testes de adoção. O executor
`session:migrate` do frontend é removido.

O downgrade de 0005 para 0004 mantém deliberadamente schema, tabelas e dados web,
pois a adoção não distingue sessões anteriores e posteriores ao Alembic. O
re-upgrade valida/adota novamente. Desinstalação destrutiva, se necessária, exige
procedimento administrativo separado; não se executa em banco de trabalho.
Downgrades anteriores a 0004 conservam seus riscos e proteções históricos.

## Operação e limites

`DATABASE_URL` administrativo e `WEB_SESSION_DATABASE_URL` de runtime apontam
para o mesmo banco, com drivers/credenciais apropriados. O primeiro usa asyncpg;
o segundo usa pg nativo. Instalações com bancos separados precisam consolidar
explicitamente os dados antes de adotar este fluxo; alterar apenas uma URL não
transfere sessões. Não usar `alembic stamp head` para contornar uma adoção falha.
Um banco web antigo sem cadeia Alembic recebe também as migrações bibliográficas
experimentais; essas tabelas continuam em `public` e sem acesso pelo BFF.

O papel de migração tem DDL e permissão TEMP no banco; o runtime web continua
com DML apenas em `libris_web`. O Alembic administra DDL, sem autorizar módulos
a acessar dados de outros módulos. O autogenerate da API continua limitado aos
modelos bibliográficos em `public`; futuras alterações web exigem revisões
explícitas. As migrações históricas 0001–0004 não são alteradas.

Testes PostgreSQL descartáveis cobrem instalação nova, adoção 0001/0002,
preservação de dados, rollback/re-upgrade e recusa atômica de estruturas divergentes.
Os harnesses web passam a preparar seus bancos usando o Alembic real.
