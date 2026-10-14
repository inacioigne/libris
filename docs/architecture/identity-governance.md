# Governança de identidade e acesso — M04.06 / #39

Contrato vigente da governança e procedimento demonstrativo. Decisão:
[ADR 0032](../decisions/0032-identity-governance.md). Resultados desta execução:
[verificação M04.06](identity-m04-06-verification.md). M2M externo permanece
bloqueado; o contrato abaixo prepara uma integração futura, sem anunciar emissão
ou consumo operacional de credenciais técnicas.

## Responsabilidades e ciclo de vida

| Responsável | Autoridade e evidência |
| --- | --- |
| Instituição solicitante | Comprovar vínculo, finalidade, responsável, aprovação, papéis e prazo no procedimento administrativo restrito |
| Administrador delegado do provedor | Criar/localizar identidade, ativar/desativar, conceder/revogar client roles, recuperar credenciais e revogar sessões; eventos Keycloak |
| Equipe de segurança/identidade | Aprovar privilégios elevados, revisar concessões, delegação, retenção e políticas de autenticação do provedor |
| Keycloak/OIDC | Senhas, MFA/políticas, recuperação, autenticação, assinatura, emissão, refresh, desprovisionamento e trilha administrativa |
| FastAPI | Validar token e cliente, resolver permissões e aplicar Operation/POLICIES via AuthorizationGuard; sem administração de usuários |
| BFF Next.js | Code + PKCE, sessão cifrada servidor, refresh/logout e guard administrativo por /me; não concede roles |
| M03 bibliográfico | Autoria/proveniência e revisão imutáveis; não registrar administração de usuários como edição bibliográfica |

Usuário autenticado não se torna bf:Agent. Não há cadastro/senha paralelo no
Libris. `actor_id` é o hash versionado do par exato issuer/sub; nomes, e-mail e
vínculo não identificam o ator. Desativar/desprovisionar não apaga autoria; não
reutilizar um subject para outra pessoa. NULL histórico permanece NULL.

Ciclo: solicitação comprovada → aprovação → provisionamento/concessão mínima →
ativação e autenticação → revisão periódica → mudança/revogação → desativação →
retenção/desprovisionamento conforme política institucional. Alteração de função
exige retirar concessões antigas antes de adicionar as necessárias. Contas sem
responsável/vínculo vigente devem ser desativadas pelo provedor.

## Menor privilégio e aprovação

O mapa executável único é `identity/infrastructure/role_mapper.py`. Os seis papéis
e as 17 permissões permanecem iguais; múltiplos papéis somam concessões. Papel
unknown/ausente não concede nada. `system:admin` não substitui permissão funcional.
Não inferir acesso por nome, domínio de e-mail, prefixo de identificador ou payload.

| Papel no client libris-api | Quem aprova institucionalmente | Quem concede no provedor |
| --- | --- | --- |
| libris-reader | Responsável pelo serviço que necessita leitura autenticada | Administrador delegado de identidades |
| libris-cataloger | Coordenação de catalogação, com vínculo e atividade comprovados | Administrador delegado de identidades |
| libris-authority-manager | Responsável por autoridades/controladoria vocabular | Administrador delegado de identidades |
| libris-reviewer | Coordenação editorial, após habilitação para revisão | Administrador delegado de identidades |
| libris-publisher | Responsável institucional pela publicação | Administrador delegado de identidades |
| libris-admin | Responsável institucional pelo sistema e segurança, aprovação independente do executor | Administrador de identidade autorizado para concessão elevada |

Esta é política operacional proposta para adoção institucional, não um workflow
implementado no produto. `libris-admin` não concede acesso ao Admin Console do
Keycloak. Delegar administração do provedor separadamente, com menor escopo possível;
não entregar master/admin ou realm-admin a integrações ordinárias. Validar a
delegação no ambiente antes de usá-la; não foi automatizada nesta issue.

