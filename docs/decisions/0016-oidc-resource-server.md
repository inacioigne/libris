# ADR 0016 — Resource Server OIDC e permissões internas

Status: aceito para Entrega A do Incremento 2, fase 3

Data: 2026-10-10

## Contexto

O monólito precisa identificar atores sem armazenar senhas ou emitir tokens.
Revisões experimentais já conservam origem, processo e perfil; falta identidade
autenticada. Entregas B–E não fazem parte desta mudança.

## Decisão

Criar o módulo identity, com domínio imutável independente de HTTP, serviço de
identificação e adaptador OIDC assíncrono. PyJWT com cryptography valida a assinatura;
HTTPX recupera descoberta e JWKS. Instâncias pertencem ao lifespan da aplicação,
com dependências FastAPI substituíveis. `/health` permanece público;
`/api/v1/identity/me` exige autenticação, mesmo com OIDC desabilitado.

Emissor é string exata, sem normalização de identidade. Exigir assinatura,
algoritmo assimétrico da allowlist, kid compatível, iss, aud, exp, sub não vazio,
nbf/iat quando presentes e discriminador assinado de access token. Por padrão,
Keycloak usa a claim de payload typ=Bearer. Não confiar somente no typ do header.
Outro provedor precisa configurar uma claim equivalente e uma audiência exclusiva
para a API. Não aceitar tokens sem esse discriminador. URLs jku/x5u do token
não participam da resolução de chaves; redirects HTTP não são seguidos.

JWKS tem TTL, lock assíncrono e intervalo mínimo global de atualização por
instância, incluindo falhas. kid desconhecido provoca tentativa limitada.
Não usar chaves expiradas na falha do provedor. Documentos são limitados a 1 MiB;
JWT a 16 KiB; JWKS a 100 chaves. Cache é local ao processo; múltiplos workers têm
caches independentes. Descoberta ocorre sob demanda e fica válida durante o
lifespan; mudança de URI publicada exige reiniciar a aplicação.

Papéis vêm exclusivamente de claims validadas: resource_access do client
configurado por padrão; realm_access somente por configuração explícita.
Mapeamento é centralizado e deny by default; admin é concessão explícita.
Permissões internas não dependem dos nomes de papéis externos.

actor_id = `oidc:sha256:` + SHA-256 hexadecimal dos bytes UTF-8 de
`json.dumps([issuer, subject], ensure_ascii=False, separators=(",", ":"))`.
Não normalizar URLs, Unicode ou subject; não usar e-mail/nome. O prefixo versiona
a convenção e deve permanecer estável. O hash distingue pares sem concatenação
ambígua; não promete anonimização de identidades conhecidas.

Serviços bibliográficos recebem opcionalmente AuthenticatedActor por argumento
nomeado do chamador confiável. Revisão guarda apenas actor_id, separado da
proveniência técnica. Migração 0002 adiciona coluna nullable, sem backfill;
revisões antigas e operações técnicas sem ator ficam NULL. NULL não prova que
uma operação é automatizada; a classificação futura de atores de serviço e
históricos será definida em outra entrega. Não há schema HTTP que aceite ator
do cliente, auditoria completa, autorização interna das operações técnicas ou
novo endpoint catalográfico.

## Alternativas

Autenticação própria duplicaria o provedor. Verificar apenas decodificação ou
buscar URLs do JWT permitiria identidades sem confiança. Realm roles implícitas
ampliariam privilégios. UUID aleatório impediria rastreabilidade estável.
BibliographicService não acessa tabelas do módulo identity; não existe cadastro
local de usuários nem FK para um provedor externo.

## Consequências

Indisponibilidade sem chave confiável gera 401 genérico, com evento operacional
nos logs; rejeições normais são debug. Token/claims/credenciais não são registrados
pelo adaptador. API não faz chamadas OIDC no startup. Produção exige HTTPS tanto
no emissor quanto no JWKS. OIDC desabilitado nunca libera operações protegidas.
Rotação pode exigir aguardar o intervalo mínimo após a última atualização.
Keycloak local é overlay opcional; hostname compartilhado mantém iss consistente.

Referências: [PyJWT](https://pyjwt.readthedocs.io/en/latest/api.html),
[containers Keycloak](https://www.keycloak.org/server/containers),
[hostname Keycloak](https://www.keycloak.org/server/hostname).
