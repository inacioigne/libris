# ADR 0022 — Constraints SHACL suplementares para políticas declarativas

Status: implementado tecnicamente para a #21; revisão e homologação pendentes

Data: 2026-10-12

## Contexto

A #20 resolve perfis 2.0 com especialização de mínimos/máximos, valores admitidos,
idiomas e propriedades adicionais. As shapes institucionais 1.1 cobrem o núcleo,
mas não aplicam, por exemplo, o enum de schema:encodingFormat de digital-2.0.0,
seu datatype de schema:dateCreated ou um mínimo especializado de títulos.
Executar somente as fontes locais aceitaria RDF contrário à política declarada.
Editar as fontes históricas ou cada configuração candidata viola imutabilidade.

## Decisão

Manter validate_profile/validate_monograph exclusivamente sobre as fontes históricas.
validate_resolved_profile recebe uma configuração **confiável, já resolvida pelo
ProfileRegistry**, confere correspondência com constraints locais e acrescenta
um grafo SHACL suplementar efêmero pelo adaptador validation_policy.py.
A aplicação futura não deve aceitar ResolvedProfile arbitrário de um request.

Não é outro motor: o mesmo pySHACL executa as regras locais e o suplemento.
A tradução é limitada ao contrato 2.0 existente: cardinalidades, tipos de nó,
texto/datatype, idiomas, enums e classes de propriedades novas. Constraints
qualificadas, referências e relações existentes permanecem nas fontes Turtle.
Descritores não substituem as shapes: tipos de destino de propriedades já cobertas
são conferidos contra as alternativas locais, sem estreitar silenciosamente listas
históricas de classes. O caso Item (descritor Identifier/Local, shape também Isbn)
é explicitamente preservado. Relaxar mínimos/máximos locais, mudar nodeKind ou
indicar datatype/classe incompatível gera contradictory_shapes.

Não traduzir presentation, required_in_form, conditions, default, vocabulary ou
specializable em regras RDF. Não aplicar defaults nem baixar fontes. Derived é
ignorado pelo suplemento: ownership e shapes compostas governam inversas.

Identificadores de shapes suplementares usam urn:libris:policy:v1, SHA-256 canônico
do conteúdo resolvido (release, referências SHACL, classes/campos/value/policy) e
nome do campo. Ordem de apresentação, traduções e disponibilidade não mudam a regra.
Blank nodes são locais a cada execução; reprodutibilidade significa isomorfismo,
não igualdade de rótulos. Mudanças da tradução exigem outro identificador de versão
do adaptador e análise de compatibilidade, nunca revalidação histórica implícita.
O serviço persistente continua usando IDs históricos e não adota perfis 2.0 agora.

Meta-SHACL local verifica as fontes antes da execução. O cache limitado conserva
somente tuplas/frozensets de termos imutáveis e verificações bem-sucedidas, com
conteúdo como chave; a resolução id/release/context fixa quais conteúdos participam.
Arquivos continuam lidos a cada chamada: mudança ou indisponibilidade não é ocultada.
Cada chamada reconstrói Graph privado; suplementos não são compartilhados/cached.

## Alternativas e consequências

- Ignorar políticas: conformidade incorreta e inconsistência com #20.
- Gerar todas as regras a partir do JSON: perde constraints qualificadas e cria
  uma segunda fonte de verdade. O suplemento preserva as regras manuais existentes.
- Rejeitar todas as especializações: impede executar configurações já previstas.
- Publicar um Turtle manual por cada combinação: multiplica artefatos e não cobre
  a especialização declarativa; novos conjuntos manuais continuam possíveis.

Sem dependências, tabelas ou API nova. Integração HTTP/códigos finais pertence à #22.
Políticas institucionais novas e homologação permanecem decisões humanas.
Ver [especificação](../architecture/shacl-validation.md) e
[inventário](../architecture/shacl-inventory.md).