Revisar concessões ao menos trimestralmente e a cada mudança/desligamento: comparar
roles efetivas (inclusive grupos/composites) com aprovações vigentes, confirmar
responsável/prazo/finalidade, remover excedentes e registrar executor, aprovador,
momento UTC, resultado e próxima revisão. Privilegiados merecem revisão mensal.
Os intervalos são recomendações administrativas, sem scheduler implementado.

## Concessão e revogação

Conceder: localizar/criar a identidade no provedor; confirmar vínculo/aprovação;
selecionar os papéis mínimos; atribuir **client roles de libris-api** ao usuário;
obter nova autenticação ou refresh adequado; validar /me e operação backend;
conferir evento administrativo e registrar evidência restrita. Não adicionar papel
padrão ao realm, nem confiar em menus frontend como prova de autorização.

Revogar: identificar usuário, concessões diretas e herdadas; remover papéis no
client correto ou desabilitar a conta; encerrar sessões no provedor e invalidar
refresh conforme o provedor; encerrar sessão BFF quando disponível; verificar nova
emissão/refresh, operação negada e comportamento do token antigo. Registrar quem,
o quê, quando, resultado, sistema e limite residual. Se um grupo/composite ainda
conceder o papel, remover a fonte pertinente; não considerar só mappings diretos.

| Ação | Efeito verificável e limite |
| --- | --- |
| Revogação de papel | Novas emissões não devem conter a concessão; JWT anterior não muda |
| Desativação do usuário | Impede autenticação/renovação conforme provedor; JWT offline já emitido pode continuar válido |
| Expiração do access token | API recusa com 401 Bearer após exp mais OIDC_CLOCK_SKEW_SECONDS |
| Revogação do refresh token | Impede novas credenciais por esse refresh; não reescreve access token |
| Encerramento de sessão no provedor | Invalida sessão/refresh associados; outras sessões/offline tokens precisam avaliação própria |
| Logout BFF | Revoga sessão local e apaga cookie; RP logout pode encerrar sessão OIDC; não invalida globalmente JWTs |

A API valida JWT offline por JWKS; cache de chave não consulta estado do usuário.
Remover papel/desabilitar/logout não é revogação instantânea na API. O limite é
`exp` do token mais tolerância de relógio (default 30 s), assumindo relógios corretos.
Refresh negado faz o BFF exigir login; até seu próximo refresh ele pode usar token
ainda válido. O BFF atual não dispõe de painel de revogação remota de todas as
sessões; não editar tabelas manualmente como procedimento ordinário.

Recomendar access token curto (por exemplo cinco minutos), avaliar renovação,
concorrência, carga, perda de sessão e resposta a incidentes antes de mudar os
prazos. Esta entrega preserva tempos atuais do realm/BFF. O ensaio descartável
reduz expiração apenas em seu realm temporário para testar 401. Introspecção
obrigatória e denylist não foram introduzidas; exigiriam decisão própria.

## Fronteiras humana e técnica

Humano: JWT validado por TokenValidator, assinatura/issuer/audience/exp/typ e
`azp == OIDC_HUMAN_CLIENT_ID` (default libris-web). `azp` é claim **assinada** do
cliente que originou a emissão, não audience da API. O cliente confiável usa Code
+ PKCE, sem service accounts/direct grants/token exchange para impersonação.
Trocar WEB_OIDC_CLIENT_ID exige alinhar OIDC_HUMAN_CLIENT_ID no backend/Compose.
Outro provedor precisa garantir a mesma claim/semântica; não há fallback inseguro.
Essa configuração é confiança administrativa, não prova universal de presença humana.

Cliente ausente/desconhecido/serviço recebe 401 Bearer mesmo com libris-admin.
Headers/body/query não mudam a decisão. Subject é opaco; prefixo service-account
não classifica o ator. Um administrador comprometido capaz de reconfigurar o
cliente humano está fora da garantia da validação local.

Técnico interno: composition root confiável instancia TechnicalContext com
`service:<id>` ou `automated:<id>`, origem, permissões e operações fechadas.
AuthorizationGuard exige allowlist **e** permissões da mesma POLICIES. Não aceita
SYSTEM_ADMIN nem operações humanas de aprovação/publicação/submissão/restauração.
Autoria técnica nova é registrada pelos mecanismos M03; ExecutionActor isolado não
autoriza. Não deserializar esses objetos de solicitações externas.

