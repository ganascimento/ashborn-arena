# Ashborn Arena — Estado de Desenvolvimento

Este arquivo mantem o estado atual do desenvolvimento de cada feature do projeto.

## Estrategia de Implementacao

1. **Game Engine** — Motor do jogo em Python puro (regras, combate, grid, habilidades)
2. **Ambiente PettingZoo** — Wrapper do engine para treinamento RL
3. **MAPPO (RL)** — Treinamento da IA multi-agente via curriculum learning
4. **Interface Visual** — 2D top-down jogavel

## Especificacao

| Area                       | Status   | Referencia                          |
| -------------------------- | -------- | ----------------------------------- |
| Mecanica de batalha        | Definida | prd.md secoes 2.1-2.6               |
| Classes e habilidades (47) | Definida | prd.md secao 3, design.md secao 2.7 |
| Atributos e formulas       | Definida | prd.md secao 5, design.md secao 3   |
| Campo de batalha           | Definido | prd.md secao 6, design.md secao 4   |
| Sistema de IA              | Definido | prd.md secao 4, design.md secao 5   |
| Interface e UX             | Definida | prd.md secao 7                      |

## Features

### Setup

| #   | Feature                     | Status    | Dep. | Spec                                                     |
| --- | --------------------------- | --------- | ---- | -------------------------------------------------------- |
| 0   | Project setup e scaffolding | concluida | —    | [features/00_project_setup/](features/00_project_setup/) |

### Game Engine (engine/)

| #   | Feature                         | Status    | Dep.  | Spec                                                                                   |
| --- | ------------------------------- | --------- | ----- | -------------------------------------------------------------------------------------- |
| 1   | Grid e movimentacao             | concluida | —     | [features/01_grid_movimentacao/](features/01_grid_movimentacao/)                       |
| 2   | Sistema de turnos e PA          | concluida | 1     | [features/02_sistema_turnos_pa/](features/02_sistema_turnos_pa/)                       |
| 3   | Atributos, modificadores e HP   | concluida | —     | [features/03_atributos_modificadores_hp/](features/03_atributos_modificadores_hp/)     |
| 4   | Pipeline de dano                | concluida | 3     | [features/04_pipeline_dano/](features/04_pipeline_dano/)                               |
| 5   | Sistema de efeitos              | concluida | 4     | [features/05_sistema_efeitos/](features/05_sistema_efeitos/)                           |
| 6   | Habilidades (47 definicoes)     | concluida | 5     | [features/06_habilidades_47/](features/06_habilidades_47/)                             |
| 7   | Status effects e elemental      | concluida | 5     | [features/07_status_effects_elemental/](features/07_status_effects_elemental/)         |
| 8   | Knockout, morte e revivificacao | concluida | 4     | [features/08_knockout_morte_revivificacao/](features/08_knockout_morte_revivificacao/) |
| 9   | Ataque de oportunidade          | concluida | 1, 4  | [features/09_ataque_oportunidade/](features/09_ataque_oportunidade/)                   |
| 10  | Objetos interativos             | concluida | 1     | [features/10_objetos_interativos/](features/10_objetos_interativos/)                   |
| 11  | Linha de visao e cobertura      | concluida | 1, 10 | [features/11_linha_visao_cobertura/](features/11_linha_visao_cobertura/)               |
| 12  | Geracao procedural de mapas     | concluida | 10    | [features/12_geracao_procedural_mapas/](features/12_geracao_procedural_mapas/)         |
| 13  | Mecanicas de combate avancadas  | concluida | 1-12  | [features/13_mecanicas_combate_avancadas/](features/13_mecanicas_combate_avancadas/)   |

### Treinamento (training/)

| #   | Feature                   | Status    | Dep. | Spec                                                                     |
| --- | ------------------------- | --------- | ---- | ------------------------------------------------------------------------ |
| 14  | Ambiente PettingZoo       | concluida | 1-13 | [features/14_ambiente_pettingzoo/](features/14_ambiente_pettingzoo/)     |
| 15  | MAPPO — redes e algoritmo | concluida | 14   | [features/15_mappo_redes_algoritmo/](features/15_mappo_redes_algoritmo/) |
| 16  | Training pipeline         | concluida | 15   | [features/16_training_pipeline/](features/16_training_pipeline/)         |

### Backend (backend/)

| #   | Feature       | Status    | Dep. | Spec                                                     |
| --- | ------------- | --------- | ---- | -------------------------------------------------------- |
| 17  | API REST      | concluida | 1-13 | [features/17_api_rest/](features/17_api_rest/)           |
| 18  | API WebSocket | concluida | 17   | [features/18_api_websocket/](features/18_api_websocket/) |
| 19  | Inference IA  | concluida | 18   | [features/19_inference_ia/](features/19_inference_ia/)   |

### Frontend (frontend/)

| #   | Feature                     | Status    | Dep. | Spec                                                                         |
| --- | --------------------------- | --------- | ---- | ---------------------------------------------------------------------------- |
| 20  | Setup — menu e preparacao   | concluida | 17   | [features/20_setup_menu_preparacao/](features/20_setup_menu_preparacao/)     |
| 21  | Batalha — grid e rendering  | concluida | 18   | [features/21_batalha_grid_rendering/](features/21_batalha_grid_rendering/)   |
| 22  | Batalha — acoes e animacoes | concluida | 21   | [features/22_batalha_acoes_animacoes/](features/22_batalha_acoes_animacoes/) |
| 23  | Batalha — HUD e feedback    | concluida | 21   | [features/23_batalha_hud_feedback/](features/23_batalha_hud_feedback/)       |
| 24  | Resultado                   | concluida | 18   | [features/24_resultado/](features/24_resultado/)                             |

### Melhorias de UX (frontend/)

| #   | Feature                          | Status    | Dep.   | Spec                                                                             |
| --- | -------------------------------- | --------- | ------ | -------------------------------------------------------------------------------- |
| 25  | Marcador do personagem ativo     | concluida | 21     | [features/25_marcador_personagem_ativo/](features/25_marcador_personagem_ativo/) |
| 26  | Correcao custo PA de movimento   | concluida | 22     | [features/26_correcao_movimento_pa/](features/26_correcao_movimento_pa/)         |
| 27  | Log de combate e ritmo da IA     | concluida | 22, 23 | [features/27_log_combate_ritmo_ia/](features/27_log_combate_ritmo_ia/)           |
| 28  | Painel de detalhes do personagem | concluida | 23     | [features/28_painel_detalhes_aliado/](features/28_painel_detalhes_aliado/)       |

### Polish e Mecanicas (engine/ + backend/ + frontend/)

| #   | Feature                       | Status    | Dep.          | Spec                                                                               |
| --- | ----------------------------- | --------- | ------------- | ---------------------------------------------------------------------------------- |
| 29  | Visual, cenario e auto-battle | concluida | 10, 11, 21-28 | [features/29_visual_cenario_auto_battle/](features/29_visual_cenario_auto_battle/) |
