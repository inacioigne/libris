# Verificação — M04.01 / #34

Data: **2026-10-13**, America/Manaus. Avaliação local da branch `main`, HEAD
`21f055ac5b7eb4130bc62068512f2739f54b8414`, working tree inicial limpo.
Este relatório registra esta execução; não sobrescreve evidências históricas.

## Entrega e fontes

Criados [baseline](security-baseline.md), [modelo de ameaças](security-threat-model.md),
[matriz de acesso](security-access-matrix.md) e
[checklist de saída](security-m04-exit-criteria.md), além deste relatório separado.
Acrescentados somente links em README, overview e identity. Nenhum código, contrato,
perfil, shape, migration, dependência, lock ou ADR foi alterado. Nenhum ADR novo:
consolidação das decisões existentes, sem decisão arquitetural nova.

Investigação leu instruções/arquitetura e fontes obrigatórias, implementadores
identity/bibliographic, App Router, configuração Keycloak/Compose, migrações e
testes de identidade/editorial/auditoria/startup e PostgreSQL relacionados.
GitHub consultado somente para leitura: #34, #27/#28/#43, #30/#31 e #35–#42,
com estados/milestones discriminados na baseline. Não houve modificação remota.

## Comandos e resultados atuais

Ferramentas existentes: Python **3.13.15**, Node.js **24.16.0** via NVM.
O npm não estava no PATH inicial; foi usado
`PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH` nos comandos frontend/check.
Nenhuma ferramenta/dependência foi instalada para esta entrega.

| Comando efetivamente executado | Resultado observado |
| --- | --- |
| `git status --short`; `git branch --show-current`; `git log -12 --oneline`; `git rev-parse HEAD` | estado inicial limpo, main, HEAD acima |
| `cd apps/api && uv run pytest ../../tests/api/identity` no sandbox | exit 1: uv Snap bloqueado por snap-confine/permissões; não executou testes |
| Mesmo comando fora do sandbox | **51 passed**, 1 warning, 8,10 s; RSA local/MockTransport |
| `cd apps/api && uv run pytest` fora do sandbox | **1.235 passed**, 465 warnings, 131,59 s; suíte padrão sem serviços externos |
| `cd apps/api && uv run ruff check . ../../tests` fora do sandbox | passou, All checks passed |
| `cd apps/api && uv run mypy src` fora do sandbox | passou, 76 arquivos |
| `cd apps/web && npm run build` com Node 24 no sandbox | exit 1: erros de stream fd/Operation not permitted e Could not parse output from TypeScript's --showConfig |
| `cd apps/web && npm run typecheck` com Node 24 no sandbox | exit 0, com avisos de stream fd do ambiente |
| `docker compose --env-file .env.example config --quiet` | passou; apenas validação estática, não inicializou serviços |
| `PATH=/home/inacio/.nvm/versions/node/v24.16.0/bin:$PATH bash scripts/check.sh` fora do sandbox | **exit 0**, completo: 1.235 testes passaram (465 warnings, 145,62 s), Ruff, mypy (76 arquivos), build Next.js, typecheck e validação Compose passaram |
| `cd apps/api && env -u TEST_DATABASE_URL -u TEST_MIGRATION_DATABASE_URL -u TEST_EDITORIAL_MIGRATION_DATABASE_URL uv run pytest -c pyproject.toml ../../tests/integration -m integration` fora do sandbox | **55 skipped**, 1,85 s; sem URLs/serviços, nenhuma prova de integração PostgreSQL |
| `apps/api/.venv/bin/python` com conferência pontual de documentação (na raiz) | passou: 17 permissões, seis papéis e todas as concessões iguais ao enum/mapa, 24 IDs em duas tabelas, 144 links locais existentes e contagem de colunas das tabelas coerente |
| `git diff --check` | passou, sem saída |

O build que falhou no sandbox passou na execução completa de check.sh fora dele;
não foi necessário alterar código/configuração para resolver essa restrição.

Avisos da suíte API: depreciação Starlette/httpx no TestClient e
RDFLib/ConjunctiveGraph. Não foi alterada dependência para suprimi-los.

## Cobertura, limites e decisões de teste

Os testes existentes já cobrem 401/403, /health público, união/papéis desconhecidos,
claims/assinatura/cache OIDC, matriz editorial e histórico autorizado. Não foram
duplicados. A matriz Markdown continua referência humana única nesta entrega;
verificação pontual compara seus valores/concessões ao enum/mapa em execução, sem
criar infraestrutura de autorização ou segunda matriz normativa estruturada.

Lacunas identificadas: documentos/chaves JWKS excessivos, key_ops, redirects/x5u/proxy,
todos os algoritmos permitidos, unknown-role especificamente no HTTP, ausência de
ator em toda operação obrigatória e falhas inesperadas da dependência identity não
possuem cobertura dedicada identificada. TH01–TH24 e #42 discriminam essas lacunas.
Critério documentado não é proteção testada por pressuposição.

