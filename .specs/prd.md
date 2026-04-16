# Ashborn Arena — Product Requirements Document

## 1. Visao Geral do Produto

Jogo de batalha RPG tatico por turnos com sistema de IA multi-agente treinada via aprendizado por reforco (PPO, MAAC ou similar). O jogador controla um time de personagens contra inimigos controlados pela IA, com tres niveis de dificuldade.

### 1.1 Objetivos

- Criar um sistema de combate tatico por turnos com profundidade estrategica
- Treinar agentes de IA que aprendam a jogar o jogo em diferentes niveis de habilidade
- Oferecer experiencia de batalha RPG com composicao flexivel de times

---

## 2. Mecanica de Batalha

### 2.1 Composicao de Times

- Cada lado pode ter de **1 a 3 personagens**
- Composicoes validas: 1v1, 1v2, 1v3, 2v2, 2v3, 3v3
- Qualquer combinacao e permitida desde que cada lado tenha no maximo 3
- **Nao e permitido duplicar classes** no mesmo time (ex: nao pode ter 2 Guerreiros)

### 2.2 Sistema de Turnos

- Batalhas sao por turno
- Cada personagem possui **4 pontos de acao (PA) por turno**
- Custos de acao:
  - Movimentacao (2 tiles): **1 PA**
  - Ataque basico: **2 PA**
  - Habilidades especiais: **variavel** (custo definido por habilidade)
  - Todos os custos sao inteiros: **1, 2 ou 3 PA**
- O personagem pode combinar acoes livremente dentro dos seus PA disponiveis
- **PA nao utilizado e perdido** no fim do turno (nao acumula)
- Habilidades possuem **cooldown em turnos** — sem mana, stamina ou recurso secundario
- Cooldown conta a partir do turno de uso. Exemplo: CD 3 usada no turno 1 → disponivel no turno 4
- Dois controles: **PA** limita o que fazer no turno, **cooldown** limita a frequencia de uso
- **Buffs percentuais stackam de forma aditiva** (ex: -30% + -20% = -50% dano recebido)
- **AoE causa friendly fire** — habilidades em area atingem aliados e inimigos na area de efeito
- **DOTs ignoram defesas** — sangramento e veneno aplicam dano fixo, sem bloqueio/resistencia
- **DOTs aplicam dano no fim do turno** do personagem afetado
- **Buffs/debuffs decrementam no inicio do turno** do personagem afetado (buff de 2 turnos = ativo durante 2 turnos completos)
- **Provocacao**: alvo taunted deve gastar PA atacando o provocador. Se nao consegue alcancar, deve gastar PA se movendo em direcao ao provocador. Se alcance da habilidade alcanca, deve atacar

### 2.3 Ordem de Turnos — Sistema de Iniciativa

- Cada personagem rola iniciativa individualmente no inicio da batalha
- Formula: **iniciativa = rolar(1-20) + modificador de Destreza**
- Personagens agem na ordem do maior para o menor valor de iniciativa
- Empates: personagem com maior Destreza base age primeiro; se ainda empatar, sorteio
- A ordem e definida uma vez no inicio da batalha e se mantem fixa durante todos os turnos

### 2.4 Ataque de Oportunidade

- Quando um personagem tenta **sair do alcance corpo a corpo** de um inimigo usando movimentacao normal, o inimigo realiza um **ataque de oportunidade** (ataque basico gratuito, sem custo de PA)
- Se houver **multiplos inimigos** adjacentes, **cada um** realiza seu ataque de oportunidade
- Habilidades de desengajamento (ex: Recuar, Passo Sombrio, Transposicao) **nao provocam** ataque de oportunidade
- O ataque de oportunidade ocorre **antes** do movimento ser concluido

### 2.5 Morte, Knockout e Revivificacao

Quando um personagem chega a **0 HP ou menos**, ele entra em estado **caido** ou **morto**, dependendo do dano:

**Estado Caido (HP entre 0 e -10):**

- Personagem fica no chao, nao pode agir (sem PA, sem habilidades, sem movimentacao)
- Perde **3 HP por turno** (sangramento)
- Pode ser revivido por **qualquer habilidade de cura** — a cura se aplica sobre o HP negativo
  - Exemplo: aliado a -4 HP recebe 15 de cura → volta com 11 HP (ativo)
  - Exemplo: aliado a -9 HP recebe 8 de cura → fica com -1 HP (ainda caido, mas vivo)
- Se HP chegar abaixo de -10 (por sangramento ou ataque): **morre permanentemente**

**Morte Permanente (HP abaixo de -10):**

- Pode ocorrer por **overkill** (ataque que leva direto abaixo de -10) ou por **sangramento** no estado caido
- Personagem removido da batalha, nao pode ser revivido
- Exemplo: personagem com 4 HP leva 15 de dano → -11 HP → morto de vez

**Atacar alvos caidos:**

- Inimigos **podem atacar** personagens caidos (custa PA normalmente)
- Alvos caidos **nao esquivam** (esquiva = 0%)
- **Bloqueio (CON) ainda se aplica** — a constituicao do personagem ainda resiste
- Permite finalizar alvos antes que sejam revividos

### 2.6 Sistema Elemental e Combos

