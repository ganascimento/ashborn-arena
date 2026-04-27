# Tasks — Feature 30: Cenario Noturno Compartilhado em Menu e Preparacao

## Antes de Comecar

Leitura obrigatoria antes de implementar:

- `CLAUDE.md` — convencoes, stack
- `.specs/features/30_cenario_noturno_compartilhado/spec.md` — criterios de aceitacao
- `frontend/src/scenes/ui-utils.ts` — helpers existentes (`drawPanel`, `createParticleTexture`)
- `frontend/src/scenes/MenuScene.ts` — cena alvo do refactor
- `frontend/src/scenes/PreparationScene.ts` — cena que ganha o cenario
- `frontend/src/network/storage.ts` — `loadDifficulty` (origem do valor exibido no label)

---

## Plano de Execucao

3 grupos sequenciais. Sem TDD — mudanca e primariamente visual e de composicao de cena.

---

### Grupo 1 — Helpers de cenario em `ui-utils.ts`

**Tarefa:** Implementar a geracao do cenario noturno como funcao reutilizavel.

1. Em `frontend/src/scenes/ui-utils.ts`, adicionar:

   - Constante interna `PIXEL = 4` (escala pixel-art)
   - Funcao privada `drawPixelDisk(gfx, cx, cy, radius, pixel)`:
     - Desenha um disco preenchido em "pixel art" (varredura por blocos `pixel x pixel`)
   - Funcao privada `drawMountainRange(gfx, width, baseY, peakHeight, octaves, seed)`:
     - Gera silhueta de montanhas com algumas oitavas de noise, base em `baseY`, picos com altura ate `peakHeight`
     - Preenche o poligono ate o rodape
   - Funcao privada `drawTree(gfx, x, baseY, scale)`:
     - Desenha tronco e copa em pixel-art
   - Funcao privada `drawForestLayer(gfx, width, baseY, density)`:
     - Distribui chamadas de `drawTree` ao longo de `width` perto de `baseY`
   - Funcao privada `createRiver(scene, top, width, height, baseDepth)`:
     - Retangulo com gradient azulado entre `top` e `top + height`
     - Tween de "shimmer" — alguns pixels reflexivos com fade alternado

2. Funcao publica `createNightLandscape(scene, width, height, baseDepth = -3)`:

   - Instancia `Phaser.Graphics` para o ceu, deseja gradient vertical de cima ate `HORIZON_Y = height * 0.55`
   - Coloca 90 estrelas com tweens de pisca (`from: 0.15 to 0.9`, duracao aleatoria 1200-3600ms, yoyo, repeat -1, delay aleatorio ate 3000ms)
   - Desenha lua em `(width * 0.82, height * 0.18)` com raio 44, fase crescente (disco escuro sobreposto a direita) e 3 crateras pequenas
   - Desenha duas cordilheiras (`drawMountainRange`) em depths empilhados (`baseDepth + 0.3` e `+0.4`)
   - Chama `createRiver` entre `HORIZON_Y` e `height * 0.68`
   - Chama `drawForestLayer` no rodape (depth `baseDepth + 0.5`)

3. Funcao publica `createForestParticles(scene, width, height)`:

   - Reusar `createParticleTexture(scene, "menu_particle", 3, 0xffd700)` (ja existente)
   - Criar `scene.add.particles(0, 0, "menu_particle", { ... })` com mesma config das antigas particulas do `MenuScene`:
     - `x: { min: 0, max: width }`, `y: height + 10`
     - `alpha: { start: 0.3, end: 0 }`, `scale: { min: 0.1, max: 0.4 }`
     - `speed: { min: 10, max: 25 }`, `angle: { min: 265, max: 275 }`
     - `lifespan: { min: 5000, max: 9000 }`, `frequency: 400`, `blendMode: "ADD"`

---

### Grupo 2 — Refactor de `MenuScene`

**Tarefa:** Substituir a geracao local de background/particles pelos helpers do Grupo 1.

1. Em `MenuScene.ts`:

   - Atualizar import para `import { createForestParticles, createNightLandscape } from "./ui-utils"`
   - Remover os metodos privados `createBackground` e `createParticles`
   - No `create()`, substituir as chamadas `this.createBackground(width, height)` e `this.createParticles(width, height)` por:
     - `createNightLandscape(this, width, height)`
     - `createForestParticles(this, width, height)`

2. Verificar visualmente:

   - Titulo, botoes de dificuldade, divisor ornamental e footer continuam visiveis acima do novo cenario
   - Sem regressao em hover/click dos botoes

---

### Grupo 3 — `PreparationScene` ganha cenario e label de dificuldade

**Tarefa:** Aplicar o cenario noturno e expor a dificuldade selecionada.

1. Em `PreparationScene.ts`:

   - Atualizar import para incluir `createForestParticles` e `createNightLandscape` junto de `drawPanel`
   - No inicio do `create()` (antes do `loadingText`):
     - `const { width, height } = this.scale;`
     - `createNightLandscape(this, width, height);`
     - `createForestParticles(this, width, height);`

2. Adicionar mapping local:

   ```typescript
   const DIFFICULTY_DISPLAY: Record<string, { label: string; color: string }> = {
     easy: { label: "Facil", color: "#44ff44" },
     normal: { label: "Normal", color: "#ffd700" },
     hard: { label: "Dificil", color: "#ff4444" },
   };
   ```

3. Implementar metodo privado `renderDifficultyLabel`:

   - Le `this.difficulty` (campo ja existente, populado a partir de `loadDifficulty`)
   - Faz lookup em `DIFFICULTY_DISPLAY` com fallback para `normal`
   - `this.add.text(1260, 22, "Dificuldade: {label}", { fontSize: "16px", color, fontFamily: FONT }).setOrigin(1, 0)`

4. Chamar `this.renderDifficultyLabel()` apos `this.renderBackButton()` (e antes de `renderClassPanel`)

5. Verificar manualmente:

   - Cenario noturno aparece atras dos paineis de classe/build/lista de time
   - Label de dificuldade aparece no canto superior direito com a cor correta
   - Ao mudar a dificuldade no menu e voltar para preparacao, o label reflete a mudanca

---

## Condicao de Conclusao

Todos os criterios de aceitacao em spec.md satisfeitos.
TypeScript compila sem erros (`npx tsc --noEmit`).
Atualizar `.specs/state.md`: registrar feature 30 com status `concluida`.