**Keycloak real e PostgreSQL real não foram executados nesta tarefa documental.**
Não foi provisionada instância descartável nem usada URL de banco de trabalho.
Testes físicos foram inspecionados e referenciados; relatórios anteriores permanecem
evidência histórica. Não houve startup, migração, downgrade, remoção de volumes ou
mutação em qualquer banco. Coleta com variáveis de teste removidas só demonstra skips,
nunca aprovação de integração. Build/typecheck não validam login inexistente.

Mermaid foi revisado quanto a sintaxe básica/subgraphs/links e estados das fronteiras;
renderização GitHub não foi executada localmente. Links relativos, tabelas Markdown,
IDs de ameaça e concessões recebem verificação pontual, discriminada abaixo.

## Aceitação e próximos passos

Entregas locais da #34 são documentais e revisáveis: inventário real, ADR 0016,
contratos M03, oito fronteiras, 24 ameaças, fail closed, 17 permissões/seis papéis,
operações editoriais, dependências M04 e capacidades diferidas M05–M15.
Revisão/aceitação pelo mantenedor e eventual fechamento de #34 são externos a esta
execução; o GitHub permanece inalterado. As integrações/login/RBAC geral/HTTP/
governança/eventos de segurança/homologação pertencem às #35–#42 e entregas posteriores,
não são pendências de implementação ocultas desta issue documental.

Branch original preservada; nenhuma branch criada, commit, push, PR, merge, rebase,
reset/restore/clean ou sincronização remota. Alterações permanecem locais sem commit.

## Estado final do Git

`git branch --show-current`: `main`. HEAD permanece o mesmo da avaliação inicial.
`git status --short`:

```text
 M README.md
 M docs/architecture/identity.md
 M docs/architecture/overview.md
?? docs/architecture/security-access-matrix.md
?? docs/architecture/security-baseline.md
?? docs/architecture/security-m04-01-verification.md
?? docs/architecture/security-m04-exit-criteria.md
?? docs/architecture/security-threat-model.md
```

`git diff --stat` (somente rastreados):

```text
 README.md                     | 4 ++++
 docs/architecture/identity.md | 8 ++++++++
 docs/architecture/overview.md | 6 ++++++
 3 files changed, 18 insertions(+)
```

Os cinco documentos novos são não rastreados e, por isso, não aparecem nesse stat.
`git diff --check` passou. Não havia alterações preexistentes a preservar além dos
arquivos existentes; nenhuma operação destrutiva foi usada.

## Reprodução da conferência documental

Executar na raiz com o ambiente Python já instalado, sem serviços externos:

```bash
apps/api/.venv/bin/python - <<'PY'
from pathlib import Path
import re
from libris.modules.identity.domain.permissions import Permission
from libris.modules.identity.infrastructure.role_mapper import ROLE_PERMISSIONS

root = Path.cwd()
files = list((root / 'docs/architecture').glob('security-*.md'))
files += [root / 'README.md', root / 'docs/architecture/overview.md',
          root / 'docs/architecture/identity.md']
links = 0
for path in files:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (path, target)
        links += 1
roles = ['libris-reader', 'libris-cataloger', 'libris-authority-manager',
         'libris-reviewer', 'libris-publisher', 'libris-admin']
rows = {}
matrix = (root / 'docs/architecture/security-access-matrix.md').read_text()
for line in matrix.splitlines():
    match = re.match(r'^\| `([^`]+)` \|', line)
    if match:
        cells = [value.strip() for value in line.split('|')[2:-1]]
        assert len(cells) == 6
        rows[match[1]] = {role for role, cell in zip(roles, cells) if cell == 'sim'}
assert set(rows) == {p.value for p in Permission}
assert set(roles) == set(ROLE_PERMISSIONS)
for permission, actual in rows.items():
    assert actual == {role for role, perms in ROLE_PERMISSIONS.items()
                      if Permission(permission) in perms}, permission
threats = (root / 'docs/architecture/security-threat-model.md').read_text()
ids = re.findall(r'^\| (TH\d+) \|', threats, re.M)
assert len(ids) == 48 and all(ids.count(f'TH{i:02}') == 2 for i in range(1, 25))
for path in files[:5]:
    previous = None
    for line in path.read_text().splitlines():
        if line.startswith('|'):
            count = line.count('|')
            assert previous in (None, count), (path, line)
            previous = count
        else:
            previous = None
print(f'OK: {len(Permission)} permissões, {len(roles)} papéis, '
      f'24 ameaças em duas tabelas, {links} links locais e tabelas coerentes.')
PY
```

A conferência verifica destinos locais, não âncoras Markdown nem URLs externas.
Não substitui revisão semântica das operações, severidades ou renderização Mermaid.
