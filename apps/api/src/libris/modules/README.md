# Módulos

`bibliographic` contém a fundação semântica experimental M02 e os contratos,
serviços internos e persistência editorial da M03. Consulte
`docs/architecture/semantic-foundation.md`,
`docs/architecture/catalogographic-contract.md` e
`docs/architecture/editorial-persistence.md`. As tabelas continuam experimentais;
não há endpoints CRUD catalográficos públicos nem editor.

`identity` contém o Resource Server OIDC inicial da M04 (validação JWT/JWKS,
permissões e `/api/v1/identity/me`). Consulte `docs/architecture/identity.md`.
O login Next.js e a homologação Keycloak real permanecem pendentes.

As demais fronteiras estão em `docs/architecture/domains.md`. Só crie módulos e
camadas quando houver casos de uso aprovados; inventário, circulação e gestão
de autoridades continuam futuros.

`security_audit` contém o contrato transversal M04.08, a interface de observação
injetável e a emissão JSON de eventos de segurança. Não possui tabelas/endpoints
nem substitui a auditoria bibliográfica M03. Consulte
`docs/architecture/security-audit.md` para correlação, privacidade e limites de
retenção/durabilidade. O BFF existente participa pelo contrato server-only;
homologação operacional permanece separada.
