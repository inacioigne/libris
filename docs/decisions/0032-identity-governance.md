# ADR 0032 — Governança externa e fronteira do cliente humano

Data: 2026-10-13. Estado: aceito para implementação local M04.06 / #39.

## Contexto

As ADRs 0016, 0030 e 0031 estabelecem Resource Server, BFF e guard por operação.
TechnicalContext configura execução interna confiável, sem autenticar OAuth M2M.
IdentityService ainda aceitava qualquer cliente emissor de um token válido para a
API, inclusive um cliente técnico que recebesse indevidamente papéis humanos.
A #39 exige projetar identidade técnica, procedimentos e revogação; não exige um
consumidor operacional client_credentials nem antecipar APIs M05.

## Decisão

Manter ciclo de vida humano, credenciais e concessões no provedor externo.
Após validação JWT/JWKS, exigir `azp` assinado igual a OIDC_HUMAN_CLIENT_ID
(padrão libris-web) para construir AuthenticatedActor e entrar em HumanContext.
Ausência, tipo incorreto e qualquer outro cliente recebem AuthenticationError/401
Bearer. Audience libris-api continua obrigatória e independente de azp.
Não inferir categoria por sub, e-mail, roles, headers ou campos de proveniência.

O cliente interativo confiável deve permanecer público, Code + PKCE S256, sem
service accounts, direct grants ou token exchange/delegação que permita impersonação
por serviços. azp identifica o cliente; não é prova universal de presença humana.
A configuração do provedor e o adaptador TokenValidator são parte da confiança.
Outro provedor precisa emitir contrato equivalente de azp; não haverá fallback
para tokens sem vinculação. Implantação existente deve alinhar WEB_OIDC_CLIENT_ID
e OIDC_HUMAN_CLIENT_ID explicitamente antes de mudar o cliente web.

M2M permanece fechado no boundary HTTP. Registrar contrato futuro para clients
confidenciais separados, credenciais por finalidade, identidade estável issuer/sub,
vinculação administrativa exata issuer/azp/sub e allowlist de permissões/operações.
Nenhum papel técnico, cliente de serviço habilitado ou segundo mapa de políticas é
necessário agora. Quando houver consumidor, seu adaptador deverá produzir
TechnicalContext e reutilizar AuthorizationGuard/POLICIES, sem promoção a humano.

Habilitar eventos administrativos Keycloak sem representação de requisições.
Evidência complementar restrita registra papel/credencial afetados sem segredos;
retenção e delegação administrativa são decisões da implantação.

## Consequências e alternativas

Preservados os seis papéis/17 permissões, /me, 401/403, CAS, revisão e auditoria M03.
Nenhuma tabela local de usuário, migração ou novo endpoint. Tokens de clientes antes
aceitos incidentalmente passam a ser rejeitados: ajuste intencional de confiança,
sem alteração do DTO/Problem Details v1. Instâncias já persistidas não são atualizadas
pela importação de realm; requerem configuração administrativa explícita.

A validação offline conserva concessões de JWT pré-emitido até expiração mais
clock skew. Não introduzir introspecção obrigatória/denylist sem decisão própria.
Emitir M2M agora não teria operação HTTP consumidora e ampliaria desnecessariamente
a superfície; confiar apenas em roles humanas perpetuaria a lacuna.

[Contrato e procedimento](../architecture/identity-governance.md).
