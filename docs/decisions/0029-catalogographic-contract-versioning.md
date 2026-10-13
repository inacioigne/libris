# ADR 0029 — Baseline documental e evolução do contrato catalográfico público

Status: **proposto para governança de releases públicas**; baseline documental
implementada na #31; sem aprovação institucional presumida

Data: 2026-10-12

## Contexto

Os ADRs 0014/0017–0028 preservam perfis, referências, RDF, diagnósticos e revisões,
mas suas versões não identificam uma especificação pública consolidada. O produto
não oferece CRUD catalográfico. Os DTOs usam `extra=forbid`, portanto “campo opcional
novo” pode preservar produtores antigos e ainda romper leitores antigos. Também
Diagnostic.code usa CatalogCode fechado, apesar do fallback recomendado para UI.
SemVer da aplicação 0.1.0 ou `/api/v1` não resolve essas diferenças.

## Proposta e parte implementada

Identificar a referência documental como `urn:libris:contract:catalogographic:v1`,
baseline **1.0.0**. O artefato JSON Schema gerado dos modelos reais e o inventário
de campos registram essa baseline. Não acrescentar constantes à aplicação, campos
aos DTOs, tabelas, mecanismo HTTP, seleção de versão ou dependências. A geração
normal recusa sobrescrever baseline divergente; `--check` é somente leitura.

Aplicar Semantic Versioning **à especificação pública**, sujeito à aprovação desta
política antes de novas releases. A major designa a família de contratos, minor
acrescenta capacidade demonstradamente compatível em ambas as direções, patch
corrige documentação/artefatos sem alterar comportamento. Mudança comportamental
não se torna patch por ser chamada de bugfix. A extensão `.schema.json` contém
schema de validação; validar invariantes Pydantic e serialização além do schema.

| Mudança | Produtor antigo → consumidor novo | Produtor novo → consumidor antigo | Classificação proposta |
| --- | --- | --- | --- |
| Correção de link/texto que descreve o mesmo comportamento | Preservado | Preservado | Patch documental |
| Novo exemplo ou teste sem alterar contrato | Preservado | Preservado | Patch documental |
| Campo opcional de entrada novo | Aceita entrada antiga, salvo mudança de default | Extra novo é rejeitado por DTO antigo | Major se enviado pela mesma superfície; minor somente com seleção explícita e payload antigo preservado |
| Campo opcional de saída novo | Não interfere no produtor antigo | Leitor com extra=forbid rejeita | Mesmo exame direcional; não presumir minor |
| Novo campo obrigatório / opcional tornando-se obrigatório | Entrada antiga pode falhar | Exige alteração do cliente | Major |
| Remover/renomear propriedade, mudar null/default/tipo/datatype | Pode invalidar entrada antiga | Pode invalidar leitura ou mudar intenção | Major quando rompe aceitação/semântica |
| Restringir mínimo/máximo/cardinalidade/valores | Pode rejeitar dados válidos antigos | Pode mudar interpretação | Major pública se afeta superfície atual; nova release de perfil/shape independente |
| Relaxar cardinalidade/adicionar enum ou código | Pode aceitar dados antigos | Modelo antigo pode rejeitar novos valores | Examinar ambas as direções; não presumir compatibilidade |
| Alterar propriedade RDF, ownership, significado ou regra de identidade | Muda significado dos dados existentes | Muda interpretação | Major e ADR específico, com decisão explícita |
| Novo recurso selecionável isoladamente | Contratos antigos intactos | Contratos antigos intactos se não recebem recurso novo | Minor possível, com evidência de isolamento |

Compatibilidade considera leitura, produção, validação e significado, não apenas
JSON bem formado. Consumidores de UI podem usar código desconhecido como fallback;
isso não torna o enum Pydantic antigo permissivo. Não alterar unilateralmente esse
enum ou extra=forbid. Clients novos devem conhecer a versão selecionada e evitar
enviar campos/valores não suportados ao leitor antigo. Sem seleção implementada,
não alegar coexistência operacional de versões HTTP.

## Releases, coexistência e migração

Releases históricas permanecem disponíveis com seus arquivos/IDs e interpretação,
incluindo contextos, bases transitivas e shapes. Não regenerar a baseline 1.0.0
contra modelos incompatíveis: introduzir artefato de versão nova, manter os anteriores
e adaptar explicitamente gerador/testes para verificar ambas as versões. Compatibilidade
da baseline é uma verificação de schema e comportamento, sem snapshot de ordenação RDF.

Descontinuação deve registrar motivo, sucessor, superfícies afetadas e janela de
suporte definida pelos mantenedores. Não há data de retirada ou prazo institucional
aprovado. Manter leitura histórica e artefatos das versões usadas; depreciação não
reescreve perfil/revisões nem redireciona automaticamente seleção explícita.
Uma API futura precisará de ADR próprio para seleção/coexistência, adaptadores e
eventual publicação de headers/rotas; não escolher esse mecanismo antecipadamente.

Migração é opt-in: mapear campos e identidades, preservar grafo original e histórico,
relatar perdas/extensões, validar destino, registrar perfil/release/proveniência e
usar revisão esperada/CAS quando houver escrita. Não recalcular URI por base nova,
reutilizar UUID, converter revisão histórica in-place ou reinterpretar releases.
BibliographicService não oferece hoje migração de perfil: documentação de estratégia
não autoriza inventar esse serviço ou operação.

## Dimensões independentes

1. Especificação pública documental 1.0.0 (DTOs, semântica e compatibilidade).
2. Formato declarativo 2.0 e releases de cada perfil (ex.: monograph 2.0.0).
3. Releases SHACL experimental 1.0 / institutional 1.1 por contexto.
4. Revision.number do registro por identidade, e versão editorial independente.

Diagnóstico 1.0, valores controlados 1.0, contexto bibframe-v1 e registro semântico
2.0 também conservam identificadores próprios. Nenhuma dimensão substitui outra.

## Alternativas e consequências

Versionar tudo pela aplicação confundiria deploy com semântica histórica; alterar
payloads ou acrescentar registro de versões na persistência anteciparia APIs sem
necessidade. A baseline documental reutiliza Pydantic, geradores e corpus existentes.

O custo é manter inventário, schema e evidência de compatibilidade juntos. O gerador
detecta divergência, mas não impede edição manual nem é infraestrutura de publicação.
SemVer não comprova por si só compatibilidade. Homologação biblioteconômica, política
de disponibilidade e aprovação deste ADR continuam decisões explícitas humanas.

Referências: [contrato](../architecture/catalogographic-contract.md),
[rastreabilidade](../architecture/catalogographic-contract-traceability.md),
[evidências](../architecture/catalogographic-contract-v1-verification.md).
