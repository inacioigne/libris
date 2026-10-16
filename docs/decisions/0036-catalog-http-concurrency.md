# ADR 0036 — Escrita HTTP catalográfica e precondição de edição

Data: 2026-10-16. Status: implementado tecnicamente para M05.03 / #47.

## Contexto

A #46 fornece Create/PATCH DTO sobre Graph; a #43 oferece transações, gate
shared/exclusive, snapshots, CAS e estado editorial independente. O HTTP precisa
vincular um validador da representação à revisão e versão editorial observadas,
sem transformar concurrency_token em ETag nem exigir leitura de auditoria.
Resolver referências locais durante escritas DTO também pode causar locks cruzados
se duas transações mantiverem FOR UPDATE em origens distintas e solicitarem
FOR KEY SHARE uma da outra sob gate shared.

## Decisão

CatalogService especializa BibliographicService e compartilha os passos `_create`
e `_revise`, stores e guard. Cada caso de uso possui uma única session.begin;
nenhuma transação HTTP externa envolve operações que já controlam transações.
A criação histórica conserva a assinatura e a validação anterior à transação.
O caso DTO resolve referências e valida/projeta dentro de sua própria transação.

Leitura corrente recupera conteúdo e versão editorial coerentes sob gate shared
e lock da identidade. Não inicializa legado nem lê auditoria. PATCH verifica o ETag,
relê sob lock e usa ambas as expectativas no CAS persistente; estado ausente legado
continua explícito na leitura e é inicializado somente na escrita bem-sucedida.
Projeção de resposta é preparada antes do commit e devolvida depois dele.

ETag forte usa SHA-256 de namespace JSON de edição v1, identidade armazenada, perfil,
revisão, versão editorial (ou ausência) e JSON canônico do Read. Alterações de estado
invalidam o validador mesmo sem nova revisão. Não vale para outras representações.
O adaptador Problem Details mapeia editorial.version_stale para 412 e
editorial.transition_forbidden/editorial.state_invalid para 409; preserva os códigos
e o fallback dos demais erros. PATCH aceita um único If-Match forte; ausência 428,
sintaxe incompatível 400,
precondição obsoleta 412. Não acrescenta campos técnicos ao contrato v1.

Escritas DTO adquirem o **gate exclusivo existente antes de qualquer lock de recurso
ou dependência**, mantendo a ordem gate → recurso → dependências. Criação ainda não
tem identidade persistida disputável ao resolver seus alvos; tudo é atômico no mesmo
commit. Não fazem upgrade shared → exclusive. `_create`/`_revise` podem readquirir
shared dentro da mesma transação que já detém exclusive. Escritas internas Graph
mantêm o protocolo anterior. Isso impede também mudanças de cabeças de dependências
durante a validação DTO, sem criar novo lock/tabela/infraestrutura.

Referência local explícita deve concordar com UUID/URI/tipo persistidos. URI-only
que encontra recurso local recebe evidência de tipo; ausência mantém pendência v1,
sem presumir verificação externa. Publicação interna preserva sua validação mais
restrita de integridade e fechos. Perfil é fixado pelo servidor e conservado.

## Alternativas e consequências

Comparar ETag só antes de abrir transação permite TOCTOU editorial; rejeitado.
Usar HistoryService.read_editorial no GET exigiria metadata_audit:read indevidamente.
Usar sessões/commits independentes para cada componente quebraria atomicidade.
Reordenar todos os locks por fecho/retry ou mudar globalmente a força dos locks
M03 adiciona complexidade. Gate exclusivo reutiliza o mecanismo experimental e
serializa escritas DTO, inclusive entre recursos diferentes; é uma limitação de
paralelismo deliberada, não promessa de capacidade de produção. Leituras shared
ainda disputam esse gate. Uma evolução após medição deverá preservar as garantias.

Nenhuma migração, perfil/shape novo, endpoint público, listagem ou transição HTTP.
Ver [contrato HTTP](../architecture/catalogographic-http.md) e
[evidência](../architecture/catalogographic-m0503-verification-2026-10-16.md).
