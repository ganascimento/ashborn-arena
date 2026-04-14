# Feature 19 — Inference IA

## Objetivo

Substituir o agente IA heuristico (`backend/ai_agent.py`) por inference MAPPO que carrega checkpoints treinados (feature 16) e usa as PolicyNetwork para selecionar acoes. Isso faz os niveis de dificuldade (easy/normal/hard) funcionarem de verdade — cada nivel carrega checkpoints de fases diferentes do curriculum learning. Quando os modelos nao estao disponiveis, faz fallback para o agente heuristico existente.

---

## Referencia nos Specs

- prd.md: secao 4.2 (niveis de dificuldade baseados em checkpoints)
- design.md: secoes 5.1 (arquitetura das redes), 5.2 (observacao), 5.3 (espaco de acoes), 5.5 (armazenamento de modelos)

---

## Arquivos Envolvidos

**Criar:**

- `backend/inference/model_loader.py` — carrega e cacheia PolicyNetwork por dificuldade
- `backend/inference/inference_agent.py` — gera acoes usando policy carregada
- `backend/tests/test_inference.py` — testes do modulo de inference

**Modificar:**

- `backend/inference/__init__.py` — re-exportar funcoes publicas
- `backend/api/routes/ws.py` — usar inference no turno da IA

---

## Criterios de Aceitacao

### Carregamento de modelos

- [ ] `get_policies("easy")` carrega 5 PolicyNetwork de `models/easy/{warrior,mage,cleric,archer,assassin}.pt`
- [ ] `get_policies("normal")` carrega de `models/normal/`
- [ ] `get_policies("hard")` carrega de `models/hard/`
- [ ] Modelos sao carregados uma unica vez e cacheados — chamadas subsequentes retornam o cache
- [ ] PolicyNetwork usa os mesmos parametros do treinamento: obs_size=OBS_TOTAL_SIZE (162), num_action_types=10, num_targets=80
- [ ] Todas as policies sao colocadas em modo eval (`policy.eval()`)
- [ ] Se o diretorio `models/{difficulty}/` nao existe, retorna None (sem erro)
- [ ] Se algum arquivo .pt esta ausente no diretorio, retorna None (sem erro)

### Geracao de acoes

- [ ] `get_inference_action(battle, entity_id, policy)` retorna `(action_type, target_tile)` — tupla de dois inteiros
- [ ] Usa `encode_observation(battle, entity_id)` de `training.environment.observations` para criar o input
- [ ] Usa `compute_action_mask(battle, entity_id)` de `training.environment.actions` para mascarar acoes invalidas
- [ ] Usa `PolicyNetwork.get_action_hierarchical` para sampling com mascara hierarquica (type → target)
- [ ] Inference roda com `torch.no_grad()` (sem calcular gradientes)
- [ ] Retorna acoes no mesmo formato que `get_ai_action` do agente heuristico: (action_type: int, target_tile: int)

### Integracao com WebSocket

- [ ] `_handle_ai_turn` no WS handler carrega policies da dificuldade da sessao
- [ ] Para cada acao da IA, determina a classe do personagem e usa a policy correspondente
- [ ] Se policies nao disponiveis (None), faz fallback para `get_ai_action` do agente heuristico
- [ ] O fallback e transparente — o comportamento externo (mensagens WS) e identico
- [ ] Testes existentes do WS (11 testes) continuam passando sem modificacao

### Fallback

- [ ] Se `models/` nao existe ou esta incompleto, a batalha funciona normalmente com o agente heuristico
- [ ] Nenhum erro e lancado por falta de modelos — apenas log ou silencio

---

## Fora do Escopo

- Treinar novos modelos ou melhorar os existentes (feature 16 — ja concluida)
- Modificar a arquitetura das redes (PolicyNetwork definida em training/agents/networks.py)
- Alterar o formato dos checkpoints (.pt)
- Frontend (features 20-24)
- Timeout de inferencia / otimizacao de performance