Algumas habilidades possuem **tags elementais** que habilitam interacoes entre si.

**Tags elementais:**

| Tag | Habilidades |
|---|---|
| **Fogo** | Nova Flamejante, Chama Sagrada |
| **Gelo** | Toque do Inverno, Flecha Glacial |
| **Eletrico** | Arco Voltaico |
| **Veneno** | Ponta Envenenada, Toque Peconhento |

**Status Molhado:**
- Aplicado por habilidades com tag **Gelo**
- Duracao: 2 turnos

**Tabela de combos:**

| Status no alvo | Proximo hit | Efeito |
|---|---|---|
| Molhado + **Eletrico** | Arco Voltaico | +50% dano (agua conduz eletricidade) |
| Molhado + **Fogo** | Nova Flamejante, Chama Sagrada | -30% dano (agua apaga fogo) |
| Molhado + **Gelo** | Toque do Inverno, Flecha Glacial | Congela: imobiliza + nao pode agir, 1 turno |

- Combo consome o status Molhado ao ativar
- Lamina Oculta (Assassino) reconhece Molhado e Congelado como debuff (+50% dano)
- **Nota**: ao adicionar novas habilidades, revisar tags elementais e atualizar esta tabela

---

## 3. Classes

### 3.1 Classes Disponiveis (Lancamento)

| Classe        | Arquetipo                                |
| ------------- | ---------------------------------------- |
| **Guerreiro** | Combate corpo a corpo, tanque            |
| **Mago**      | Dano magico a distancia, AoE             |
| **Clerigo**   | Tanque sustentavel, suporte, cura, buffs |
| **Arqueiro**  | Dano fisico a distancia                  |
| **Assassino** | Dano burst, mobilidade                   |

### 3.2 Sistema de Habilidades

- Cada classe possui um **ataque basico** (custo 2 PA, sem cooldown)
  - **Corpo a corpo** (alcance 1 tile): Guerreiro, Clerigo, Assassino
  - **A distancia** (alcance 5 tiles): Arqueiro (fisico), Mago (magico)
- Cada classe tem uma **lista de 11 habilidades** disponivel (algumas compartilhadas entre classes)
- O jogador escolhe **5 habilidades** dessa lista para equipar no personagem (alem do ataque basico)
- Total por personagem em batalha: **1 ataque basico + 5 habilidades escolhidas = 6 acoes**

### 3.3 Habilidades — Detalhamento

> **NOTA DE IMPLEMENTACAO**: Habilidades sao o maior ponto de complexidade do jogo. Cada habilidade tem efeitos unicos, formulas de dano, condicoes e interacoes. Para viabilizar a implementacao, **toda habilidade deve ser decomposta em blocos de efeito padronizados** (Dano Direto, DOT, Cura, Buff, Debuff, Movimento, Controle, Escudo, Reflexao) com parametros numericos exatos. A lista abaixo define o design de cada habilidade — a especificacao tecnica completa com valores numericos sera feita no **design.md** usando a gramatica de efeitos.

- Total: **47 habilidades unicas** (39 exclusivas + 8 compartilhadas entre 2 classes)
- Habilidades compartilhadas podem ter eficacia diferente dependendo dos atributos de quem usa

#### Habilidades Compartilhadas

| Habilidade        | Classes  | PA  | CD  | Escala  | Alcance       | Efeito                                           |
| ----------------- | -------- | --- | --- | ------- | ------------- | ------------------------------------------------ |
| Investida         | GUE, ASS | 2   | 3   | FOR     | Corpo a corpo | Avanca ate o alvo e causa dano fisico            |
| Provocacao        | GUE, CLE | 1   | 3   | CON     | 3 tiles       | Forca o alvo a atacar o usuario por 2 turnos     |
| Corte Profundo    | GUE, ASS | 2   | 3   | FOR     | Corpo a corpo | Dano fisico e sangramento (dano por 3 turnos)    |
| Escudo Inabalavel | GUE, CLE | 1   | 4   | CON     | Pessoal       | Bloqueia completamente o proximo ataque recebido |
| Chama Sagrada     | MAG, CLE | 2   | 2   | INT/SAB | 4 tiles       | Dano magico ao alvo e cura leve ao usuario       |
| Barreira Arcana   | MAG, CLE | 1   | 3   | INT/SAB | 4 tiles       | Escudo magico no aliado que absorve dano         |
| Tiro Certeiro     | ARQ, ASS | 2   | 2   | DES     | 5 tiles       | Disparo preciso com chance de critico aumentada  |
| Recuar            | ARQ, ASS | 1   | 2   | —       | Pessoal       | Recua 2 tiles, saindo do alcance corpo a corpo   |

#### Guerreiro

Identidade: combate corpo a corpo, dano fisico consistente, resistencia.
Compartilhadas: Investida, Provocacao, Corte Profundo, Escudo Inabalavel.

