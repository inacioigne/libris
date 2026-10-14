# Verificação do tema — 2026-10-14

Data: 2026-10-14, America/Manaus. Alteração visual local, com working tree já
modificado pelo usuário. Relatórios anteriores e mudanças preexistentes preservados.

## Mudanças

O `ThemeProvider` existente continua no layout de idioma. O modo resolvido agora
deriva da preferência e do sistema, sem um estado adicional atualizado em efeitos
encadeados. Preferências inválidas são descartadas; a chave legada `theme` continua
aceita. Falhas de armazenamento não impedem a aplicação do tema. O padrão permanece
claro e o modo `auto` acompanha `prefers-color-scheme`.

O Tailwind responde à classe `.dark`; corpo, foco, link de salto e componentes
existentes recebem cores escuras. Um select nativo com label em português/inglês
permite escolher Claro/Escuro/Sistema na página inicial e no cabeçalho administrativo.
Não foram adicionadas dependências nem alteradas regras de autenticação/autorização.

O teste existente de contraste aceita quebras de linha no CSS e também verifica as
cores de texto/foco escuros. O `<main>` administrativo já estava comentado e permanece
assim: esta entrega não restaura conteúdo ocultado pelas alterações preexistentes.

## Comandos e resultados

Node 24.16.0 foi usado pelo caminho local do nvm:

```bash
PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh
```

| Verificação | Resultado |
| --- | --- |
| `uv run pytest` | 1.668 passaram; 477 warnings; nenhum skip nesta suíte padrão |
| `uv run ruff check . ../../tests ../../scripts/verify-m04-integration.py` | Passou |
| `uv run mypy src` | Passou, 86 arquivos |
| `npm test` | 157 passaram, nenhum skip |
| `npm run build` | Passou |
| `npm run typecheck` | Passou |
| `docker compose --env-file .env.example config --quiet` | Passou, sem iniciar serviços |

A primeira tentativa no sandbox falhou ao iniciar o uv via Snap; a execução completa
fora do sandbox terminou com código zero. Nenhuma migração foi executada.

## Navegador

Uma instância temporária do build foi iniciada em `127.0.0.1:3197`, com
`WEB_AUTH_ENV=local` e `WEB_ORIGIN=http://localhost:3197`, usando `npm run start`.
Um harness temporário em `/tmp/libris-theme-browser.mjs`, via DevTools Protocol,
executou Chromium headless com perfil descartável. A instância e o perfil foram
encerrados/removidos ao final.

Resultado: passou. Cenários verificados:

- Alternar claro/escuro e conferir as cores computadas de corpo e cards.
- Recarregar e preservar a preferência salva.
- Escolher Sistema e emular mudanças claro/escuro do navegador.
- Escolher Claro explicitamente e manter a escolha mesmo com sistema escuro.
- Navegar de `/pt` para `/en` mantendo tema e traduzindo o seletor.
- Abrir `/en/admin` e conferir seletor e cor escura do cabeçalho.
- Recarregar com preferências inválidas, migrar a chave legada e usar armazenamento
  bloqueado; a troca permanece funcional.
- Nenhuma exceção JavaScript observada; nenhuma violação CSP observada.

Limites: o tema é aplicado após a hidratação, portanto pode aparecer brevemente
claro durante a carga inicial. Não houve nova homologação de login Keycloak,
PostgreSQL real, produção ou auditoria completa de acessibilidade. O teste de
navegador não exerceu o conteúdo administrativo oculto pelo `<main>` comentado.
