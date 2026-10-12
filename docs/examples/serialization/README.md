# Exemplos de representação v1

Dados exclusivamente sintéticos. work, instance, item, agent, subject e organization
possuem JSON Read operacional e JSON-LD/Turtle semanticamente isomórficos.
related.json lista os seis Read explicitamente selecionados; related.jsonld/ttl
compõem seus snapshots e derivam hasInstance/hasItem, sem gravá-las nos proprietários.

Os testes em tests/api/test_semantic_serialization.py validam todos os exemplos.
O contexto é repetido em cada nó do array para evitar @graph, preservando o parser
seguro atual. A ordem e os rótulos de blank nodes não são parte do contrato.

Da raiz, com ambiente sincronizado:

```bash
apps/api/.venv/bin/python scripts/generate_serialization_examples.py
```

Ver [especificação](../../architecture/semantic-serialization.md).