| Habilidade           | PA  | CD  | Escala | Alcance             | Efeito                                                                      |
| -------------------- | --- | --- | ------ | ------------------- | --------------------------------------------------------------------------- |
| Impacto Brutal       | 2   | 2   | FOR    | Corpo a corpo       | Golpe pesado com dano fisico elevado                                        |
| Grito de Guerra      | 1   | 4   | FOR    | 2 tiles (area)      | Aumenta dano de aliados proximos por 2 turnos                               |
| Redemoinho de Aco    | 3   | 4   | FOR    | Corpo a corpo (AoE) | Dano fisico em todos os inimigos adjacentes                                 |
| Muralha de Ferro     | 1   | 3   | CON    | Pessoal             | Reduz dano recebido por 2 turnos                                            |
| Furia Implacavel     | 1   | 4   | FOR    | Pessoal             | Aumenta dano causado e recebido por 2 turnos                                |
| Sentenca do Carrasco | 3   | 5   | FOR    | Corpo a corpo       | Dano massivo. Bonus contra alvos abaixo de 30% HP                           |
| Bastiao              | 1   | 4   | CON    | Pessoal (area)      | Aliados adjacentes recebem menos dano. Guerreiro recebe mais dano. 2 turnos |

#### Mago

Identidade: dano magico a distancia, controle de area, fragilidade compensada por utilidade.
Compartilhadas: Chama Sagrada, Barreira Arcana.

| Habilidade         | PA  | CD  | Escala | Alcance       | Efeito                                                         |
| ------------------ | --- | --- | ------ | ------------- | -------------------------------------------------------------- |
| Estilhaco Arcano   | 2   | 1   | INT    | 5 tiles       | Projetil magico com dano moderado e confiavel                  |
| Nova Flamejante    | 3   | 4   | INT    | 3 tiles (AoE) | Explosao de fogo em area                                       |
| Toque do Inverno   | 2   | 3   | INT    | 4 tiles       | Dano magico e aplica lentidao por 2 turnos                     |
| Arco Voltaico      | 3   | 4   | INT    | 5 tiles       | Relampago que atinge alvo e salta para 1-2 inimigos proximos   |
| Vacuo Arcano       | 2   | 5   | INT    | 3 tiles (AoE) | Inimigos na area nao podem usar habilidades por 1 turno        |
| Transposicao       | 1   | 3   | —      | 4 tiles       | Teleporta para posicao alvo dentro do alcance                  |
| Sifao Vital        | 2   | 3   | INT    | 4 tiles       | Dano magico e recupera HP proporcional ao dano                 |
| Meteoro            | 3   | 5   | INT    | 5 tiles (AoE) | Dano magico massivo em area. Atinge no inicio do proximo turno |
| Canalizacao Arcana | 1   | 4   | INT    | Pessoal       | Aumenta dano magico. Nao pode se mover. 2 turnos               |

#### Clerigo

Identidade: tanque sustentavel, suporte, cura. Mais resistente que o Guerreiro atraves de cura e mitigacao.
Compartilhadas: Provocacao, Chama Sagrada, Escudo Inabalavel, Barreira Arcana.

| Habilidade         | PA  | CD  | Escala  | Alcance        | Efeito                                                                |
| ------------------ | --- | --- | ------- | -------------- | --------------------------------------------------------------------- |
| Toque da Aurora    | 2   | 1   | SAB     | 3 tiles        | Cura um aliado                                                        |
| Egide Sagrada      | 1   | 3   | SAB     | 3 tiles        | Aumenta defesa do aliado alvo por 2 turnos                            |
| Expurgo            | 1   | 3   | SAB     | 3 tiles        | Remove efeitos negativos de um aliado                                 |
| Consagracao        | 2   | 4   | SAB     | 3 tiles (AoE)  | Area sagrada que cura aliados dentro dela por 3 turnos                |
| Retribuicao Divina | 1   | 4   | CON/SAB | Pessoal        | Reflete parte do dano recebido ao atacante por 2 turnos               |
| Julgamento Divino  | 3   | 4   | SAB     | 4 tiles        | Dano sagrado elevado em alvo unico                                    |
| Voto de Sacrificio | 1   | 4   | CON/SAB | Pessoal (area) | Redireciona parte do dano de aliados proximos para si mesmo. 2 turnos |

#### Arqueiro

Identidade: dano fisico a distancia, precisao, controle por flechas especiais.
Compartilhadas: Tiro Certeiro, Recuar.

| Habilidade            | PA  | CD  | Escala | Alcance       | Efeito                                                             |
| --------------------- | --- | --- | ------ | ------------- | ------------------------------------------------------------------ |
| Tiro Perfurante       | 2   | 2   | DES    | 5 tiles       | Disparo que ignora parte da defesa do alvo                         |
| Chuva de Flechas      | 3   | 4   | DES    | 5 tiles (AoE) | Dano fisico em area                                                |
| Ponta Envenenada      | 2   | 3   | DES    | 5 tiles       | Dano fisico e veneno (dano por 3 turnos)                           |
| Flecha Glacial        | 2   | 3   | DES    | 5 tiles       | Dano fisico e imobiliza o alvo por 1 turno                         |
| Olho do Predador      | 1   | 4   | DES    | Pessoal       | Proximo ataque causa dano dobrado                                  |
| Rajada Dupla          | 3   | 3   | DES    | 5 tiles       | Dois disparos no mesmo ou em alvos diferentes                      |
| Armadilha Espinhosa   | 1   | 3   | DES    | 3 tiles       | Coloca armadilha em tile. Inimigo que pisar recebe dano e lentidao |
| Alcance Supremo       | 1   | 4   | —      | Pessoal       | Aumenta alcance de todos os ataques por 2 turnos                   |
| Concentracao Absoluta | 1   | 4   | DES    | Pessoal       | Aumenta critico e dano a distancia. Nao pode se mover. 2 turnos    |