Técnico OAuth externo: **não implementado**. Não há conversão de client_credentials
em HumanContext ou TechnicalContext e nenhum cliente de serviço habilitado no realm
versionado. Nenhum novo papel técnico foi necessário: não existe consumidor M2M.

Contrato para ativação futura, quando existir integração concreta:

- Cliente confidencial separado por finalidade, por exemplo `libris-service-import`,
  distinto de libris-web/libris-api; responsável, aprovação, prazo e inventário restrito.
- Client authentication e client_credentials, sem login/browser session, password
  grant, refresh token de usuário ou offline_access. Segredo exclusivo em secret
  manager/ambiente; jamais no JSON versionado, log ou NEXT_PUBLIC.
- Audience libris-api, issuer exato e access token assinado; `azp` do cliente técnico
  e `sub` da conta de serviço associados explicitamente no backend ao par emissor/
  cliente/subject esperado. Não confiar em client_id de request nem apenas em azp
  sem vinculação e política. Identidade externa estável por issuer/sub, separada
  dos IDs internos; rotação de segredo preserva a conta, recriação requer novo vínculo.
- Cadastro de **configuração de autorização**, não banco de usuários: capabilities,
  operações e origem fixadas pelo operador confiável. Negar cliente/subject não
  cadastrados, audience/issuer/exp inválidos, permissão ausente e ação fora da lista.
- Se houver papéis técnicos, mapeamento fechado separado do mapa humano, sem herdar
  libris-cataloger/admin; exigir interseção da concessão autenticada com a política
  interna. Reutilizar AuthorizationGuard/POLICIES; nunca uma segunda máquina.
- Sem SYSTEM_ADMIN ou decisões editoriais humanas. Diferentes serviços têm contas
  e autoria distintas; source/origin/process do payload não substituem a vinculação.
- Antes de habilitar: testes reais client_credentials positivos/negativos, rotação,
  revogação, autoria, clients trocados e impossibilidade de impersonar humano.

Provisionamento futuro no Admin Console: criar client OpenID Connect confidencial,
Client authentication ON, Service accounts roles ON; Standard/Implicit/Direct access
OFF; Full scope OFF; sem redirect/web origins. Configurar mapper aud=libris-api só
no access token e sub/azp assinados; atribuir somente concessão técnica aprovada.
**Manter cliente desabilitado até existir o adaptador e os testes acima.** Não
habilitar service accounts no cliente público web, nem adicionar serviço a
OIDC_HUMAN_CLIENT_ID. Gerar segredo no provedor, transferir por canal restrito.

Rotação: inventariar consumidores e proprietário, gerar credencial nova no provedor,
armazenar versão nova no secret manager, atualizar consumidor, testar autenticação
e capacidade mínima, invalidar credencial anterior conforme política/versão do
Keycloak e comprovar que ela falha. Registrar ID da credencial, nunca seu valor.
Revogação: desabilitar cliente, retirar concessões e invalidar credenciais/sessões
pertinentes; testar falha de nova emissão e expiração residual dos tokens antigos.
Overlap na rotação e revogação de secret anterior precisam ser verificados na versão
implantada. Este roteiro é contrato, não evidência de M2M executado.

## Vínculos institucionais futuros — M10/M11

Ator global issuer/sub independe de instituição. Um vínculo verificável terá ID
próprio, instituição, unidade/biblioteca pertinentes, função, vigência/status,
fonte autoritativa, aprovador e versão. Vários vínculos podem coexistir; revogar
um não apaga ator, outros vínculos nem autoria histórica. Instituição é entidade
administrativa, biblioteca é unidade de serviço e papel é capacidade funcional;
não são aliases, nem autoridades bibliográficas por consequência.

