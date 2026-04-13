# Tasks — Feature 14: MAPPO Redes e Algoritmo

## Antes de Comecar

Ler obrigatoriamente antes de escrever qualquer codigo:

- `CLAUDE.md` — stack, estrutura do projeto, convencoes
- `.specs/features/14_mappo_redes_algoritmo/spec.md` — criterios de aceitacao desta feature
- `.specs/notes.md` — edge cases e decisoes anteriores
- `.specs/design.md` secoes 5.1 (arquitetura das redes), 5.3 (espaco de acoes), 5.4 (hiperparametros)
- `training/environment/observations.py` — OBS_TOTAL_SIZE (162) para dimensoes de input
- `training/environment/actions.py` — NUM_ACTION_TYPES (10), NUM_TARGETS (80), ActionType

---

## Plano de Execucao

2 grupos sequenciais. Grupo 1 e a fase TDD. Grupo 2 e a implementacao.

- **Grupo 1**: testes para networks, buffer e MAPPO. Parar apos criar os testes.
- **Grupo 2**: implementar networks.py, buffer.py, mappo.py. Rodar testes.

Dependencia: Grupo 2 so executa apos aprovacao dos testes do Grupo 1.

---

### Grupo 1 — Testes (TDD)

**Tarefa:** Criar testes para as redes neurais, buffer de rollout e algoritmo MAPPO.

1. Criar `training/tests/test_networks.py`:
   - **PolicyNetwork:**
     - Cria com (obs_size=162, num_action_types=10, num_targets=80, hidden_size=128)
     - forward(obs, type_mask, target_mask) retorna type_logits (batch, 10) e target_logits (batch, 80)
     - Mascaramento: posicoes False na mask recebem logits muito negativos
     - get_action retorna action tuple (type, target), log_prob scalar, entropy scalar
     - evaluate_action retorna log_prob e entropy para acao dada
     - Parametros treinaveis (contar > 0)
   - **CriticNetwork:**
     - Cria com (global_state_size=162*6, hidden_size=256)
     - forward(global_state) retorna value (batch, 1)
     - Parametros treinaveis (contar > 0)

2. Criar `training/tests/test_mappo.py`:
   - **RolloutBuffer:**
     - add() armazena timestep
     - compute_returns(gamma=0.99, gae_lambda=0.95) calcula advantages e returns
     - Advantages normalizados (mean ~0 com tolerancia)
     - get_batches(batch_size=64) retorna batches com tensors corretos
     - clear() esvazia o buffer
   - **MAPPOAgent:**
     - Cria com 5 policies + 1 critic
     - select_action retorna action, log_prob, entropy para cada classe
     - get_value retorna scalar
     - update(buffer) executa sem erro e reduz loss (1 iteracao)
     - save/load preserva pesos (forward produz mesma saida antes e apos)

3. Rodar testes e confirmar que todos falham.

**Parar apos criar os testes. Nao implementar logica de producao. Aguardar aprovacao do usuario.**

---

### Grupo 2 — Implementacao (um agente)

**Tarefa:** Implementar as redes neurais, buffer e algoritmo MAPPO em PyTorch.

1. Criar `training/agents/networks.py`:
   - `class PolicyNetwork(nn.Module)`:
     - `__init__(self, obs_size, num_action_types, num_targets, hidden_size=128)`:
       - `self.shared = nn.Sequential(Linear(obs_size, hidden_size), ReLU(), Linear(hidden_size, hidden_size), ReLU())`
       - `self.type_head = Linear(hidden_size, num_action_types)`
       - `self.target_head = Linear(hidden_size, num_targets)`
     - `forward(self, obs, type_mask, target_mask)`:
       - features = self.shared(obs)
       - type_logits = self.type_head(features)
       - type_logits[~type_mask] = -1e8
       - target_logits = self.target_head(features)
       - target_logits[~target_mask] = -1e8
       - return type_logits, target_logits
     - `get_action(self, obs, type_mask, target_mask)`:
       - type_logits, target_logits = self.forward(obs, type_mask, target_mask)
       - type_dist = Categorical(logits=type_logits)
       - action_type = type_dist.sample()
       - target_dist = Categorical(logits=target_logits)
       - target = target_dist.sample()
       - log_prob = type_dist.log_prob(action_type) + target_dist.log_prob(target)
       - entropy = type_dist.entropy() + target_dist.entropy()
       - return (action_type, target), log_prob, entropy
     - `evaluate_action(self, obs, action, type_mask, target_mask)`:
       - Recalcula distribuicoes e retorna log_prob e entropy para a acao dada
   - `class CriticNetwork(nn.Module)`:
     - `__init__(self, global_state_size, hidden_size=256)`:
       - MLP: Linear(global_state_size, hidden_size) → ReLU → Linear(hidden_size, hidden_size) → ReLU → Linear(hidden_size, 1)
     - `forward(self, global_state) -> Tensor (batch, 1)`

2. Criar `training/agents/buffer.py`:
   - `class RolloutBuffer`:
     - Armazena por agent_id: listas de obs, actions, log_probs, rewards, values, dones, type_masks, target_masks
     - `add(agent_id, obs, action, log_prob, reward, value, done, type_mask, target_mask)`
     - `compute_returns(gamma=0.99, gae_lambda=0.95)`:
       - Para cada agente: calcula GAE advantages e returns
       - Normaliza advantages (mean=0, std=1)
     - `get_batches(batch_size=64)`:
       - Concatena dados de todos agentes
       - Shuffla e retorna mini-batches como dicts de tensors
     - `clear()`: limpa todos os dados

3. Criar `training/agents/mappo.py`:
   - `class MAPPOAgent`:
     - `__init__(self, obs_size=162, global_state_size=None, num_action_types=10, num_targets=80, lr=3e-4, clip_range=0.2, entropy_coeff=0.01, value_coeff=0.5, epochs=4)`:
       - Cria 5 PolicyNetworks (keyed por CharacterClass.value: "warrior", "mage", etc.)
       - Cria 1 CriticNetwork
       - Optimizer: Adam com lr=3e-4 sobre todos parametros (policies + critic)
     - `select_action(self, class_name, obs, type_mask, target_mask)`:
       - Seleciona policy pela class_name, chama get_action
     - `get_value(self, global_state)`:
       - Retorna critic.forward(global_state)
     - `update(self, buffer)`:
       - buffer.compute_returns()
       - Para cada epoch (4):
         - Para cada batch em buffer.get_batches(64):
           - Calcula ratio = exp(new_log_prob - old_log_prob)
           - Policy loss (clipped)
           - Value loss (MSE)
           - Entropy bonus
           - Total loss = policy_loss + value_coeff * value_loss - entropy_coeff * entropy
           - optimizer.step()
     - `save(self, directory)`: salva cada policy como {class_name}.pt
     - `load(self, directory)`: carrega policies de .pt files

4. Atualizar `training/agents/__init__.py`:
   - `from training.agents.mappo import MAPPOAgent`
   - `from training.agents.networks import CriticNetwork, PolicyNetwork`

5. Rodar `pytest training/tests/test_networks.py training/tests/test_mappo.py -v`.

6. Rodar `pytest engine/tests/ training/tests/ -v` para garantir zero regressoes.

---

## Condicao de Conclusao

- Todos os criterios de aceitacao do spec.md satisfeitos
- Todos os testes passam com `pytest engine/tests/ training/tests/ -v`
- Atualizar `.specs/state.md`: status da feature 14 de `pendente` para `concluida`
- Atualizar `.specs/notes.md` com edge cases descobertos
