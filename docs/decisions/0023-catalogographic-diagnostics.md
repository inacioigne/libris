# ADR 0023 — Diagnósticos catalográficos públicos e Problem Details

Status: implementado tecnicamente para a #22; homologação institucional pendente

Data: 2026-10-12

## Contexto

#15/#17/#19 consolidaram contratos, identidades e representações; #20/#21 fornecem
perfis resolvidos, SHACL local, ValidationReport e FieldValidationIssue. Faltam
uma representação pública sem termos RDF internos, códigos e tradução HTTP.
Não existem rotas de catálogo. Introduzi-las para demonstrar erros anteciparia CRUD.

## Decisão

Publicar contrato 1.0 em application/diagnostics.py, neutro ao transporte e gerado
por Pydantic v2; API reexporta os nomes. infrastructure/diagnostics.py adapta os
relatórios existentes. application/validation.py coordena pré-validação histórica
ou de ResolvedProfile confiável. Serviços persistentes conservam validate_profile,
suas assinaturas, precondições de domínio e fronteiras commit/rollback.
CatalogValidationRejected herda CatalogError/ValueError e conserva o resultado.
Falhas técnicas continuam exceções na escrita, nunca conformidade falsa/verdadeira.

Códigos do domínio em domain/errors.py não importam HTTP. A camada api/problems.py
mapeia exceções conhecidas e padroniza RFC 9457; fallback inesperado é 500, com log
interno seguro. Não capturar ValueError/LookupError genericamente como erro do usuário:
isso esconderia programação defeituosa. Ausência persistente recebe subclasse
LookupError explícita. Violações de referências/ownership recebem subclasses
ValueError, sem alterar mensagens usadas por chamadores legados.

Correlação via middleware ASGI e ContextVar; UUID aceito/gerado uma vez e devolvido
em X-Request-ID, inclusive 500. instance é urn:uuid, sem path/query recebidos.
O adaptador If-Match exige ETag forte da representação fornecido pelo chamador;
não gera ETags nem converte tokens uuid:rN em revisões HTTP.

Valores literais são omitidos; IRIs com query, credenciais, esquema local ou mais
de 2048 caracteres também. Mensagens dinâmicas do motor são substituídas por
mensagens públicas fixas; mensagens SHACL autorais presentes no pacote são
preservadas. Caminhos complexos têm estrutura pública limitada, sem inferência ou
correlação heurística. Identificadores de blank nodes são digests de descrições
canônicas com literais redigidos, locais ao diagnóstico, nunca identidades persistentes.

## Alternativas e consequências

Expor relatório pySHACL/ValidationError diretamente vazaria valores e detalhes
internos. Substituir ValidationIssue ou duplicar motores quebraria #20/#21.
Modelo somente em API forçaria serviço interno a importar HTTP ou duplicar contrato.
Capturar todas as falhas como 422 confundiria confiabilidade e conformidade.

Campos/códigos aditivos preservam 1.x; mudanças de significado/obrigatoriedade
exigem nova major. Clientes toleram código novo e usam message como fallback.
OpenAPI real expõe schemas e respostas globais; a operação de pré-validação HTTP,
as rotas de escrita e o editor Next.js permanecem futuros. Sem dependências,
locks novos, migrações, alterações de releases ou infraestrutura permanente.

Ver [contrato](../architecture/catalogographic-errors.md) e
[evidências](../architecture/catalogographic-errors-verification.md).