#### Assassino

Identidade: burst de dano, mobilidade alta, finalizacao de alvos fracos.
Compartilhadas: Investida, Corte Profundo, Tiro Certeiro, Recuar.

| Habilidade        | PA  | CD  | Escala  | Alcance       | Efeito                                                             |
| ----------------- | --- | --- | ------- | ------------- | ------------------------------------------------------------------ |
| Lamina Oculta     | 2   | 1   | DES     | Corpo a corpo | Dano fisico com bonus se alvo estiver sob debuff                   |
| Passo Sombrio     | 1   | 3   | —       | 4 tiles       | Teleporta para as costas do alvo                                   |
| Danca das Laminas | 3   | 3   | DES/FOR | Corpo a corpo | Dois golpes rapidos no mesmo alvo                                  |
| Veu das Sombras   | 2   | 5   | —       | Pessoal       | Impossivel de ser alvo por 1 turno. Proximo ataque com dano bonus  |
| Toque Peconhento  | 1   | 4   | DES     | Pessoal       | Envenena arma: proximos 3 ataques aplicam dano adicional por turno |
| Marca da Morte    | 3   | 5   | DES/FOR | Corpo a corpo | Dano massivo. Critico garantido se alvo abaixo de 25% HP           |
| Sede de Sangue    | 1   | 4   | DES     | Pessoal       | Aumenta dano causado. Perde toda esquiva. 2 turnos                 |

> **Definido** — Especificacao numerica completa em **design.md secao 2.7**. Inclui dano_base, fator_scaling, efeitos de status, duracoes e percentuais para todas as 47 habilidades.

---

## 4. IA Multi-Agente

### 4.1 Abordagem

- Algoritmo: **MAPPO** (Multi-Agent PPO) com implementacao propria em PyTorch
- Paradigma: **CTDE** — Centralized Training, Decentralized Execution
- **1 policy por classe** (5 redes no total) — a mesma rede funciona em qualquer composicao de time
- Centralized Critic ve estado global durante treinamento; na execucao cada agente usa apenas observacao local
- Ambiente implementado como **PettingZoo** (API multi-agente padrao para RL)

### 4.2 Niveis de Dificuldade

Baseados em **checkpoints de treinamento** de diferentes fases. Sem mecanismos artificiais.

| Nivel       | Origem                            | Comportamento                                      |
| ----------- | --------------------------------- | -------------------------------------------------- |
| **Facil**   | Checkpoint da Fase 1 (1v1)        | Sabe jogar individualmente, nao coordena com time   |
| **Normal**  | Checkpoint da Fase 2-3 (2v2/3v3)  | Coordena razoavelmente, faz combos basicos          |
| **Dificil** | Checkpoint final                   | Explora sinergias, foca alvos prioritarios, combos  |

Armazenamento: 5 arquivos `.pt` por nivel (um por classe), 3 niveis = **15 arquivos**.

### 4.3 Observacao do Agente

Cada policy recebe como input:

- **Self**: classe, HP, PA restante, posicao, cooldowns das 5 habilidades, atributos finais, status ativos
- **Aliados** (2 slots fixos, masked se vazio): classe, HP, posicao, status ativos
- **Inimigos** (3 slots fixos, masked se vazio): classe, HP, posicao, status ativos
- **Mapa**: grid 10x8 flattened (tipo de objeto por tile, objetos em chamas)
- **Global**: turno atual

Visao **completa** do campo (sem fog of war) — simplifica o treinamento e o jogo ja tem complexidade suficiente.

### 4.4 Espaco de Acoes — Micro-decisoes Sequenciais

Cada turno, o agente toma **micro-decisoes ate o PA acabar**:

```
Micro-decisao:
1. Tipo: [mover, ataque_basico, habilidade_1..5, arremessar_objeto, encerrar_turno]
2. Alvo: [tile do grid (para mover/AoE) OU indice do alvo (para ataques direcionados)]
```

O agente repete micro-decisoes ate PA = 0 ou escolher "encerrar turno". Acoes invalidas sao mascaradas (habilidade em cooldown, PA insuficiente, sem LoS, etc.).

### 4.5 Funcao de Recompensa

Recompensas intermediarias para acelerar convergencia:

| Evento | Recompensa |
|---|---|
| **Vitoria** | +10 |
| **Derrota** | -10 |
| **Matar inimigo** | +3 |
| **Derrubar inimigo (caido)** | +1 |
| **Aliado morto** | -2 |
| **Dano causado** | +0.1 por ponto de dano |
| **Cura realizada** | +0.1 por ponto curado |
| **Combo elemental ativado** | +0.5 |

Valores iniciais, serao ajustados durante treinamento.

### 4.6 Treinamento — Curriculum Learning

4 fases sequenciais. Cada fase carrega os pesos da anterior.

