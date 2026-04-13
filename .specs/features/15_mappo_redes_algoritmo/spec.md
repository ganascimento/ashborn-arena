# Feature 14 — MAPPO Redes e Algoritmo

## Objetivo

Implementar o algoritmo MAPPO (Multi-Agent PPO) com implementacao propria em PyTorch: 5 policy networks (uma por classe) + 1 centralized critic compartilhado, rollout buffer para coleta de trajetorias, e o loop de update PPO com clipped objective. Paradigma CTDE — Centralized Training, Decentralized Execution. Esta feature fornece toda a maquinaria de RL necessaria para o training pipeline (feature 15).

---

## Referencia nos Specs

- prd.md: secoes 4.1 (abordagem IA — MAPPO, CTDE, 1 policy por classe), 4.7 (self-play)
- design.md: secoes 5.1 (arquitetura das redes — MLP, dimensoes), 5.3 (espaco de acoes — tipo + alvo + mascara), 5.4 (pipeline de treinamento — hiperparametros)

---

## Arquivos Envolvidos

### Criar

- `training/agents/networks.py` — PolicyNetwork, CriticNetwork (PyTorch nn.Module)
- `training/agents/mappo.py` — MAPPOAgent (gerencia policies + critic, coleta rollouts, executa updates PPO)
- `training/agents/buffer.py` — RolloutBuffer (armazena trajetorias para PPO update)
- `training/tests/test_networks.py` — testes das redes
- `training/tests/test_mappo.py` — testes do algoritmo MAPPO

### Modificar

- `training/agents/__init__.py` — re-exportar MAPPOAgent, PolicyNetwork, CriticNetwork

---

## Criterios de Aceitacao

### Policy Network (design.md 5.1)

- [ ] `PolicyNetwork(obs_size, num_action_types, num_targets, hidden_size=128)` cria rede MLP
- [ ] Arquitetura: 2 camadas ocultas de 128 neuronios cada, ReLU (conforme design.md 5.1)
- [ ] Input: observacao local com shape (batch, 162)
- [ ] Output: duas heads — `type_logits` (batch, 10) e `target_logits` (batch, 80)
- [ ] `forward(obs, type_mask, target_mask)` retorna type_logits e target_logits com acoes invalidas mascaradas (valor -1e8 antes do softmax)
- [ ] `get_action(obs, type_mask, target_mask)` retorna action (type, target), log_prob, entropy
- [ ] `evaluate_action(obs, action, type_mask, target_mask)` retorna log_prob e entropy para uma acao especifica (usado no PPO update)
- [ ] 5 instancias independentes (uma por CharacterClass) — nao compartilham pesos

### Centralized Critic (design.md 5.1)

- [ ] `CriticNetwork(global_state_size, hidden_size=256)` cria rede MLP
- [ ] Arquitetura: 2 camadas ocultas de 256 neuronios cada, ReLU
- [ ] Input: estado global completo (todas observacoes concatenadas)
- [ ] Output: valor escalar V(s) — shape (batch, 1)
- [ ] 1 instancia compartilhada entre todos os agentes

### RolloutBuffer

- [ ] Armazena trajetorias por agente: observations, actions, log_probs, rewards, values, dones, masks
- [ ] `add(agent_id, obs, action, log_prob, reward, value, done, type_mask, target_mask)` adiciona um timestep
- [ ] `compute_returns(gamma=0.99, gae_lambda=0.95)` calcula returns e advantages usando GAE (Generalized Advantage Estimation)
- [ ] `get_batches(batch_size=64)` retorna mini-batches para o PPO update
- [ ] `clear()` limpa o buffer apos o update

### GAE (Generalized Advantage Estimation)

- [ ] `advantage_t = delta_t + gamma * gae_lambda * advantage_{t+1}` onde `delta_t = reward_t + gamma * V(s_{t+1}) * (1-done) - V(s_t)`
- [ ] Returns = advantages + values
- [ ] Advantages normalizados (mean=0, std=1) antes do PPO update

### PPO Update (design.md 5.4)

- [ ] `MAPPOAgent.update(buffer)` executa o PPO update
- [ ] Clip range: 0.2 (conforme design.md 5.4)
- [ ] Policy loss: `L_clip = -min(ratio * A, clip(ratio, 1-eps, 1+eps) * A)` onde ratio = exp(log_prob_new - log_prob_old)
- [ ] Value loss: MSE entre V(s) e returns
- [ ] Entropy bonus: coeficiente 0.01 (incentiva exploracao)
- [ ] Total loss: policy_loss + 0.5 * value_loss - entropy_coeff * entropy
- [ ] Epochs por update: 4 (conforme design.md 5.4)
- [ ] Optimizer: Adam com learning rate 3e-4

### MAPPOAgent

- [ ] `MAPPOAgent(obs_size, global_state_size, num_action_types, num_targets)` cria agente com 5 policies + 1 critic
- [ ] `select_action(class_name, obs, type_mask, target_mask)` seleciona acao usando a policy da classe
- [ ] `get_value(global_state)` retorna V(s) do critic
- [ ] `save(directory)` salva 5 policies como .pt files (guerreiro.pt, mago.pt, etc.)
- [ ] `load(directory)` carrega policies de .pt files
- [ ] Formato de salvamento compativel com `models/easy/`, `models/normal/`, `models/hard/` (conforme design.md 5.5)

### Mascaramento de Acoes

- [ ] Action masking aplicado via logits: posicoes invalidas recebem -1e8 antes do softmax
- [ ] Sampling: `Categorical(logits=masked_logits).sample()`
- [ ] Log prob calculado usando a distribuicao mascarada

---

## Fora do Escopo

- Training loop completo (coleta de rollouts + updates iterativos) — feature 15
- Curriculum learning (fases 1v1→3v3) — feature 15
- Self-play pool — feature 15
- Integracao com ArenaEnv (coleta de dados do ambiente) — feature 15
- Tuning de hiperparametros — pos-treinamento
- Inference para o backend (carregamento de modelos para jogar) — feature 18
