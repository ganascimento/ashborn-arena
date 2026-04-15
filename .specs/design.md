# Ashborn Arena — Design Document

Este arquivo contem as regras de negocio detalhadas, decisoes de design e a estrutura tecnica da aplicacao.
Enquanto o PRD define **o que** o produto faz e **por que**, este documento define **como** ele funciona internamente.

## Proposito

- Detalhar cada sistema do jogo (combate, classes, IA, mapa) com regras precisas e formulas
- Servir como referencia tecnica para implementacao
- Documentar decisoes de design e seus tradeoffs
- Definir a arquitetura de dados (estruturas, estados, transicoes)

## Estrutura Planejada

As secoes abaixo serao preenchidas conforme as definicoes do PRD forem fechadas.

### 1. Sistema de Combate

#### 1.1 Turnos e PA

- 4 PA por turno, custos inteiros (1, 2 ou 3 PA)
- PA nao utilizado e **perdido** no fim do turno (nao acumula)
- Cooldown conta a partir do turno de uso (CD 3 no turno 1 → disponivel turno 4)
- Buffs percentuais stackam de forma **aditiva** (-30% + -20% = -50%)

#### 1.2 Composicao de Times

- 1 a 3 personagens por lado
- Nao e permitido duplicar classes no mesmo time
- Composicoes: 1v1, 1v2, 1v3, 2v2, 2v3, 3v3

#### 1.3 Movimentacao

- 2 tiles por 1 PA
- Pode mover atraves de aliados, nao pode mover atraves de inimigos ou objetos bloqueantes
- Diagonal custa igual a ortogonal

#### 1.4 Timing de Efeitos

- **DOTs** (sangramento, veneno): aplicam dano no **fim do turno** do personagem afetado
- **DOTs ignoram defesas**: dano fixo, sem bloqueio/resistencia
- **Buffs/debuffs**: decrementam duracao no **inicio do turno** do personagem afetado
- Buff de 2 turnos = ativo durante 2 turnos completos do personagem, expira no inicio do 3o

#### 1.5 Provocacao (Taunt)

- Alvo taunted deve gastar PA atacando o provocador
- Se nao consegue alcancar com ataque: deve gastar PA se movendo em direcao ao provocador
- Se o alcance da habilidade alcanca o provocador: deve atacar
- Duracao: 2 turnos (definida pela habilidade Provocacao)

#### 1.6 Condicao de Vitoria

- Batalha termina quando todos os inimigos sao **mortos permanentemente** (HP < -10)
- Caidos ainda contam como vivos — precisam ser finalizados ou morrer por sangramento
- Sem limite de tempo, sem objetivos alternativos

### 2. Classes e Habilidades

#### 2.1 Sistema de Recursos

O jogo utiliza **dois sistemas** para controlar o uso de habilidades:

- **Pontos de Acao (PA)**: 4 por turno, limitam o que o personagem faz em cada turno
- **Cooldown (CD)**: em turnos, limita a frequencia de uso de cada habilidade

Nao existe mana, stamina ou recurso secundario. PA + CD sao suficientes para controlar burst e cadencia.

#### 2.2 Estrutura de Habilidades

Cada habilidade e definida por:

| Propriedade         | Descricao                                                        |
| ------------------- | ---------------------------------------------------------------- |
| Custo PA            | Pontos de acao consumidos ao usar (1-3)                          |
| Cooldown            | Turnos ate poder usar novamente (0-5)                            |
| Atributo de scaling | Qual atributo afeta a eficacia (FOR, DES, CON, INT, SAB)         |
| Alcance             | Distancia maxima para uso (corpo a corpo, X tiles, pessoal, AoE) |
| Efeito              | Dano, cura, buff, debuff, utilidade                              |

#### 2.3 Habilidades por Classe

- Cada classe possui **11 habilidades** disponiveis
- O jogador escolhe **5** para equipar (alem do ataque basico)
- **8 habilidades sao compartilhadas** entre 2 classes cada
- Total de habilidades unicas no jogo: **47**
- Lista completa com valores: ver PRD secao 3.3

#### 2.4 Ataque de Oportunidade

- Movimentacao normal para fora do alcance corpo a corpo de um inimigo provoca **ataque de oportunidade**
- O inimigo adjacente executa seu **ataque basico gratuitamente** (sem gastar PA, fora do seu turno)
- **Multiplos inimigos adjacentes** = multiplos ataques de oportunidade
- O ataque ocorre **antes** do movimento ser concluido
- **Habilidades de desengajamento nao provocam**: Recuar, Passo Sombrio, Transposicao

Isso torna o posicionamento uma decisao de alto risco — entrar no corpo a corpo e um comprometimento. Classes com mobilidade (Assassino, Arqueiro) tem ferramentas para sair sem punicao, classes sem (Mago) precisam de Transposicao ou aceitar o risco.

#### 2.5 Ataque Basico

Todas as classes possuem um ataque basico:

```
PA: 2 | CD: 0 | dano_base: 6 | scaling: 1.0
```

| Classe | Atributo | Tipo dano | Alcance | Dano (base) | Dano (max build) |
|---|---|---|---|---|---|
| Guerreiro | FOR | Fisico | 1 tile (melee) | 9 | 14 |
| Mago | INT | Magico | 5 tiles (ranged) | 10 | 15 |
| Clerigo | FOR | Fisico | 1 tile (melee) | 5 | 10 |
| Arqueiro | DES | Fisico | 5 tiles (ranged) | 10 | 15 |
| Assassino | DES | Fisico | 1 tile (melee) | 9 | 14 |

