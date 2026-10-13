# ADR 0025 — Extensões semânticas governadas por releases locais

Status: implementado tecnicamente para #25; homologação institucional pendente

Data: 2026-10-12

## Contexto

ADRs 0007, 0014 e 0017–0024 estabelecem Graph canônico, identidades estáveis,
DTOs limitados, perfis declarativos, SHACL local e valores controlados.
SemanticRegistry 1.0 já suporta namespaces externos, mas não fixa seu conteúdo
por release nem verifica a autorização de classes. Um namespace conhecido não
constitui homologação de todos os seus termos. Não há rota pública de catalogação.

## Decisão

Evoluir o registro existente de forma aditiva: formato 1.1 com rótulos,
descrições, mantenedor, inclusão, aprovação e namespace explícito de termos.
Release 2.0 local preserva contratos de 1.0 e acrescenta dcterms:abstract e
prov:Entity auxiliar. Bases/prefixos não se sobrepõem; bf e identidades das
classes principais são reservados. Classes não homologadas não entram como
origem/destino de campos. Não transformar classes auxiliares em novas entidades.

Fixar ambos os registros por SHA-256 no pacote e resolver release por mapa
confiável. Associar o perfil candidato work-extensions:2.0.0 ao registro 2.0;
herança e transições preservam a associação. Perfis históricos seguem em 1.0.
Verificação aditiva impede redefinir contratos semânticos anteriores. Metadados
de suporte Libris não são axiomas universais das ontologias; política institucional
permanece em CatalogPolicy e shapes, sem novos condicionais DCTERMS.

Reutilizar ProfileRegistry, ResolvedProfile, RDFLib, pySHACL, diagnóstico e contexto
bibframe-v1. O resumo é validado pelas restrições suplementares existentes.
Preservação de triplas, autorização de campos e conformidade SHACL são independentes.
Exportar o Graph integral e verificar isomorfismo, nunca reconstruir um snapshot
integral a partir dos DTOs reduzidos. Os DTOs permanecem fechados.

O serviço transacional mantém os perfis legados. O perfil novo demonstra resolução
e validação, sem prometer integração HTTP/transacional ainda ausente. O caminho
existente de revisão preserva extensões quando recebe o Graph completo; não
combina patches automaticamente. Nenhuma mudança no banco ou migração.

Mapeamentos são especificações de relações/evidência/transformação, sem motor
executável ou inferência de equivalência. Não criar owl:sameAs/equivalentProperty/
equivalentClass. Mudanças incompatíveis exigem novas releases, decisão de migração,
URI estável, proveniência, concorrência e validação final. Não revalidar históricos
nem atualizar suas referências automaticamente.

## Alternativas e consequências

- Segundo registro de ontologias ou modelos bibliográficos JSON: duplicaria fontes
  de verdade; evoluir os contratos locais existentes.
- Alterar semantics-v1 ou o contexto histórico: reinterpreta releases; criar 2.0,
  preservar 1.0 e reutilizar IRIs absolutas no contexto existente.
- Aceitar qualquer termo de namespace conhecido: confunde reconhecimento e edição;
  exigir classe/propriedade/perfil suportados.
- Shapes fechadas e descarte de predicados externos: perderiam dados de intercâmbio;
  preservar RDF e validar as regras declaradas sem autorizar novos campos.
- Ontologias/imports remotos: validação dependeria de terceiros; somente pacote local.
- Migrador ou inferência genéricos: sem necessidade executável nesta issue.

Sem dependências, endpoints, frontend, tabelas, triplestore, filas ou microsserviços.
[Arquitetura e matriz](../architecture/semantic-extensions.md).
