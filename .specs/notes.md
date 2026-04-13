# Ashborn Arena — Notas Tecnicas

Notas sobre decisoes de implementacao e limitacoes conhecidas. Consultado por `/describe-feature` ao escrever specs e atualizado por `/build-feature` ao concluir features.

---

## Limitacoes Conhecidas (MVP)

Nenhuma limitacao pendente no game engine. Todas as mecanicas de combate foram implementadas na feature 13.

---

## Decisoes de Implementacao

### calculate_raw_damage — round half up

Formula: `base_damage + math.floor(modifier * scaling + 0.5)`. Usa round-half-up (nao banker's rounding do Python) para ser consistente com a tabela de balanceamento do design.md 2.8.

### Hierarchical action sampling

A PolicyNetwork tem dois heads (type + target) independentes, mas o sampling e sequencial: primeiro samplea o type, depois aplica a target_mask especifica daquele type. Isso garante que toda acao sampleada e valida no environment. O `evaluate_action` usa a mask armazenada no buffer (a do type selecionado).

### PPO update per-class

Cada uma das 5 policies so e atualizada com dados da sua propria classe. O buffer armazena `class_name` por timestep, `get_batches_by_class()` separa os dados, e o update itera por policy com seus proprios batches.

### Terminal reward injection

Apos cada episodio, agentes que nao receberam `done=True` durante o loop tem: (1) rewards pendentes de outros agentes acumulados, (2) VICTORY/DEFEAT injetado na ultima entry do buffer, (3) `done=True` forcado. Isso garante que o GAE sabe que o episodio terminou e que losers veem reward negativo.

### Pending rewards para multi-agent

Em ambiente AEC (1 agente por step), eventos que afetam outros agentes (ALLY_DEAD, KILL) geram rewards que sao acumulados em `pending_rewards` e somados ao reward do agente no seu proximo turno.

---

## Resolvidos

- TurnManager.remove_entity no ultimo personagem: BattleState protege contra isso (feature 13)
- Chama Sagrada/Barreira Arcana dual attr (INT/SAB): `_get_scaling_attr` seleciona SAB para Clerigo (feature 13)
- Global state size variavel: `encode_global_state` retorna tamanho fixo 972 (code review #1)
- Action-target independente: hierarchical sampling resolve (code review #1)
- Losers sem DEFEAT/-10: terminal injection resolve (code review #2)
- PPO todas policies em todos dados: per-class batching resolve (code review #3)
- Adam momentum decay: `zero_grad(set_to_none=True)` (code review #4)
- Grid.remove_occupant memory leak: limpa entradas vazias (code review engine)
- LoS interpolacao: trocado para Bresenham (code review engine)
