# Ashborn Arena — Notas Tecnicas

Notas sobre decisoes de implementacao, edge cases conhecidos e dividas tecnicas acumuladas durante o desenvolvimento. Consultado por `/describe-feature` ao escrever specs e atualizado por `/build-feature` ao concluir features.

---

## Edge Cases Conhecidos

### TurnManager.remove_entity no ultimo personagem

Se `remove_entity` for chamado no unico personagem restante da ordem, `_start_turn()` causa `IndexError` porque `_turn_order` fica vazio. Na pratica, a batalha ja teria terminado (condicao de vitoria), mas o combat system deve checar vitoria ANTES de chamar remove_entity no ultimo. Feature afetada: 02.

### BuffDef nao armazena scaling para efeitos computados

Efeitos como Consagracao HOT (5 + SAB * 0.5/turno) e Barreira Arcana shield (8 + INT/SAB * 1.5) tem valor base no BuffDef mas nao armazenam atributo de scaling nem fator. O combat system precisara computar o valor final usando `calculate_raw_damage(base, modifier, scaling)` e passar o resultado como `value` ao criar o Effect. Features afetadas: 06, 05.

### Chama Sagrada e Barreira Arcana — atributo dual (INT/SAB)

Essas habilidades compartilhadas entre Mago e Clerigo usam INT para Mago e SAB para Clerigo. O catalogo (feature 06) registra `damage_attr="int_"` como default. O combat system deve selecionar o atributo correto baseado na classe de quem usa a habilidade.

---

## Decisoes de Arredondamento

### calculate_raw_damage — round half up

Formula: `base_damage + math.floor(modifier * scaling + 0.5)`. Usa round-half-up (nao banker's rounding do Python) para ser consistente com a tabela de balanceamento do design.md 2.8. Exemplos verificados: Impacto Brutal (FOR+3, 1.2) = 14, Sentenca do Carrasco (FOR+3, 1.5) = 19.

---

## Limpezas Realizadas (code review pos-feature 12)

- `Grid.remove_occupant`: corrigido para limpar entradas vazias do dict `_cells` em vez de acumular listas vazias
- `get_tiles_in_line`: trocado de interpolacao com `round()` para Bresenham — interpolacao pulava tiles em angulos nao-alinhados (ex: parede em tile intermediario nao bloqueava LoS)
