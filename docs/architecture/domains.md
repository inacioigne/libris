# Domínios e responsabilidades

Os módulos abaixo são fronteiras propostas, não funcionalidades implementadas.
Apenas a infraestrutura comum e saúde existem. Cada módulo possui seus dados e
contratos; as dependências abaixo são lógicas e não autorizam acesso direto a tabelas.

| Módulo futuro | Responsabilidade | Limites e colaboração |
| --- | --- | --- |
| Catalogação | Work, Instance, Item semântico; relacionamentos; revisões e proveniência | Referencia autoridades; não registra empréstimos, multas ou disponibilidade |
| Autoridades | Pessoas, organizações, assuntos, lugares; identificadores e reconciliação | Publica referências reutilizáveis; não altera catálogo por acesso direto |
| Inventário | Exemplar administrativo, barcode, localização, condição e situação patrimonial | Referencia Instance e, quando pertinente, Item; não possui o registro bibliográfico |
| Circulação | Empréstimos, devoluções, reservas e aplicação das políticas | Usa contratos de inventário, usuários e políticas; protege concorrência e transações |
| Usuários | Leitores, vínculos e categorias institucionais | Dados pessoais segregados dos dados bibliográficos públicos; identidade não é autoridade |
| Políticas | Regras de prazo, elegibilidade e limites por contexto | Regras versionadas; circulação registra qual versão foi aplicada |
| Aquisições | Fornecedores, pedidos, orçamento e recebimento | Gera pedidos de incorporação ao inventário; não cria tabelas do catálogo diretamente |
| Periódicos | Assinaturas, previsão, recebimento e lacunas de fascículos | Colabora com aquisições, catálogo e inventário |
| Descoberta | Projeções Elasticsearch, consulta, facetas e relevância | Índices reconstruíveis; disponibilidade é projeção ou consulta ao inventário |
| Relatórios | Indicadores, exportações e projeções analíticas | Evita relatórios pesados nas transações; controle de acesso e minimização de dados |
| Interoperabilidade | Importação/exportação MARC, JSON-LD e APIs externas | Adaptadores mapeiam formatos para contratos de domínio; MARC não é modelo interno |

## Fronteiras e consistência

Separar referência pública bibliográfica de referência interna administrativa.
Um empréstimo aponta para um exemplar de inventário, nunca diretamente para um
Work. Reservas por obra/edição e regras de seleção serão definidas em etapa própria.
A disponibilidade não é propriedade autoritativa de um documento Elasticsearch.

Na primeira implementação, preferir chamadas de serviços dentro do processo.
Quando uma alteração precisar de efeitos assíncronos, usar outbox PostgreSQL,
consumidores idempotentes e envelopes com event_id, versão, occurred_at, aggregate_id,
revision e correlation_id. Esses campos são proposta, não contrato implementado.
Garantias de entrega e ordem serão definidas no ADR do primeiro caso concreto.

Configuração, logging, conexão de banco e saúde são infraestrutura comum e não
um domínio de negócio. Evitar um módulo shared que concentre regras de todos os
módulos. `packages/shared` não substitui contratos explícitos entre eles.