#### 2.6 Efeitos de Status

| Efeito | Descricao | Tipo |
|---|---|---|
| **Sangramento** | X dano fisico/turno | DOT |
| **Veneno** | X dano magico/turno | DOT |
| **Lentidao** | Movimentacao custa 2 PA em vez de 1 | Debuff |
| **Imobilizar** | Nao pode se mover (pode atacar/usar habilidades) | Controle |
| **Silenciar** | So pode usar ataque basico | Controle |
| **Taunt** | Forcado a atacar o provocador | Controle |

**Status elementais:**

| Efeito | Descricao | Tipo |
|---|---|---|
| **Molhado** | Aplicado por habilidades Gelo. Duracao 2 turnos | Elemental |
| **Congelado** | Imobiliza + nao pode agir, 1 turno. Resultado de combo Molhado+Gelo | Controle |

Regras de stack:
- **DOTs de fontes diferentes**: stackam independentemente
- **DOT da mesma fonte**: renova duracao, nao stacka
- **Controle/debuffs**: nova aplicacao renova duracao, nao stacka
- **Combos elementais**: consomem o status ao ativar (Molhado e removido)

#### 2.6.1 Tags Elementais e Combos

Habilidades com tag elemental:

| Tag | Habilidades |
|---|---|
| Fogo | Nova Flamejante, Chama Sagrada |
| Gelo | Toque do Inverno, Flecha Glacial |
| Eletrico | Arco Voltaico |
| Veneno | Ponta Envenenada, Toque Peconhento |

Tabela de combos:

| Status no alvo | Hit com tag | Efeito |
|---|---|---|
| Molhado + Eletrico | Arco Voltaico | +50% dano |
| Molhado + Fogo | Nova Flamejante, Chama Sagrada | -30% dano |
| Molhado + Gelo | Toque do Inverno, Flecha Glacial | Congela (imobiliza + sem acao, 1 turno) |

- Combo se aplica **apos** calculo de dano bruto, **antes** de defesas
- Lamina Oculta reconhece Molhado e Congelado como debuff para seu bonus de +50%
- **Nota**: esta tabela deve ser revisada ao adicionar novas habilidades

#### 2.7 Especificacao Numerica — Habilidades

Notacao: `base X, ATTR * Y` = dano_base X + (modificador_atributo * Y).
Para habilidades INT/SAB: Mago usa INT, Clerigo usa SAB.

##### Habilidades Compartilhadas

**Investida** (GUE, ASS) — PA: 2, CD: 3
├─ Movimento: avanco ate o alvo, max 4 tiles
└─ Dano Direto: base 10, FOR * 1.2, fisico

**Provocacao** (GUE, CLE) — PA: 1, CD: 3
└─ Controle: taunt, 2 turnos

**Corte Profundo** (GUE, ASS) — PA: 2, CD: 3
├─ Dano Direto: base 6, FOR * 0.8, fisico
└─ DOT: sangramento 4/turno, 3 turnos

**Escudo Inabalavel** (GUE, CLE) — PA: 1, CD: 4
└─ Escudo: bloqueia 100% do proximo ataque (expira em 3 turnos se nao ativado)

**Chama Sagrada** (MAG, CLE) — PA: 2, CD: 2 [Fogo]
├─ Dano Direto: base 8, (INT/SAB) * 1.0, magico
└─ Cura ao usuario: 4 + (INT/SAB) * 0.3

**Barreira Arcana** (MAG, CLE) — PA: 1, CD: 3
└─ Escudo em aliado: absorve 8 + (INT/SAB) * 1.5 dano (expira em 3 turnos)

**Tiro Certeiro** (ARQ, ASS) — PA: 2, CD: 2
├─ Dano Direto: base 8, DES * 1.0, fisico
└─ Bonus: +15% chance critico neste ataque

**Recuar** (ARQ, ASS) — PA: 1, CD: 2
└─ Movimento: recuo 2 tiles, nao provoca ataque de oportunidade

##### Guerreiro

**Impacto Brutal** — PA: 2, CD: 2
└─ Dano Direto: base 10, FOR * 1.2, fisico

**Grito de Guerra** — PA: 1, CD: 4
└─ Buff (aliados em 2 tiles): +25% dano causado, 2 turnos

**Redemoinho de Aco** — PA: 3, CD: 4
└─ Dano Direto (AoE adjacente): base 12, FOR * 1.0, fisico

**Muralha de Ferro** — PA: 1, CD: 3
└─ Buff (pessoal): -30% dano recebido, 2 turnos

**Furia Implacavel** — PA: 1, CD: 4
├─ Buff: +35% dano causado, 2 turnos
└─ Debuff (self): +20% dano recebido, 2 turnos

**Sentenca do Carrasco** — PA: 3, CD: 5
├─ Dano Direto: base 14, FOR * 1.5, fisico
└─ Bonus: +50% dano se alvo abaixo de 30% HP

**Bastiao** — PA: 1, CD: 4
├─ Buff (area): aliados adjacentes -25% dano recebido, 2 turnos
└─ Debuff (self): +20% dano recebido, 2 turnos

##### Mago

**Estilhaco Arcano** — PA: 2, CD: 1
└─ Dano Direto: base 8, INT * 1.0, magico

**Nova Flamejante** — PA: 3, CD: 4 [Fogo]
└─ Dano Direto (AoE raio 1): base 14, INT * 1.2, magico

**Toque do Inverno** — PA: 2, CD: 3 [Gelo]
├─ Dano Direto: base 8, INT * 0.8, magico
├─ Debuff: lentidao, 2 turnos
└─ Status: aplica Molhado, 2 turnos