A fonte de vínculo será um cadastro institucional/IdP governado, com validação no
backend e política por recurso; claims assinadas ainda precisam contrato de
proveniência/atualização/revogação. Campos institution_id de request ou domínio de
e-mail não provam vínculo. Selecionar contexto não pode ampliar os vínculos do ator.
Ainda precisam ser definidos conflitos, escopos de recurso, visibilidade e revisão.

Não há multi-tenancy, filtros institucionais, tabelas de tenant, isolamento por
schema ou proteção cruzada implementados. As permissões atuais não devem ser
interpretadas como autorização institucional para todos os rascunhos. O guard
atual exige capacidades editoriais/histórico, mas não verifica propriedade nem
instituição: não expor coleção multiinstitucional antes dessa implementação.

## Roteiro administrativo reproduzível — Keycloak 26.8.0

Use instância **nova e descartável**, porta livre diferente de 8081, sem volumes de
trabalho, com realm libris importado do JSON. Não basta nomear usuário de teste no
realm de trabalho: o teste de expiração altera configuração do realm descartável.
O procedimento M04.02 em [Keycloak local](identity-keycloak-local.md) complementa
PKCE/DNS. Não parar serviços de terceiros para liberar porta.

1. Gerar usuário/senha administrativos aleatórios fora do Git em arquivo privado
   (umask 077, modo 0600); não usar `set -x`, gravar tokens ou imprimir respostas.