| Fase | Composicao | Foco | Checkpoint salvo |
|---|---|---|---|
| 1 | 1v1 (todas classes) | Mecanicas basicas, habilidades, posicionamento | Facil |
| 2 | 2v2 | Coordenacao, healer cura, tank tanka | — |
| 3 | 3v3 | Coordenacao completa, combos, friendly fire | Normal |
| 4 | Composicoes mistas (1v2, 2v3) | Assimetria, adaptacao | Dificil |

### 4.7 Self-play

- Treina contra copias de si mesmo via **pool de politicas**
- Oponente selecionado aleatoriamente do pool a cada partida
- Versao atual adicionada ao pool periodicamente
- Evita overfitting contra uma unica estrategia

---

## 5. Atributos de Personagem

### 5.1 Atributos Primarios

O jogo utiliza **5 atributos primarios**. Cada um tem impacto direto nas mecanicas de combate.

| Atributo         | Sigla | Efeito no combate                                                                 |
| ---------------- | ----- | --------------------------------------------------------------------------------- |
| **Forca**        | FOR   | Dano fisico corpo a corpo, chance de aplicar efeitos fisicos (atordoar, empurrar) |
| **Destreza**     | DES   | Iniciativa, esquiva, chance de critico, dano fisico a distancia                   |
| **Constituicao** | CON   | HP maximo, resistencia a efeitos de status                                        |
| **Inteligencia** | INT   | Dano magico, eficacia de debuffs                                                  |
| **Sabedoria**    | SAB   | Poder de cura, resistencia magica, eficacia e duracao de buffs                    |

### 5.2 Atributos Base e HP por Classe

Cada classe possui uma distribuicao de atributos base que reflete sua identidade, alem de um HP base que define sua resistencia natural.

| Classe        | FOR | DES | CON | INT | SAB | HP Base |
| ------------- | --- | --- | --- | --- | --- | ------- |
| **Guerreiro** | 8   | 4   | 7   | 2   | 4   | 50      |
| **Mago**      | 2   | 4   | 4   | 9   | 6   | 30      |
| **Clerigo**   | 4   | 3   | 6   | 5   | 8   | 45      |
| **Arqueiro**  | 3   | 9   | 4   | 4   | 5   | 35      |
| **Assassino** | 5   | 8   | 3   | 4   | 5   | 35      |

### 5.3 Formula de HP

```
HP = hp_base_classe + (modificador_CON * 5)
```

- O modificador CON pode ser negativo, reduzindo o HP abaixo do base da classe
- HP por ponto de modificador: **5**

| Classe        | HP Base | CON base | Mod CON | HP sem build | HP max (+5 CON) |
| ------------- | ------- | -------- | ------- | ------------ | --------------- |
| **Guerreiro** | 50      | 7        | +2      | 60           | 85              |
| **Clerigo**   | 45      | 6        | +1      | 50           | 75              |
| **Arqueiro**  | 35      | 4        | -1      | 30           | 55              |
| **Assassino** | 35      | 3        | -2      | 25           | 50              |
| **Mago**      | 30      | 4        | -1      | 25           | 50              |

### 5.4 Sistema de Build — Distribuicao de Pontos

- O jogador recebe **10 pontos livres** para distribuir entre os 5 atributos
- Maximo de **+5 pontos adicionais** em um unico atributo
- Minimo de +0 (nao e obrigatorio investir em todos)
- Os pontos sao distribuidos na tela de preparacao, antes da batalha
- A distribuicao permite personalizar a classe (ex: Guerreiro com mais DES para agir antes, Assassino com mais FOR para burst fisico)

### 5.5 Fator de Corte e Modificadores

Todos os calculos do jogo utilizam o **modificador** do atributo, nao o valor bruto:

```
modificador = atributo_final - 5
```

- **5 e o ponto neutro** — acima de 5 = bonus, abaixo de 5 = penalidade
- Modificador negativo causa penalidades reais: menos dano, mais dano recebido, sem esquiva/critico
- Forca o jogador a montar builds com tradeoffs significativos
- Formulas completas e pipeline de resolucao de dano: ver **design.md secao 3**

### 5.6 Papel Defensivo dos Atributos

| Atributo | Papel ofensivo            | Papel defensivo                           |
| -------- | ------------------------- | ----------------------------------------- |
| FOR      | Dano corpo a corpo        | —                                         |
| DES      | Dano a distancia, critico | Esquiva (apenas fisico)                   |
| CON      | —                         | HP, bloqueio fisico, resistencia a status |
| INT      | Dano magico, debuffs      | —                                         |
| SAB      | Cura, buffs               | Resistencia magica                        |

### 5.7 Scaling de Habilidades

Cada habilidade escala com um ou dois atributos via modificador. Habilidades usam a formula:

```
efeito = valor_base + (modificador_atributo * fator_scaling)
```

> **Definido** — Valores numericos completos em **design.md secao 2.7**.

---

## 6. Campo de Batalha

### 6.1 Grid

- Grid **quadrado**, **10 colunas x 8 linhas** (80 tiles)
- Orientacao paisagem (largura > altura)
- Visao **2D top-down**
- Movimento diagonal custa o mesmo que ortogonal (1 tile = 1 tile)