**Arco Voltaico** — PA: 3, CD: 4 [Eletrico]
├─ Dano Direto (alvo primario): base 12, INT * 1.0, magico
└─ Cadeia: salta para ate 2 inimigos em 2 tiles, 70% do dano

**Vacuo Arcano** — PA: 2, CD: 5
└─ Controle (AoE raio 1): silenciar, 1 turno

**Transposicao** — PA: 1, CD: 3
└─ Movimento: teleporte ate 4 tiles, nao provoca ataque de oportunidade

**Sifao Vital** — PA: 2, CD: 3
├─ Dano Direto: base 8, INT * 1.0, magico
└─ Cura ao usuario: 50% do dano causado

**Meteoro** — PA: 3, CD: 5
├─ Marcacao: area (raio 1) indicada no turno de uso
└─ Dano Direto (AoE raio 1): base 20, INT * 1.5, magico — resolve no inicio do proximo turno

**Canalizacao Arcana** — PA: 1, CD: 4
├─ Buff: +40% dano magico, 2 turnos
└─ Debuff (self): nao pode se mover, 2 turnos

##### Clerigo

**Toque da Aurora** — PA: 2, CD: 1
└─ Cura: base 10, SAB * 1.5

**Egide Sagrada** — PA: 1, CD: 3
└─ Buff (aliado): -20% dano recebido, 2 turnos

**Expurgo** — PA: 1, CD: 3
└─ Remove todos debuffs e status negativos do aliado

**Consagracao** — PA: 2, CD: 4
└─ HOT (AoE raio 1): 5 + SAB * 0.5 por turno, 3 turnos

**Retribuicao Divina** — PA: 1, CD: 4
└─ Reflexao: 30% do dano recebido refletido ao atacante, 2 turnos

**Julgamento Divino** — PA: 3, CD: 4
└─ Dano Direto: base 14, SAB * 1.5, magico

**Voto de Sacrificio** — PA: 1, CD: 4
└─ Redireciona 40% do dano de aliados em 2 tiles para o usuario, 2 turnos

##### Arqueiro

**Tiro Perfurante** — PA: 2, CD: 2
├─ Dano Direto: base 8, DES * 1.0, fisico
└─ Bonus: ignora 50% do bloqueio do defensor

**Chuva de Flechas** — PA: 3, CD: 4
└─ Dano Direto (AoE raio 2): base 10, DES * 0.8, fisico

**Ponta Envenenada** — PA: 2, CD: 3 [Veneno]
├─ Dano Direto: base 6, DES * 0.8, fisico
└─ DOT: veneno 4/turno, 3 turnos

**Flecha Glacial** — PA: 2, CD: 3 [Gelo]
├─ Dano Direto: base 7, DES * 0.8, fisico
├─ Controle: imobilizar, 1 turno
└─ Status: aplica Molhado, 2 turnos

**Olho do Predador** — PA: 1, CD: 4
└─ Buff: proximo ataque causa 2x dano (100% bonus)

**Rajada Dupla** — PA: 3, CD: 3
└─ Dano Direto x2: base 7 cada, DES * 0.8 cada, fisico — alvos podem ser diferentes

**Armadilha Espinhosa** — PA: 1, CD: 3
├─ Coloca armadilha em tile (dura 5 turnos ou ate ativada)
└─ Ao ativar: base 6, DES * 0.5, fisico + lentidao 2 turnos

**Alcance Supremo** — PA: 1, CD: 4
└─ Buff: +2 tiles de alcance em ataques a distancia, 2 turnos

**Concentracao Absoluta** — PA: 1, CD: 4
├─ Buff: +15% chance critico, +30% dano a distancia, 2 turnos
└─ Debuff (self): nao pode se mover, 2 turnos

##### Assassino

**Lamina Oculta** — PA: 2, CD: 1
├─ Dano Direto: base 7, DES * 1.0, fisico
└─ Bonus: +50% dano se alvo sob debuff ou status negativo

**Passo Sombrio** — PA: 1, CD: 3
└─ Movimento: teleporte para costas do alvo, max 4 tiles, nao provoca ataque de oportunidade

**Danca das Laminas** — PA: 3, CD: 3
└─ Dano Direto x2: base 7 cada, DES * 1.0 cada, fisico — mesmo alvo

**Veu das Sombras** — PA: 2, CD: 5
├─ Buff: impossivel de ser alvo, 1 turno
└─ Bonus: proximo ataque causa +50% dano

**Toque Peconhento** — PA: 1, CD: 4 [Veneno]
└─ Buff: proximos 3 ataques aplicam DOT veneno 3/turno, 2 turnos por stack

**Marca da Morte** — PA: 3, CD: 5
├─ Dano Direto: base 16, DES * 1.5, fisico
└─ Bonus: critico garantido (1.5x) se alvo abaixo de 25% HP

**Sede de Sangue** — PA: 1, CD: 4
├─ Buff: +35% dano causado, 2 turnos
└─ Debuff (self): esquiva reduzida a 0%, 2 turnos

#### 2.8 Referencia de Balanceamento

Exemplos com modificadores base (sem pontos distribuidos):

**Dano single target (sem crit):**