2. Subir Keycloak novo em tmpfs com `--import-realm`, `KC_HOSTNAME` igual ao issuer
   de teste (exemplo http://keycloak.localhost:18081), publicação loopback e nome
   exclusivo. Imagem de referência igual ao Compose. Sem reutilizar volume.
3. Entrar no Admin Console desse host/porta, selecionar **libris**. Confirmar que
   Users está vazio e clients são libris-api e libris-web; confirmar PKCE/service
   accounts OFF no web. Conferir Tokens antes de mudar tempos.
4. Realm settings → Events → Admin events settings: Save events ON, Include
   representation OFF. O JSON já os configura para importação inicial. Em Events
   → Admin events conferir operação, recurso, authDetails/ator, momento e erro.
5. Users → Add user: identificador sintético único, Enabled ON; completar campos
   obrigatórios e definir credencial efêmera em Credentials. Senhas/recuperação/MFA
   continuam no provedor. Não adicionar usuários/credenciais ao JSON versionado.
6. Users → usuário → Role mapping → Assign role → filtrar clients → libris-api →
   libris-cataloger. Conferir effective roles e fontes herdadas. Registrar aprovação
   e ID não secreto do papel em evidência administrativa restrita.
7. Autenticar com libris-web por Code + PKCE; executar GET /api/v1/identity/me com
   Bearer em memória por ferramenta/harness privado. Esperar actor_id estável,
   roles e permissões; nunca copiar JWT em URL, issue, screenshot ou log. /health
   é público. O endpoint funcional `/probe/create` do harness existe só no teste.
8. Remover libris-cataloger de Role mapping. Nova emissão deve ter permissões
   vazias; /me 200 com mesma identidade e operação protegida 403. Token anterior
   ainda pode dar 200 na operação. Reatribuir papel só com aprovação pertinente.
9. Users → Sessions → Logout all sessions. Conferir refresh anterior recusado.
   Desabilitar em Details → Enabled OFF e salvar; verificar login/refresh negados.
   JWT anterior ainda pode passar na API até expiração. Reativar somente se aprovado.
10. Para expiração rápida, somente no realm descartável: reduzir access token
    lifespan, emitir novo token, esperar exp mais skew, verificar 401 e
    WWW-Authenticate: Bearer. Não alterar prazos de instância de trabalho.
11. Consultar Admin events e o registro restrito da aprovação: concessão/removal,
    disable/enable/logout, ator, hora UTC e resultado. Não habilitar representação
    para obter mais detalhes de credenciais.
12. Limpeza: excluir somente IDs de usuário/client/recursos registrados como criados
    pela execução. Encerrar apenas o container descartável pelo nome exato; tmpfs
    desaparece. Remover arquivos privados e credenciais efêmeras. Não apagar eventos,
    volumes ou realm compartilhados. A evidência sanitizada permanece no relatório.

Para execução automatizada, `tests/integration/keycloak_governance_harness.py`
reutiliza o login PKCE real. Requer ambiente privado com KEYCLOAK_ADMIN_USERNAME e
KEYCLOAK_ADMIN_PASSWORD da instância descartável, TEST_KEYCLOAK_ISOLATED=1,
TEST_KEYCLOAK_GOVERNANCE=1 e TEST_KEYCLOAK_ISSUER explícito terminando em
/realms/libris. O harness modifica somente usuário criado por ele e lifespan do
realm descartável. Não imprime respostas/segredos e apaga seu usuário em finally.
As flags são confirmação operacional de isolamento, não um controle contra um
operador privilegiado que forneça endereço errado.

```bash
# No shell privado já configurado para a instância recém-criada:
cd apps/api
uv run pytest -c pyproject.toml ../../tests/integration/test_keycloak_oidc.py -k governance -s
```

Instâncias persistidas: importação no startup **não sobrescreve** realm existente.
Aplicar eventos pelo Admin Console (passo 4), conferir ausência de service accounts
no web e alinhar OIDC_HUMAN_CLIENT_ID ao cliente interativo real. Não apagar volume
para aplicar JSON. Se usar kcadm.sh, autenticar com config privada (`--config` em
arquivo 0600), usar o realm explícito em cada comando, sem `-s` contendo senhas
na linha de comando, e não exportar realm com segredos. Exemplo de atualização
não secreta, após autenticação privada e conferência do realm correto:

```bash
kcadm.sh update realms/libris --config "$PRIVATE_KCADM_CONFIG" \
  -s adminEventsEnabled=true -s adminEventsDetailsEnabled=false
```

## Auditoria, evidências e limites

| Fonte | O que comprova | Limite |
| --- | --- | --- |
| Eventos administrativos Keycloak | Ator administrativo/authDetails, instante, operação, recurso e erro | Sem representação, role/credential exata pode exigir registro restrito complementar |
| Registro administrativo institucional | Solicitante/aprovador/executor, usuário alvo por ID restrito, papel/ID de credencial, data, motivo, resultado e referência ao evento | Procedimento externo, sem workflow automatizado no Libris |
| API | Rejeição OIDC genérica 401 e autorização 403; logging operacional existente | Não é trilha completa de concessão/revogação nem ledger de segurança |
| BFF | Resultado de sessão/login/logout e guard atual | Sem trilha administrativa ampliada; #41 |
| M03 | Ator e proveniência da revisão/ação bibliográfica | Não documenta administração de identidade |
| #41 futura | Correlação e auditoria de segurança ampliada | Sem novo banco/logging/event bus nesta entrega |

Definir retenção de eventos, backups, acesso restrito e expurgo com os responsáveis
da implantação; não pressupor retenção infinita ou durabilidade de um tmpfs. Events
ON sem Include representation reduz exposição, mas IDs/IPs e metadados ainda exigem
controle de acesso e minimização. Evidência compartilhável contém apenas contagens,
status, etapas e referência restrita, sem tokens, senhas, secrets ou PII desnecessária.

Matriz de validação: testes offline de assinatura/issuer/aud/exp, papéis, múltiplos
papéis, spoof HTTP, cliente assinado, mudança entre emissões e JWT residual em
`test_identity.py`; guard técnico/allowlist/editorial/admin e contratos M03 na suíte
existente; teste real de governança opcional no harness. Cenários M2M positivos,
rotação de segredo e classificação externa não foram executados, pois o consumidor
não está implementado. Resultados, falhas/skips e critérios estão no relatório.

Referências primárias consultadas: [administração e eventos Keycloak](https://www.keycloak.org/docs/latest/server_admin/index.html#_events)
e [contas de serviço Keycloak](https://www.keycloak.org/docs/latest/server_admin/index.html#_service_accounts).
A documentação latest pode evoluir; confirmar os controles na versão implantada.