### 6.2 Movimentacao

- **2 tiles por 1 PA** gasto em movimentacao
- Maximo teorico: 4 PA * 2 tiles = 8 tiles por turno (sem atacar)
- Turno tipico: 1 PA mover (2 tiles) + 2 PA ataque + 1 PA sobrando
- **Pode mover atraves de aliados**, nao pode mover atraves de inimigos ou objetos que bloqueiam

### 6.3 Zonas de Spawn

- **Time A**: colunas 1-2 (lado esquerdo)
- **Time B**: colunas 9-10 (lado direito)
- Zonas de spawn livres de objetos
- Distancia entre frentes: ~6 tiles

### 6.4 Objetos Interativos

O cenario possui objetos destrutiveis e interativos.

| Objeto          | HP  | Bloqueia mov. | Bloqueia visao | Inflamavel | Arremessavel               |
| --------------- | --- | ------------- | -------------- | ---------- | -------------------------- |
| **Caixa**       | 10  | Sim           | Sim            | Sim        | Sim                        |
| **Barril**      | 12  | Sim           | Sim            | Sim        | Sim                        |
| **Arvore**      | 20  | Sim           | Sim            | Sim        | Nao                        |
| **Arbusto**     | 5   | Nao           | Nao            | Sim        | Nao                        |
| **Rocha**       | 30  | Sim           | Sim            | Nao        | Nao (destrutivel)          |

### 6.5 Interacoes com o Cenario

**Arremessar objeto** (caixas, barris):

- Custo: 2 PA, requer estar adjacente ao objeto
- Distancia: 2 + mod_FOR tiles (minimo 1)
- Dano: base 6, FOR \* 1.0, fisico
- Objeto e destruido ao colidir

**Atacar objeto**:

- Qualquer ataque pode mirar em objeto destrutivel
- Objeto recebe dano pelo pipeline normal (sem esquiva, sem bloqueio)
- HP 0 = destruido, tile fica livre

**Fogo**:

- Habilidades de fogo (Nova Flamejante, Chama Sagrada) incendeiam objetos inflamaveis na area
- Objeto em chamas: **3 dano/turno** a personagens adjacentes, dura **3 turnos**
- Apos 3 turnos em chamas, objeto e destruido
- Fogo **nao se espalha** entre objetos

**Agua/Gelo apaga fogo**:

- Toque do Inverno, Flecha Glacial atingindo objeto em chamas: apaga o fogo
- Objeto mantem o HP atual (dano acumulado persiste), pode ser incendiado novamente

### 6.6 Linha de Visao e Cobertura

- Ataques a distancia requerem **linha de visao livre** ao alvo
- LoS: linha reta do centro do tile do atacante ao centro do tile do alvo
- Objeto com "bloqueia visao" no caminho = **projetil interceptado pelo objeto** (o objeto recebe o dano em vez do alvo)
- **AoE**: precisa de LoS ao ponto alvo (centro do efeito); se bloqueado, o objeto interceptador recebe o dano
- **Investida bloqueada**: se um objeto bloqueia o caminho da investida, o objeto recebe dano e o personagem para adjacente (ou no tile se o objeto for destruido)
- **Meteoro**: ignora LoS (vem de cima — contrapartida do delay de 1 turno)
- **Corpo a corpo**: nao requer LoS (adjacente = sempre valido)

### 6.7 Biomas

2 biomas com distribuicoes diferentes de objetos. Sem efeitos mecanicos extras no MVP.

| Bioma              | Objetos comuns                           | Caracteristica visual                   |
| ------------------ | ---------------------------------------- | --------------------------------------- |
| **Floresta (dia)** | Arvores, arbustos, rochas                | Muita cobertura, caminhos entre arvores |
| **Vila**           | Caixas, barris, rochas (muros), arbustos | Corredores e choke points               |

### 6.8 Geracao Procedural

- Mapas gerados proceduralmente a cada batalha
- **Densidade**: 12-16 objetos por mapa (~15-20% de cobertura)
- **Area de placement**: colunas 2-7, linhas 1-6 (bordas e zonas de spawn sempre livres)
- **Garantias**: minimo 2 coberturas no meio do mapa, minimo 1 corredor aberto para linha de visao

---

## 7. Interface e Experiencia

### 7.1 Plataforma e Stack

- **Plataforma**: Web (browser)
- **Frontend**: Phaser 3 + TypeScript
- **Backend**: Python + FastAPI
- **Comunicacao**:
  - **REST** (FastAPI): menu, setup de time, builds — request/response simples
  - **WebSocket** (FastAPI): batalha — bidirecional, servidor empurra acoes da IA uma a uma
- **Sem autenticacao**, sem banco de dados de usuario, sem criacao de conta

### 7.2 Persistencia — localStorage

Toda informacao do jogador e armazenada no **localStorage** do browser:
- Builds customizados (atributos + habilidades por classe)
- Preferencias (dificuldade, ultimo time usado)
- Nenhum dado pessoal e coletado ou armazenado no servidor

### 7.3 Fluxo do Jogador

