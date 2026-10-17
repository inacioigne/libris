# ADR 0038 — Adaptadores HTTP do ciclo editorial e histórico

Data: 2026-10-16. Status: implementado tecnicamente para M05.05 / #49.

## Contexto

ADRs 0026–0028 e 0031 já governam máquina editorial, snapshots, auditoria e
transações. M05.03/04 acrescentaram DTOs e ETag de edição vinculado a conteúdo e
versão editorial. Falta publicar comandos e histórico sem duplicar essas garantias.

## Decisão

Adicionar sete rotas POST explícitas, sem parâmetro de ação arbitrária. Cada rota
seleciona uma EditorialOperation existente. EditorialService recebe expectativa
opcional da operação: pré-autoriza exatamente essa operação e confere sua identidade
após resolver a transição sob lock. Assim publish não executa republish, mesmo se o
ator possuir ambas as permissões. Chamadores internos anteriores continuam válidos.
A matriz TRANSITIONS permanece a única máquina; nenhuma concessão RBAC é alterada.

CatalogEditorialService adapta coleção/tipo persistido e contexto OIDC, reutiliza
CatalogService, HistoryService, BibliographicService.restore_content e
PostgresEditorialTransactions. Não há SQL ou commit nos routers. A observação prévia
para If-Match produz as duas expectativas entregues ao CAS transacional existente.
A resposta da transição usa o estado confirmado e o conteúdo observado, sem releitura
posterior que pudesse misturar uma edição concorrente com o resultado da operação.

Usar o ETag de edição M05.03 como precondição dos comandos e da restauração.
GET do recurso e GET editorial fornecem esse mesmo validador de edição. Seu valor
representa a geração de edição do recurso; não é validador de snapshot/exportação.
Não acrescentar expected_revision/version ao payload. Estado legado sem inicialização
continua null, e a primeira transição efetiva inicializa draft/version=1 dentro da
própria transação. Leituras não fabricam estado ou eventos.

Estado requer leitura editorial do tipo; histórico combinado requer a política
metadata.editorial_history; revisões e auditoria preservam permissões independentes.
A autorização específica ocorre antes da observação do recurso. Transição autorizada
não exige implicitamente acesso à auditoria. Extras no body são proibidos e headers
não substituem o ator validado. Proveniência técnica é fixada pelo servidor.

A projeção pública fica em `/{collection}/{id}/public`, separada do GET editorial.
Retorna apenas Read da revisão selecionada por read_public; ausente, legado, retirado,
arquivado ou outra coleção retornam o mesmo Problem Details 404 sem conteúdo interno.
Nenhum ETag editorial é enviado nessa leitura. A política no-store/private existente
aplica-se também a essa rota, evitando caches públicos obsoletos após retirada.

Histórico preserva keyset existente: revisão ascendente e eventos por instante/UUID.
Não cria snapshot global entre páginas; novos registros posteriores ao cursor podem
aparecer. O cursor completo é devolvido sem perda de precisão. Snapshots completos
são Turtle e comparação delega ao algoritmo RDF isomórfico existente. Rótulos de
blank nodes não constituem identidade durável. Restauração cria revisão nova sem
publicá-la e registra restored/content no mesmo commit.

## Consequências e limites

Sem migrações, tabelas, dependências, locks, máquina ou permissões adicionais.
O gate conservador existente mantém seus limites de paralelismo. A classificação
externa necessária à publicação continua exigindo configuração confiável; a API
não aceita um mapa de verificação do cliente nem presume existência remota. A
configuração HTTP atual não fornece esse mapa: referências não locais sem evidência
bloqueiam publicação, como no serviço M03.

Listagem pública, negociação Accept e descoberta continuam na #50. Não há interface
M07, circulação, conectores ou homologação institucional/produção nesta entrega.
Ver [contrato HTTP](../architecture/catalogographic-editorial-http.md) e
[evidências](../architecture/catalogographic-m0505-verification-2026-10-16.md).
