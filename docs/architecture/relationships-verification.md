# Verificação do pré-requisito de relacionamentos (#16)

Os contratos da #16 estavam publicados no GitHub, mas ausentes do checkout
2f2b61c. Foram reaproveitados na #17, com os 108 testes e as 41 fixtures + manifest
originais, sem importar o relatório histórico como evidência de execução local.

Os resultados executados nesta sessão e os limites estão no
[relatório de identificadores](persistent-identifiers-verification.md).
A suíte inclui test_relationships.py, test_catalogographic_schemas.py e os
testes novos de identidade, preservando formatos URI-only, modalidades tipadas,
operações, agrupamentos Contribution/Publication e resolvedor desacoplado.

Existência em banco, aliases de fusão, workflow e endpoints são integrações futuras
onde não houver persistência implementada; doubles não comprovam PostgreSQL.