```
1. Tela Inicial
   └─ Escolher dificuldade (Facil / Normal / Dificil)

2. Tela de Preparacao
   ├─ Escolher composicao do time (1-3 personagens, sem duplicar classe)
   ├─ Para cada personagem:
   │   ├─ Carregar build pre-definido OU build salvo no localStorage
   │   ├─ Ajustar distribuicao de atributos (10 pontos, cap +5)
   │   └─ Escolher 5 habilidades das 11 disponiveis
   ├─ Opcao: "IA joga por mim" (auto-battle — IA controla ambos os lados)
   └─ Confirmar e iniciar batalha

3. Tela de Batalha (WebSocket)
   ├─ Grid 2D top-down (Phaser 3)
   ├─ Turno do jogador: selecionar acoes, enviar via WS, animar resultado
   ├─ Turno da IA: servidor envia acoes uma a uma via WS
   │   ├─ Cada acao e animada antes de receber a proxima
   │   └─ Frontend controla timing das animacoes
   └─ Feedback visual: alcance, AoE, dano, status, LoS

4. Tela de Resultado
   └─ Vitoria ou derrota, resumo da batalha
```

### 7.4 Builds Pre-definidos

5 builds otimizados disponiveis como ponto de partida (1 por classe). O jogador pode usar como estao ou modificar livremente.

| Classe | Build pre-definido | Foco |
|---|---|---|
| Guerreiro | FOR +5, CON +3, DES +2 | Tank/DPS corpo a corpo |
| Mago | INT +5, SAB +3, CON +2 | Dano magico maximo |
| Clerigo | SAB +5, CON +5 | Cura e sobrevivencia |
| Arqueiro | DES +5, CON +3, FOR +2 | Dano a distancia e critico |
| Assassino | DES +5, FOR +3, CON +2 | Burst e mobilidade |

### 7.5 Feedback Visual na Batalha

- Highlight de tiles de **alcance** ao selecionar habilidade
- Preview de **area de efeito** (inclui aviso de friendly fire)
- Indicador de **LoS bloqueada** (linha vermelha)
- Numeros flutuantes de **dano** (vermelho), **cura** (verde), **critico** (amarelo)
- Barras de HP sobre cada personagem
- Icones de **status** ativos (molhado, sangramento, etc.)
- Indicador de **objetos em chamas**

### 7.6 Marcador do Personagem Ativo

O personagem cujo turno esta ativo deve ser **claramente distinguivel** de todos os outros no grid:
- **Borda pulsante** ao redor do sprite do personagem ativo (cor do time: azul jogador, vermelho IA)
- **Seta indicadora** acima do personagem ativo, visivel mesmo com HUD densa
- Ao iniciar turno de novo personagem, o marcador **transiciona suavemente** do anterior para o proximo
- O indicador de texto no topo da tela ("Turno de: X") deve exibir o **nome da classe** em portugues, nao o entity_id interno

### 7.7 Log de Combate

Painel lateral ou inferior que registra as acoes da batalha em tempo real:
- Cada entrada mostra: **quem** fez a acao, **qual** acao/habilidade, **em quem**, e o **resultado** (dano causado, cura aplicada, efeito aplicado, etc.)
- Formato resumido, uma linha por evento (ex: "Mago usou Nova Flamejante em Guerreiro — 18 dano [Fogo]")
- **Scroll automatico** para a ultima entrada, com possibilidade de rolar para cima
- Maximo de **50 entradas** visiveis (FIFO — entradas antigas saem)
- O log persiste durante toda a batalha (nao limpa entre turnos)

**Ritmo das acoes da IA:**
- Entre cada acao da IA, aguardar um **delay minimo de 800ms** (alem do tempo de animacao) para dar tempo do jogador acompanhar
- Esse delay e aplicado **apos** a animacao completar, antes de enviar o `ready` para o servidor

### 7.8 Painel de Detalhes do Aliado

Ao **clicar em um personagem aliado** no grid, exibir um painel de detalhes:
- **HP atual / HP maximo** (numerico)
- **PA restante** no turno (se for o personagem ativo)
- Lista de **efeitos ativos** com nome e duracao restante em turnos
- Lista de **habilidades** com estado de cooldown (disponivel ou "CD: X turnos")
- **Atributos finais** (base + pontos alocados)
- O painel fecha ao clicar em outro lugar ou pressionar ESC
- Clicar em um **personagem inimigo** mostra apenas HP atual/maximo e efeitos ativos (informacao limitada)

---

## 8. Definicoes Fechadas

Todas as 34 questoes resolvidas.

### Combate e Regras

