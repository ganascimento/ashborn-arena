# Feature 03 — Atributos, Modificadores e HP

## Objetivo

Implementar o modelo de personagem (Character) com as 5 classes, 5 atributos primarios, sistema de modificadores (fator de corte = 5), formula de HP, e validacao do sistema de build (distribuicao de 10 pontos livres). Esta feature fornece o modelo de dominio central do engine — praticamente todas as features subsequentes (pipeline de dano, habilidades, efeitos, knockout, IA) dependem do Character para funcionar.

---

## Referencia nos Specs

- prd.md: secoes 5.1 (atributos primarios), 5.2 (atributos base e HP por classe), 5.3 (formula de HP), 5.4 (sistema de build), 5.5 (fator de corte e modificadores), 5.6 (papel defensivo dos atributos)
- design.md: secoes 3.1 (atributos primarios), 3.2 (composicao de atributos), 3.3 (modificador — fator de corte), 3.8 (formula de HP)

---

## Arquivos Envolvidos

### Criar

- `engine/models/character.py` — CharacterClass (enum), Attributes (dataclass), BASE_ATTRIBUTES (dict), BASE_HP (dict), Character (classe principal)
- `engine/tests/test_character.py` — testes unitarios do modelo de personagem

### Modificar

- `engine/models/__init__.py` — re-exportar CharacterClass, Attributes, Character

---

## Criterios de Aceitacao

### Classes

- [ ] `CharacterClass` e um enum com 5 valores: WARRIOR, MAGE, CLERIC, ARCHER, ASSASSIN
- [ ] `BASE_ATTRIBUTES` mapeia cada classe aos seus atributos base conforme prd.md 5.2:
  - Guerreiro: FOR=8, DES=4, CON=7, INT=2, SAB=4
  - Mago: FOR=2, DES=4, CON=4, INT=9, SAB=6
  - Clerigo: FOR=4, DES=3, CON=6, INT=5, SAB=8
  - Arqueiro: FOR=3, DES=9, CON=4, INT=4, SAB=5
  - Assassino: FOR=5, DES=8, CON=3, INT=4, SAB=5
- [ ] `BASE_HP` mapeia cada classe ao HP base conforme prd.md 5.2:
  - Guerreiro=50, Mago=30, Clerigo=45, Arqueiro=35, Assassino=35

### Atributos e Modificadores

- [ ] `Attributes` armazena os 5 atributos: str, dex, con, int_, wis (int_ para evitar conflito com keyword)
- [ ] `Attributes.modifier(attr_name)` retorna `atributo_final - 5` (fator de corte, conforme design.md 3.3)
- [ ] Guerreiro base: modificadores FOR=+3, DES=-1, CON=+2, INT=-3, SAB=-1
- [ ] Mago base: modificadores FOR=-3, DES=-1, CON=-1, INT=+4, SAB=+1
- [ ] Clerigo base: modificadores FOR=-1, DES=-2, CON=+1, INT=0, SAB=+3
- [ ] Arqueiro base: modificadores FOR=-2, DES=+4, CON=-1, INT=-1, SAB=0
- [ ] Assassino base: modificadores FOR=0, DES=+3, CON=-2, INT=-1, SAB=0

### Sistema de Build

- [ ] `Attributes.from_base_and_build(base, build)` cria atributos finais somando base + pontos distribuidos
- [ ] Build valido: soma dos 5 valores == 10, cada valor entre 0 e 5 (inclusive)
- [ ] Build com soma != 10 levanta ValueError
- [ ] Build com valor > 5 em um atributo levanta ValueError
- [ ] Build com valor < 0 em um atributo levanta ValueError
- [ ] Build de zeros (0, 0, 0, 0, 0) com soma != 10 levanta ValueError
- [ ] Build (5, 5, 0, 0, 0) e valido (soma = 10, nenhum > 5)
- [ ] Build (3, 2, 2, 2, 1) e valido (soma = 10)

### HP

- [ ] `Character.max_hp` segue a formula: hp_base_classe + (modificador_CON * 5) — conforme design.md 3.8
- [ ] Guerreiro sem build (CON=7, mod=+2): HP = 50 + (2 * 5) = 60
- [ ] Mago sem build (CON=4, mod=-1): HP = 30 + (-1 * 5) = 25
- [ ] Clerigo sem build (CON=6, mod=+1): HP = 45 + (1 * 5) = 50
- [ ] Arqueiro sem build (CON=4, mod=-1): HP = 35 + (-1 * 5) = 30
- [ ] Assassino sem build (CON=3, mod=-2): HP = 35 + (-2 * 5) = 25
- [ ] Guerreiro com +5 CON (CON=12, mod=+7): HP = 50 + (7 * 5) = 85
- [ ] Mago com +5 CON (CON=9, mod=+4): HP = 30 + (4 * 5) = 50
- [ ] `Character.current_hp` inicia igual a `max_hp`

### Character

- [ ] `Character(entity_id, character_class, attributes)` cria personagem com id, classe, atributos e HP calculado
- [ ] `Character.entity_id` retorna o id do personagem (str)
- [ ] `Character.character_class` retorna a classe (CharacterClass)
- [ ] `Character.attributes` retorna os atributos finais (Attributes)

---

## Fora do Escopo

- Pipeline de dano (esquiva, bloqueio, critico, resistencia magica) — feature 04
- Definicao e execucao de habilidades (scaling por atributo) — feature 06
- Status effects e sistema elemental — feature 05/07
- Knockout, morte, sangramento, revivificacao — feature 08
- Integracao com TurnManager (entity_id ja e generico) — usado nas features subsequentes
- Builds pre-definidos para IA — feature 18
