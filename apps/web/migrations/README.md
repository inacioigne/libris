# SQL histórico de sessões web

Os arquivos 0001/0002 são preservados para reproduzir bancos legados nos testes
de adoção. Não devem ser usados para novas instalações ou atualizações.

Desde o ADR 0034, execute explicitamente `uv run alembic upgrade head` em
`apps/api`, com `DATABASE_URL` administrativo apontando para o mesmo banco do BFF.
A revisão 0005 cria/adota as três tabelas no schema separado `libris_web`.