| Habilidade | Classe | Mod | Dano |
|---|---|---|---|
| Ataque Basico | Guerreiro (FOR +3) | 1.0 | 9 |
| Ataque Basico | Mago (INT +4) | 1.0 | 10 |
| Impacto Brutal | Guerreiro (FOR +3) | 1.2 | 14 |
| Estilhaco Arcano | Mago (INT +4) | 1.0 | 12 |
| Tiro Certeiro | Arqueiro (DES +4) | 1.0 | 12 |
| Lamina Oculta | Assassino (DES +3) | 1.0 | 10 (15 c/ debuff) |
| Sentenca do Carrasco | Guerreiro (FOR +3) | 1.5 | 19 (28 execute) |
| Meteoro | Mago (INT +4) | 1.5 | 26/alvo (adiado) |
| Marca da Morte | Assassino (DES +3) | 1.5 | 21 (31 execute) |

**Cura:**

| Habilidade | Classe | Valor |
|---|---|---|
| Toque da Aurora | Clerigo (SAB +3) | 15 HP |
| Consagracao | Clerigo (SAB +3) | 7/turno (21 total) |
| Chama Sagrada | Clerigo (SAB +3) | 5 HP (auto-cura) |
| Sifao Vital | Mago (INT +4) | 6 HP (50% de 12 dano) |

**Turnos para abater (ataque basico, sem buff/cura):**

| Atacante vs Alvo | Dano/hit | HP alvo | Hits |
|---|---|---|---|
| GUE vs Mago (sem build) | 9 +1 (bloq -1) = 10 | 25 | ~3 |
| GUE vs Guerreiro | 9 -2 (bloq +2) = 7 | 60 | ~9 |
| MAG vs Guerreiro | 10 +1 (res -1) = 11 | 60 | ~6 |
| MAG vs Assassino | 10 -0 (res 0) = 10 | 25 | ~3 |
| ARQ vs Clerigo | 10 -1 (bloq +1) = 9 | 50 | ~6 |

### 3. Atributos e Formulas

#### 3.1 Atributos Primarios

5 atributos: **FOR**, **DES**, **CON**, **INT**, **SAB**.

| Atributo | Efeitos mecanicos                                                              |
| -------- | ------------------------------------------------------------------------------ |
| FOR      | Dano fisico corpo a corpo, chance de efeitos fisicos (atordoar, empurrar)      |
| DES      | Modificador de iniciativa, esquiva, chance de critico, dano fisico a distancia |
| CON      | HP maximo, resistencia a efeitos de status                                     |
| INT      | Dano magico, eficacia de debuffs                                               |
| SAB      | Poder de cura, resistencia magica, eficacia e duracao de buffs                 |

#### 3.2 Composicao de Atributos

O atributo final de um personagem e calculado como:

```
atributo_final = atributo_base_classe + pontos_distribuidos
```

- **Atributos base**: definidos por classe (ver PRD secao 5.2)
- **Pontos livres**: 10 pontos para distribuir
- **Cap**: maximo +5 em um unico atributo
- **Range possivel**: atributo base da classe ate atributo base + 5

#### 3.3 Modificador de Atributo — Fator de Corte

Todos os calculos do jogo utilizam o **modificador**, nao o atributo bruto:

```
modificador = atributo_final - 5
```

O valor **5 e o ponto neutro**. Acima de 5 = vantagem, abaixo de 5 = penalidade.

| Atributo Final | Modificador | Impacto               |
| -------------- | ----------- | --------------------- |
| 2              | -3          | Penalidade forte      |
| 4              | -1          | Penalidade leve       |
| 5              | 0           | Neutro                |
| 8              | +3          | Bonus bom             |
| 10             | +5          | Bonus forte           |
| 14             | +9          | Bonus maximo possivel |

Modificadores por classe (sem pontos distribuidos):

| Classe    | FOR | DES | CON | INT | SAB |
| --------- | --- | --- | --- | --- | --- |
| Guerreiro | +3  | -1  | +2  | -3  | -1  |
| Mago      | -3  | -1  | -1  | +4  | +1  |
| Clerigo   | -1  | -2  | +1  | 0   | +3  |
| Arqueiro  | -2  | +4  | -1  | -1  | 0   |
| Assassino | 0   | +3  | -2  | -1  | 0   |

Consequencias do fator de corte:

- Modificador **positivo**: soma dano, aumenta chance, reduz dano recebido
- Modificador **negativo**: reduz dano causado, aumenta dano recebido, sem esquiva/critico
- Forcam o jogador a escolher: corrigir fraquezas ou maximizar forcas

#### 3.4 Sistema de Iniciativa

```
iniciativa = rolar(1, 20) + modificador_DES
```

Exemplos:

- Clerigo (DES 3, mod -2): rola 1-20, resultado efetivo -1 a 18
- Arqueiro (DES 9, mod +4): rola 1-20, resultado efetivo 5 a 24
- Arqueiro com +5 DES (DES 14, mod +9): resultado efetivo 10 a 29

- Ordem de acao: maior iniciativa age primeiro
- Desempate: maior DES base > sorteio
- Calculada uma vez no inicio da batalha, fixa para todos os turnos

#### 3.5 Tipos de Dano

| Tipo       | Atributo ofensivo                      | Defesas aplicaveis               |
| ---------- | -------------------------------------- | -------------------------------- |
| **Fisico** | FOR (corpo a corpo) ou DES (distancia) | Esquiva + Bloqueio               |
| **Magico** | INT                                    | Resistencia Magica (sem esquiva) |

Diferenca fundamental:

- **Fisico**: alta variancia — pode errar (esquiva), pode critar
- **Magico**: consistente — sempre acerta, sem critico, compensado por AoE

#### 3.6 Formulas de Combate

**Dano bruto:**

```
dano_bruto = dano_base_habilidade + (modificador_atributo * fator_scaling)
```

