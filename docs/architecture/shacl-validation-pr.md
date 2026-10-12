# Proposta de Pull Request — #21

Título: `feat(bibliographic): consolidate versioned SHACL validation (#21)`

Base: `main`. Head: `feat/21-shacl-validation`.

## Resumo

A validação dos perfis 2.0 executava somente shapes históricas, ignorando políticas especializadas como mínimos e formatos digitais admitidos. O adaptador agora acrescenta apenas constraints ausentes, no mesmo pySHACL, e rejeita configurações contraditórias. O perfil core conserva o grafo de 832 triplas, sem constraints duplicadas.

O diagnóstico conserva focusNode/resultPath, severidade, mensagens, sourceShape/sourceConstraintComponent/value e termos RDF exatos. Falhas de resolução, shapes indisponíveis/malformadas e falhas do motor são distinguíveis de não conformidade. A resolução histórica deriva do registro único por release/contexto.

## Decisões e compatibilidade

- ADR 0022 justifica o suplemento determinístico limitado às políticas declarativas 2.0 não cobertas pelas fontes locais.
- validate_profile/validate_monograph e JSON/TTL históricos preservados; revisões mantêm sua release. Sem migração, dependências, tabelas ou endpoints novos.
- Snapshot aceita referências URI não descritas; composição verifica inversas, sem alterar dados ou fabricar tipos.
- Cache limitado conserva somente termos/verificações imutáveis; Graph privado por execução. Medição simples: 3,103 s frio e 0,040 s quente.
- Inventário integral, especificação, matriz de critérios/evidências e quatro fixtures novas. Warning/Info não bloqueiam; Violation bloqueia.

## Validação

- API Python 3.13.15: 788 testes aprovados, 0 falhas (54,99 s), incluindo 67 casos SHACL novos.
- Ruff sem erros; mypy sem erros em 53 arquivos; 10 artefatos gerados verificados.
- Frontend Node 24.16.0: build e typecheck aprovados.
- Docker Compose config e git diff --check aprovados.
- 5 testes PostgreSQL ignorados: TEST_DATABASE_URL dedicado ausente; rollback físico não comprovado nesta sessão. Doubles verificam saída transacional e ausência de save.
- scripts/check.sh interrompido por uv/Snap; partes verificadas separadamente. Testes/build com threads/subprocessos exigiram execução fora do sandbox.

## Limitações

Contrato HTTP definitivo pertence à #22; vocabulários/ontologias a #24/#25 e corpus futuro a #30. Não há integração v2 à escrita persistente ou quotas de CPU para endpoints. Homologação catalográfica e identidade/pertinência externa exigem avaliação humana.

Referência: #21. Revisão humana requerida; não fechar a issue antes da aprovação.
