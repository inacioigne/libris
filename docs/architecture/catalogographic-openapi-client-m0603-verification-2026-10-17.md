# Verificação M06.03 — cliente TypeScript OpenAPI catalográfico — 2026-10-17

## Contexto

Esta execução valida a geração reproduzível de tipos e cliente HTTP para a API catalográfica via OpenAPI real e versionada do projeto. A entrega preserva as baselines já verificadas na M06.01 e usa a especificação oficial em `docs/architecture/catalogographic-openapi-v1.json` como fonte única.

## Implementação

- Gerador em `apps/web/scripts/generate-catalogographic-client.ts`
- Artefatos gerados em `apps/web/src/generated/catalogographic-openapi.ts` e `catalogographic-client.ts`
- Teste de regressão em `apps/web/tests/openapi-client.test.ts`
- `npm run openapi:generate` e `npm run openapi:check` adicionados ao `apps/web/package.json`
- `npm test` agora executa a checagem de drift antes da suíte web
- CI atualizado em `.github/workflows/catalogographic-contract.yml` para rodar a verificação web junto com os checks API

## Limites e escolha técnica

- Preferimos `openapi-typescript` para produzir tipos TS estritos e `openapi-fetch` para o cliente HTTP, combinados com um adaptador mínimo para aceitar `Accept: application/json` e preservar `cache: no-store` em uso no web app.
- Evitamos duplicar DTOs em código manual; os artefatos gerados são considerados de produção, com instrução explícita de regeneração e não edição manual.
- Manteremos as operações reais e modelos em `catalogographic-openapi-v1.json`; nenhuma camada de cliente é tratada como substituta da API, apenas como bridge tipado e reproduzível.

## Execuções realizadas

Todos os comandos abaixo foram executados com Node 24 em `/home/inacio/.nvm/versions/node/v24.16.0/bin` e com a raiz do repositório em `/home/inacio/dev/libris`.

1. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm install --ignore-scripts`
   - Resultado: dependências instaladas; `apps/web/package-lock.json` atualizado com `openapi-typescript` e `openapi-fetch`.

2. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH node --import tsx scripts/generate-catalogographic-client.ts`
   - Resultado: generation bem-sucedida dos arquivos em `src/generated/`.

3. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm run openapi:check`
   - Resultado: `Catalogographic OpenAPI client is up to date.`

4. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm test`
   - Resultado: 168 testes aprovados, 0 falhas.

5. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm run build`
   - Resultado: build de produção concluído com sucesso.

6. `cd apps/web && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH npm run typecheck`
   - Resultado: TypeScript strict sem erros.

7. `cd /home/inacio/dev/libris && PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh`
   - Resultado: API e web passaram; o script finalizou com sucesso após o restante do pipeline do backend.

## Observações finais

- A geração não altera a baseline OpenAPI ou os contratos de domínio; falha de drift é tratada como erro de qualidade.
- A suíte web passou sem skips, e o build final validou a integração com Next.js 16.
- A API backend foi revalidada pelo `scripts/check.sh`, preservando a baseline e a cobertura existente sem depender de banco de trabalho ou ambiente externo.