**Critico (apenas dano fisico):**

```
chance_critico = max(0, modificador_DES * 2%)
multiplicador_critico = 1.5x
```

- Range: 0% (DES <= 5) ate 18% (DES 14)
- Apenas ataques fisicos podem critar

**Esquiva (apenas dano fisico):**

```
chance_esquiva = max(0, modificador_DES_defensor * 3%)
```

- Range: 0% (DES <= 5) ate 27% (DES 14)
- Evita o ataque completamente
- Nao funciona contra magia

**Bloqueio (apenas dano fisico):**

```
bloqueio = modificador_CON_defensor
```

- Reducao fixa subtraida do dano
- Modificador negativo = recebe MAIS dano fisico
- Range: -2 (CON 3) ate +7 (CON 12)

**Resistencia Magica (apenas dano magico):**

```
resistencia_magica = modificador_SAB_defensor
```

- Equivalente ao bloqueio, mas para dano magico
- Modificador negativo = recebe MAIS dano magico
- Range: -1 (SAB 4) ate +8 (SAB 13)

**Reducao de Dano (buffs/habilidades ativas):**

```
reducao_percentual = valor definido pela habilidade (ex: Muralha de Ferro = 30%)
```

- Vem de habilidades, nao de atributos
- Aplicada apos bloqueio/resistencia
- Nao e passiva — precisa ser ativada
- **Stacking aditivo**: multiplos buffs somam (ex: -30% + -20% = -50%)

#### 3.7 Pipeline de Resolucao de Dano

**Ataque fisico:**

```
1. Calcular dano_bruto = base + (modificador_ataque * scaling)
2. Checar critico: max(0, mod_DES_atacante * 2%) → se sim: dano_bruto *= 1.5
3. Checar esquiva: max(0, mod_DES_defensor * 3%) → se esquivou: dano = 0, FIM
4. Subtrair bloqueio: dano = dano_bruto - mod_CON_defensor
5. Aplicar reducoes % de buffs ativos: dano *= (1 - reducao%)
6. Dano minimo: max(dano, 1)
```

**Ataque magico:**

```
1. Calcular dano_bruto = base + (modificador_INT * scaling)
2. Sempre acerta (sem esquiva, sem critico)
3. Subtrair resistencia: dano = dano_bruto - mod_SAB_defensor
4. Aplicar reducoes % de buffs ativos: dano *= (1 - reducao%)
5. Dano minimo: max(dano, 1)
```

**Cura:**

```
1. Calcular cura_bruta = base + (modificador_SAB * scaling)
2. Aplicar ao alvo (nao excede HP maximo)
```

#### 3.8 Formula de HP

```
HP = hp_base_classe + (modificador_CON * 5)
```

- `hp_base_classe`: valor fixo por classe (reflete resistencia natural)
- `modificador_CON`: CON_final - 5 (fator de corte)
- HP por ponto de modificador: **5**
- Modificador negativo reduz HP abaixo do base

| Classe    | HP Base | Mod CON (base) | HP sem build | HP max (+5 CON) |
|---|---|---|---|---|
| Guerreiro | 50 | +2 | 60 | 85 |
| Clerigo   | 45 | +1 | 50 | 75 |
| Arqueiro  | 35 | -1 | 30 | 55 |
| Assassino | 35 | -2 | 25 | 50 |
| Mago      | 30 | -1 | 25 | 50 |

O gap e significativo: Guerreiro base (60) tem quase 2.5x o HP de um Mago base (25). Isso forca o Mago a depender de posicionamento, Transposicao e Barreira Arcana para sobreviver.

#### 3.9 Knockout e Morte

**Threshold de morte**: **-10 HP**

```
HP > 0        → ativo (age normalmente)
0 >= HP >= -10 → caido (knockout)
HP < -10       → morto permanentemente
```

**Estado caido:**
- Nao pode agir (sem PA, sem habilidades, sem movimentacao)
- Perde 3 HP/turno (sangramento automatico, inicio do turno do personagem)
- Pode ser alvo de ataques: sem esquiva (0%), bloqueio (CON) se aplica
- Pode ser revivido por qualquer habilidade de cura

**Revivificacao:**
```
hp_apos_cura = hp_atual_negativo + valor_da_cura
se hp_apos_cura > 0 → personagem volta ao estado ativo com hp_apos_cura
se hp_apos_cura <= 0 → continua caido com hp_apos_cura (mas ainda vivo se >= -10)
```

**Morte permanente:**
- Overkill: ataque leva HP direto abaixo de -10
- Sangramento: HP cai abaixo de -10 durante estado caido
- Finalizacao: ataque a caido leva HP abaixo de -10
- Personagem removido da batalha, tile fica livre

**Janela de revivificacao:**

| HP ao cair | Turnos ate morrer |
|---|---|
| 0 a -1 | 3 turnos |
| -2 a -4 | 2 turnos |
| -5 a -7 | 1 turno |
| -8 a -10 | Ultimo turno (reviver agora ou morre) |
| -11+ | Morto de vez |

#### 3.10 Area de Efeito

Habilidades podem ter diferentes formatos de targeting:

| Formato                    | Descricao                                             | Exemplo                                             |
| -------------------------- | ----------------------------------------------------- | --------------------------------------------------- |
| **Alvo unico**             | 1 alvo a X tiles de distancia                         | Impacto Brutal, Tiro Perfurante                     |
| **Adjacente**              | Todos os tiles ao redor do usuario (1 tile)           | Redemoinho de Aco                                   |
| **Area circular (raio R)** | Todos dentro de R tiles do ponto alvo                 | Nova Flamejante (raio 1), Chuva de Flechas (raio 2) |
| **Cadeia (N alvos)**       | Atinge alvo primario + salta para N inimigos proximos | Arco Voltaico (cadeia 2)                            |

