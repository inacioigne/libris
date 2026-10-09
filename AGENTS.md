# Convenções do Libris

Leia README.md, docs/architecture e docs/decisions antes de alterar a arquitetura.
Esta fase contém infraestrutura somente; não acrescentar funcionalidades fictícias.

- Monólito modular. Módulos futuros em apps/api/src/libris/modules/<domínio>.
- Separe api, application, domain e infrastructure quando houver código que justifique
  essas camadas. Domínio não importa FastAPI nem acessa HTTP.
- Um módulo não acessa repositórios/tabelas de outro; use serviços e contratos explícitos.
- BIBFRAME Work/Instance/Item não se confunde com exemplar administrativo ou empréstimo.
- PostgreSQL é fonte de verdade; Elasticsearch é projeção reconstruível.
- Não introduza microsserviços, triplestore, filas ou abstrações sem ADR e necessidade.
- Python >=3.13,<3.15; ambiente de referência 3.13. SQLAlchemy 2 async e Pydantic 2.
- Tipagem Python obrigatória, TypeScript strict; nomes de código em inglês,
  documentação em português. Não usar Any para contornar erros sem justificativa.
- Serviços transacionais controlam commit/rollback; rotas não contêm regras de negócio.
- Migrações Alembic revisadas; nunca create_all na inicialização. Não criar tabelas
  bibliográficas definitivas nesta etapa.
- Configuração via ambiente; não versionar .env, credenciais, dados pessoais ou caches.
- Não expor segredos por NEXT_PUBLIC_*. Traduções em src/i18n/messages.ts.
- Preferir HTML semântico e primitivas Radix UI; usar shadcn/ui quando houver controles complexos reais.
- Atualize uv.lock/package-lock.json junto das dependências; Docker usa locks.
- Execute scripts/check.sh, ou as partes disponíveis; informe resultados e limites
  observados. Testes da API não exigem PostgreSQL/Elasticsearch.
- Testes de integração futuros devem usar PostgreSQL, não SQLite como substituto.
- Preserve arquivos existentes. Nunca afirme que serviços ou testes passaram sem execução.
- Novas decisões estruturais exigem ADR. Não escolha licença do projeto unilateralmente.