1. **Ordem de turnos** — Iniciativa individual, rolar(1-20) + modificador DES. _(secao 2.3)_
2. **Movimentacao** — Grid 10x8, 2 tiles por 1 PA, diagonal custa igual, ataque de oportunidade ao sair do corpo a corpo. _(secoes 2.4, 6.1-6.2)_
3. **Alcance de ataques** — Corpo a corpo = 1 tile. Distancia = 3-5 tiles por habilidade. LoS obrigatoria, objetos bloqueiam. AoE precisa LoS ao ponto alvo. Meteoro ignora LoS. _(secao 6.6)_
4. **Dano e defesa** — Fator de corte (mod = atributo - 5). Fisico: crit (DES) + esquiva (DES) + bloqueio (CON). Magico: sempre acerta, resistencia (SAB). Pipeline completo. _(design.md secao 3.5-3.7)_
5. **Morte e knockout** — Estado caido (0 a -10 HP), sangramento 3/turno, revivificacao por cura, morte permanente abaixo de -10. Caidos podem ser atacados (sem esquiva, com bloqueio). _(secao 2.5, design.md secao 3.9)_
6. **Condicoes de vitoria** — Batalha termina quando todos os inimigos sao derrotados (mortos permanentemente). Sem limite de tempo ou objetivos alternativos.
7. **Efeitos de status** — Sangramento, veneno, lentidao, imobilizar, silenciar, taunt, molhado, congelado. DOTs stackam entre fontes, controle renova duracao. _(design.md secao 2.6)_
8. **Cooldowns** — Habilidades usam cooldown em turnos. Sem mana/stamina. _(secao 2.2)_
9. **Recurso secundario** — Apenas PA + cooldown. Sem recurso secundario. _(secao 2.2)_
10. **Acoes fracionarias** — Sem PA fracionario. Todos os custos sao valores inteiros (1, 2 ou 3 PA).
11. **Sinergia entre classes** — Sistema elemental com tags (Fogo, Gelo, Eletrico, Veneno). Status Molhado (aplicado por Gelo). 3 combos definidos. _(secao 2.6, design.md secao 2.6.1)_
12. **PA nao utilizado** — Perdido no fim do turno. Nao acumula. _(secao 2.2)_
13. **Contagem de cooldown** — Conta a partir do turno de uso. CD 3 usada no turno 1 → disponivel no turno 4. _(secao 2.2)_
14. **Stacking de buffs** — Aditivo. -30% + -20% = -50%. _(secao 2.2, design.md secao 3.6)_
15. **Friendly fire** — AoE de dano atinge aliados e inimigos. AoE de cura atinge apenas aliados. _(secao 2.2, design.md secao 3.8)_

### Classes e Habilidades

16. **Quantidade de habilidades** — 11 por classe, 47 unicas total (8 compartilhadas). _(secao 3.3)_
17. **Habilidades passivas** — Sem passivas. Todas as habilidades sao ativas (custam PA).
18. **Ultimate** — Sem ultimate separada. Habilidades de CD 5 ja cumprem esse papel.
19. **Progressao / level** — Sem progressao. Batalhas independentes.

### Mapa e Cenario

20. **Tipo de grid** — Quadrado, 10x8. _(secao 6.1)_
21. **Tamanho do mapa** — 10 colunas x 8 linhas (80 tiles). _(secao 6.1)_
22. **Terreno** — Objetos destrutiveis e interativos. Fogo, arremesso, cobertura. _(secoes 6.4-6.5)_
23. **Obstaculos** — Objetos bloqueiam movimento e/ou visao. LoS obrigatoria para ranged. _(secoes 6.4, 6.6)_
24. **Cenarios variados** — 2 biomas (Floresta, Vila), geracao procedural, 12-16 objetos. _(secoes 6.7-6.8)_

### IA e Treinamento

25. **Observacao da IA** — Visao completa do campo, sem fog of war. Input estruturado: self + aliados (2 slots) + inimigos (3 slots) + mapa flattened. _(secao 4.3, design.md secao 5.2)_
26. **Espaco de acoes** — Micro-decisoes sequenciais dentro do turno. Cada decisao: tipo (10 opcoes) + alvo (tile/indice). Mascara de acoes invalidas. _(secao 4.4, design.md secao 5.3)_
27. **Funcao de recompensa** — Intermediaria: vitoria/derrota (+/-10), kill (+3), dano/cura (+0.1/ponto), combo (+0.5). _(secao 4.5)_
28. **Self-play** — Sim, com pool de politicas. Oponente aleatorio do pool. Versao atual adicionada periodicamente. _(secao 4.7)_
29. **Niveis de dificuldade** — Checkpoints de diferentes fases do curriculum. Facil=fase1, Normal=fase2-3, Dificil=final. Sem mecanismos artificiais. _(secao 4.2)_

### Experiencia do Jogador

30. **Interface** — Web. Backend: Python + FastAPI. Frontend: Phaser 3 + TypeScript. REST para menu/setup, WebSocket para batalha (acoes da IA enviadas uma a uma). Sem autenticacao.
31. **Selecao de time** — Tela de preparacao antes da batalha. 5 builds pre-definidos (1 por classe, otimizados). Jogador pode modificar habilidades e atributos livremente. Tudo salvo em localStorage do browser.
32. **Modo de jogo** — Batalhas avulsas contra IA. Sem campanha, sem progressao, sem multiplayer. Jogador escolhe composicao do time, dificuldade e joga.
33. **Visualizacao** — 2D top-down via Phaser 3. Grid 10x8 com tilemaps, sprites por classe, animacoes de habilidades e efeitos.
34. **Feedback ao jogador** — Highlight de tiles de alcance, preview de area de efeito, indicadores de LoS bloqueada, numeros de dano/cura flutuantes, barra de HP, icones de status. _(a detalhar no design.md)_