Regras de AoE:

- **Friendly fire**: AoE de dano atinge **aliados e inimigos** na area — posicionamento e critico
- AoE de cura (Consagracao) tambem afeta apenas aliados na area
- **Esquiva nao se aplica** contra AoE — nao ha como desviar de uma area inteira
- **Bloqueio e resistencia** se aplicam individualmente para cada alvo atingido
- Cadeia (Arco Voltaico) so salta para **inimigos** (excecao ao friendly fire)

#### 3.11 Ataque de Oportunidade

- Movimentacao normal para fora do alcance corpo a corpo de um inimigo provoca **ataque de oportunidade**
- O inimigo adjacente executa seu **ataque basico gratuitamente** (sem gastar PA, fora do seu turno)
- **Multiplos inimigos adjacentes** = multiplos ataques de oportunidade
- O ataque ocorre **antes** do movimento ser concluido
- **Habilidades de desengajamento nao provocam**: Recuar, Passo Sombrio, Transposicao
- Ataque de oportunidade segue o pipeline de dano fisico normalmente (pode critar, pode ser esquivado)

> Valores numericos definidos na secao 2.7. Referencia de balanceamento na secao 2.8.

### 4. Campo de Batalha

#### 4.1 Grid e Movimentacao

- Grid quadrado: **10 colunas x 8 linhas** (80 tiles)
- Movimento: **2 tiles por 1 PA**
- Diagonal custa igual a ortogonal
- Zona de spawn Time A: colunas 1-2 | Time B: colunas 9-10 (livres de objetos)

#### 4.2 Objetos Interativos

Cada objeto possui propriedades que definem seu comportamento:

| Objeto | HP | Bloqueia mov. | Bloqueia LoS | Inflamavel | Arremessavel |
|---|---|---|---|---|---|
| Caixa | 10 | Sim | Sim | Sim | Sim |
| Barril | 12 | Sim | Sim | Sim | Sim |
| Arvore | 20 | Sim | Sim | Sim | Nao |
| Arbusto | 5 | Nao | Nao | Sim | Nao |
| Rocha | — | Sim | Sim | Nao | Nao |
| Poca | — | Nao | Nao | Nao | Nao |

**Arremessar** (caixas, barris):
- PA: 2, requer adjacencia
- Distancia: 2 + mod_FOR tiles (min 1)
- Dano: base 6, FOR * 1.0, fisico
- Objeto destruido ao colidir

**Atacar objeto**:
- Pipeline normal, sem esquiva, sem bloqueio
- HP 0 = destruido, tile livre

**Fogo**:
- Habilidades de fogo incendeiam objetos inflamaveis na area de efeito
- Objeto em chamas: 3 dano/turno a personagens adjacentes, 3 turnos
- Apos 3 turnos: objeto destruido
- Fogo nao se espalha entre objetos

**Agua/Gelo extingue fogo**:
- Habilidades de gelo/agua apagam fogo em objetos atingidos
- HP do objeto mantem estado atual

#### 4.3 Linha de Visao (LoS)

- Ataques a distancia requerem LoS livre
- Calculo: linha reta centro-a-centro entre tiles do atacante e alvo
- Objeto com "bloqueia LoS" no caminho = ataque bloqueado
- **AoE**: requer LoS ao ponto alvo (centro do efeito), efeito expande normalmente (pode atingir atras de cobertura)
- **Meteoro**: ignora LoS (ataque aereo, delay de 1 turno como contrapartida)
- **Corpo a corpo**: nao requer LoS (adjacente = sempre valido)

#### 4.4 Geracao Procedural

- Mapas gerados a cada batalha
- Semi-simetrico: espelhado no eixo central (colunas 5-6) com variacoes
- Densidade: 12-16 objetos (~15-20% cobertura)
- Zonas de spawn sempre livres
- Garantias: min 2 coberturas no meio, min 1 corredor aberto

#### 4.5 Biomas

4 biomas definem o pool de objetos disponivel para a geracao:

| Bioma | Pool de objetos | Tendencia |
|---|---|---|
| Floresta (dia) | Arvores, arbustos, rochas, pocas | Alta cobertura, caminhos entre arvores |
| Floresta (noite) | Mesmo pool | Variante visual (sem efeito mecanico no MVP) |
| Vila | Caixas, barris, rochas, arbustos | Corredores, choke points |
| Pantano | Pocas, arbustos, arvores esparsas | Area aberta, pocas neutralizam fogo |

### 5. Sistema de IA

#### 5.1 Arquitetura das Redes

5 policy networks (uma por classe) + 1 centralized critic.

**Policy Network (por classe):**
```
Input: observacao local (self + aliados + inimigos + mapa)
→ MLP: 2 camadas ocultas, 128 neuronios cada, ReLU
→ Output: distribuicao de probabilidade sobre acoes validas
```

**Centralized Critic (compartilhado):**
```
Input: estado global completo (todos agentes + mapa inteiro)
→ MLP: 2 camadas ocultas, 256 neuronios cada, ReLU
→ Output: valor estimado do estado (V(s))
```

Redes mantidas pequenas para viabilizar treinamento em CPU (2 cores, 8GB RAM).

#### 5.2 Representacao do Estado

**Observacao local (input da policy):**

| Componente | Dimensao | Conteudo |
|---|---|---|
| Self | ~20 | classe (one-hot 5), HP, PA, posicao (x,y), cooldowns (5), atributos (5), status flags |
| Aliado 1 | ~12 | classe, HP, posicao, status flags (masked se ausente) |
| Aliado 2 | ~12 | idem |
| Inimigo 1 | ~12 | idem |
| Inimigo 2 | ~12 | idem |
| Inimigo 3 | ~12 | idem |
| Mapa | 80 | grid 10x8 flattened (tipo objeto por tile + flags: chamas, armadilha) |

Total: ~160 valores. Compacto o suficiente para MLPs pequenas.

**Estado global (input do critic):**
- Todas observacoes locais concatenadas + informacoes ocultas (cooldowns de todos, etc.)

#### 5.3 Espaco de Acoes

Acoes discretas em dois passos por micro-decisao:

```
Passo 1 — Tipo (10 opcoes):
[mover, ataque_basico, hab_1, hab_2, hab_3, hab_4, hab_5, arremessar, encerrar_turno, passar]

Passo 2 — Alvo (80 opcoes max):
[tile (x,y) do grid] — para mover, AoE, arremessar
[indice do alvo] — para ataques direcionados (inimigo/aliado)
```

**Mascara de acoes invalidas** aplicada antes do softmax:
- Habilidade em cooldown → masked
- PA insuficiente → masked
- Alvo sem LoS → masked
- Fora de alcance → masked

#### 5.4 Pipeline de Treinamento

```
Fase 1 (1v1) → salva checkpoint_easy
       ↓ (carrega pesos)
Fase 2 (2v2) → treina
       ↓
Fase 3 (3v3) → salva checkpoint_normal
       ↓
Fase 4 (misto) → salva checkpoint_hard
```

Cada fase: self-play com pool de politicas, MAPPO update.

**Hiperparametros iniciais:**
- Learning rate: 3e-4
- Clip range (PPO): 0.2
- Discount (gamma): 0.99
- GAE lambda: 0.95
- Batch size: 64
- Epochs por update: 4
- Ajustar conforme convergencia

#### 5.5 Armazenamento de Modelos

```
models/
├── easy/
│   ├── guerreiro.pt
│   ├── mago.pt
│   ├── clerigo.pt
│   ├── arqueiro.pt
│   └── assassino.pt
├── normal/
│   └── (mesma estrutura)
└── hard/
    └── (mesma estrutura)
```

### 6. Arquitetura da Aplicacao

#### 6.1 Visao Geral

```
┌─ Frontend (Phaser 3 + TypeScript) ─────────┐
│  Menu/Setup ◄── REST ──► FastAPI            │
│  Batalha    ◄── WS ────► FastAPI            │
│  localStorage (builds, preferencias)        │
└─────────────────────────────────────────────┘

┌─ Backend (Python) ─────────────────────────┐
│  FastAPI                                    │
│  ├─ REST: /builds, /start-battle            │
│  └─ WS: /battle/{id}                        │
│  Game Engine (regras, combate, grid)        │
│  MAPPO Inference (PyTorch, 5 policies .pt)  │
└─────────────────────────────────────────────┘
```

#### 6.2 Protocolo de Comunicacao

**REST** (menu, setup):
- `GET /builds/defaults` — retorna 5 builds pre-definidos
- `POST /battle/start` — envia composicao + builds, cria sessao de batalha

**WebSocket** (batalha):

Conexao: `ws://host/battle/{session_id}`

Mensagens do **cliente → servidor** (acao do jogador):
```json
{ "type": "action", "character": "guerreiro_p1", "action": "move", "target": [5, 3] }
{ "type": "action", "character": "guerreiro_p1", "action": "ability", "ability": "impacto_brutal", "target": "mago_ia" }
{ "type": "action", "character": "guerreiro_p1", "action": "end_turn" }
{ "type": "ready" }
```

Mensagens do **servidor → cliente** (resultado + turno da IA):
```json
{ "type": "action_result", "character": "guerreiro_p1", "action": "move", "from": [3,3], "to": [5,3] }
{ "type": "action_result", "character": "guerreiro_p1", "action": "ability", "ability": "impacto_brutal", "target": "mago_ia", "damage": 14, "crit": false }
{ "type": "turn_start", "character": "assassino_ia" }
{ "type": "ai_action", "character": "assassino_ia", "action": "move", "from": [8,4], "to": [6,4] }
{ "type": "ai_action", "character": "assassino_ia", "action": "ability", "ability": "lamina_oculta", "target": "mago_p1", "damage": 15 }
{ "type": "turn_end", "character": "assassino_ia", "next": "clerigo_p1" }
{ "type": "battle_end", "result": "victory" }
```

**Fluxo do turno da IA:**
1. Servidor calcula todas as micro-acoes do personagem IA
2. Envia cada acao como mensagem WS separada
3. Frontend recebe, anima, e envia `{ "type": "ready" }` quando terminar a animacao
4. Servidor envia a proxima acao
5. Repete ate o turno acabar

Isso garante que o jogador ve cada acao individualmente com animacao completa.

### 7. Interface e Experiencia

Estrutura de telas e feedback geral definidos no PRD secao 7. Abaixo, specs tecnicas dos componentes de UI implementados apos playtesting.

#### 7.1 Marcador do Personagem Ativo

**Componente visual:** anel pulsante + seta indicadora

- Anel: `Phaser.GameObjects.Arc` com stroke, animado via tween de escala (1.0 → 1.15, yo-yo, loop infinito, duracao 600ms)
- Seta: triangulo acima do sprite, offset Y = -40px do centro do container, mesma animacao de flutuacao (y +-4px, yo-yo, duracao 800ms)
- Cor: `0x4488ff` (jogador) ou `0xff4444` (IA)
- Transicao: ao mudar turno, destruir marcador atual e criar no novo personagem (sem animacao de transicao — instantaneo)
- Texto do turn indicator: traduzir entity_id para nome da classe via lookup `CLASS_DISPLAY` (ja existente nos scenes)

#### 7.2 Correcao do Custo de PA por Movimento

A regra de **2 tiles por 1 PA** (prd.md secao 6.2) deve funcionar da seguinte forma:

- O jogador clica em um tile destino. O **backend** calcula o caminho e o custo total
- O `action_result` do servidor **ja retorna o custo correto** nos eventos — o problema e que o frontend calcula PA localmente de forma errada
- **Frontend fix**: no `updatePAFromAction`, o calculo de custo de movimento deve usar `Math.ceil(distancia_total / 2)` sobre a distancia total do caminho, nao sobre cada segmento individual
- O frontend deve enviar um unico comando `move` com o tile destino final; o backend resolve o pathfinding e retorna o custo
- **Validacao**: o backend ja aplica a regra correta (1 PA = 2 tiles). O frontend so precisa refletir o PA retornado pelo servidor

**Sugestao de implementacao**: usar `pa_remaining` do `turn_start` como source of truth e, em `action_result`, deduzir o custo baseado nos eventos retornados pelo servidor, recalculando a distancia total do path (nao por segmento)

#### 7.3 Log de Combate

**Componente:** `BattleCombatLog` — painel na lateral direita ou inferior da tela de batalha

**Layout:**
- Posicao: lateral direita, abaixo da ability bar (x: 700, y apos ability bar)
- Tamanho: ~300px largura, ~200px altura
- Background: retangulo semi-transparente (`0x1a1a2e`, alpha 0.85)
- Texto: monospace 12px, cor `#cccccc`
- Scroll: manter array de strings, renderizar as ultimas N que cabem na area visivel
- Maximo: 50 entradas (FIFO)

**Formato das entradas:**
```
[Turno {n}] {Classe} usou {Habilidade} em {Alvo} — {resultado}
```

Exemplos:
```
[Turno 3] Mago usou Nova Flamejante em Guerreiro — 18 dano [Fogo]
[Turno 3] Guerreiro moveu para (5,3)
[Turno 4] Clerigo usou Luz Restauradora em Mago — +12 cura
[Turno 4] Assassino sofreu 3 dano (sangramento)
```

**Mapeamento de eventos para log:**
- `move` / `ability_movement` → "{Classe} moveu para ({x},{y})"
- `basic_attack` → "{Classe} atacou {Alvo} — {dano} dano"
- `ability` → "{Classe} usou {nome_habilidade} em {Alvo} — {dano} dano" ou "{cura} cura"
- `aoe_hit` → "{Alvo} recebeu {dano} dano [AoE]"
- `bleed` / `dot_tick` → "{Classe} sofreu {dano} dano ({tipo_efeito})"
- `heal` / `hot_tick` → "{Classe} recuperou {cura} HP"
- `knocked_out` → "{Classe} foi nocauteado!"
- `death` → "{Classe} morreu!"
- `effect_applied` → "{Classe} recebeu efeito: {tag}"
- `effect_expired` → "Efeito {tag} expirou em {Classe}"

**Ritmo da IA:**
- Apos cada `ai_action` ser animada, aplicar `await delay(800)` antes de enviar `ready`
- Isso garante que o jogador tem tempo de ler o log e observar a animacao

#### 7.4 Painel de Detalhes do Personagem

**Componente:** `CharacterDetailPanel` — overlay ativado por clique

**Ativacao:**
- Clique em sprite de **aliado**: painel completo
- Clique em sprite de **inimigo**: painel reduzido
- Fechar: clique fora do painel, tecla ESC, ou clique em outro personagem

**Layout aliado (painel completo):**
```
┌─────────────────────────────┐
│  Guerreiro         HP: 45/85│
│  PA: 2/4                    │
│─────────────────────────────│
│  FOR: 13 (+8)   DES: 6 (+1)│
│  CON: 10 (+5)   INT: 2 (-3)│
│  SAB: 4 (-1)               │
│─────────────────────────────│
│  Efeitos:                   │
│    Sangramento (2 turnos)   │
│    Lentidao (1 turno)       │
│─────────────────────────────│
│  Habilidades:               │
│    Impacto Brutal    OK     │
│    Investida         CD: 2  │
│    Corte Profundo    OK     │
│    Muralha de Ferro  CD: 1  │
│    Grito de Guerra   OK     │
└─────────────────────────────┘
```

**Layout inimigo (painel reduzido):**
```
┌─────────────────────────────┐
│  Mago              HP: 22/55│
│─────────────────────────────│
│  Efeitos:                   │
│    Molhado (3 turnos)       │
└─────────────────────────────┘
```

**Implementacao:**
- Container Phaser com depth alto (300+) para ficar acima de tudo
- Posicao: centralizado na tela ou ao lado do personagem clicado
- Background: retangulo solido `0x1a1a2e` com borda `0x4488ff` (aliado) ou `0xff4444` (inimigo)
- Dados de cooldown: ler do `playerCooldowns` map existente no BattleScene
- Dados de efeitos: ler do `activeEffects` map existente no BattleScene
- Dados de atributos: ler do `CharacterOut.attributes` ja armazenado
