# Feature 30 — Cenario Noturno Compartilhado em Menu e Preparacao

## Objetivo

Substituir o background escuro abstrato do `MenuScene` por um cenario noturno pixel-art coerente (ceu estrelado com gradient, lua, montanhas em camadas, rio e floresta em silhueta), e reaplicar o mesmo cenario na `PreparationScene` para criar continuidade visual entre as duas telas. Tambem expor a dificuldade selecionada no canto superior da tela de preparacao, ja que ela e escolhida no menu mas ate entao nao era visivel apos a transicao.

A funcionalidade de geracao do cenario fica em `ui-utils.ts` para ser reutilizada por qualquer cena futura. As particulas douradas existentes sao preservadas e tambem migradas para `ui-utils.ts` como helper compartilhado.

---

## Referencia nos Specs

- prd.md: secao 7 (Interface e UX)
- design.md: secao 7 (specs visuais das cenas)

---

## Arquivos Envolvidos

### Modificar

| Arquivo | Descricao |
|---|---|
| `frontend/src/scenes/ui-utils.ts` | Novos helpers exportados: `createNightLandscape`, `createForestParticles`. Helpers privados: `drawPixelDisk`, `drawMountainRange`, `drawForestLayer`, `drawTree`, `createRiver` |
| `frontend/src/scenes/MenuScene.ts` | Removidos metodos privados `createBackground` e `createParticles`; passa a chamar `createNightLandscape(this, w, h)` e `createForestParticles(this, w, h)` |
| `frontend/src/scenes/PreparationScene.ts` | Adiciona `createNightLandscape` + `createForestParticles` no `create()`; adiciona metodo `renderDifficultyLabel` exibindo a dificuldade salva no canto superior direito |

---

## Criterios de Aceitacao

### Helper de Cenario (`ui-utils.ts`)

- [ ] Funcao `createNightLandscape(scene, width, height, baseDepth = -3)` exportada
- [ ] Cenario gerado tem (de tras pra frente, depths crescentes a partir de `baseDepth`):
  - Ceu com gradient vertical pixel a pixel (mais escuro em cima, mais claro perto do horizonte)
  - 90 estrelas com posicoes pixel-aligned, com tween de fade infinito (yoyo)
  - Lua pixel-art com glow externo, fase crescente (uma "mordida" escura no lado direito) e algumas crateras
  - Cordilheira de fundo (tom azul escurecido)
  - Cordilheira frontal (tom mais escuro, sobreposta a primeira)
  - Rio horizontal abaixo do horizonte com reflexos animados
  - Camada de floresta em silhueta no rodape, com arvores pixel-art
- [ ] Tudo renderizado em escala pixel (`PIXEL = 4`), coordenadas alinhadas a multiplos de PIXEL
- [ ] Funcao `createForestParticles(scene, width, height)` exportada — particulas douradas (similar as antigas do menu) com `blendMode: ADD`, subindo do rodape para o topo da tela
- [ ] Helpers internos (`drawPixelDisk`, `drawMountainRange`, `drawForestLayer`, `drawTree`, `createRiver`) sao funcoes locais ao modulo, nao exportadas
- [ ] Geracao usa `Math.random()` — variacao em cada montagem da cena e aceitavel (estrelas e arvores em posicoes diferentes a cada navegacao)

### MenuScene

- [ ] `createBackground` e `createParticles` (privados) sao removidos
- [ ] Cenario noturno e particulas sao instanciados em `create()` via `createNightLandscape` e `createForestParticles`
- [ ] Titulo "ASHBORN ARENA", botoes de dificuldade, divisor ornamental e footer permanecem inalterados (renderizados acima do cenario)
- [ ] Comportamento dos botoes de dificuldade nao muda

### PreparationScene

- [ ] Cenario noturno e particulas sao instanciados em `create()` antes do conteudo da tela
- [ ] Painel de classe, painel de build, lista de time, ability bar e botao de inicio nao tem aparencia alterada — apenas ganham o background novo por baixo
- [ ] Novo label "Dificuldade: {Facil|Normal|Dificil}" renderizado no canto superior direito (`(1260, 22)`, origem `(1, 0)`)
- [ ] Cor do label segue mapping `easy → #44ff44`, `normal → #ffd700`, `hard → #ff4444`
- [ ] Label usa `fontSize: 16px`, `fontFamily: monospace`
- [ ] Se a dificuldade salva nao existir no mapping, fallback para "Normal"

### Compatibilidade

- [ ] Build TypeScript continua sem erros (`npx tsc --noEmit`)
- [ ] Outras cenas (`BattleScene`, `ResultScene`) nao sao afetadas
- [ ] `createParticleTexture` (helper antigo) e mantido em `ui-utils.ts` — pode ser usado por outras cenas e tambem internamente por `createForestParticles`

---

## Fora do Escopo

- Cenario diferente por dificuldade (mesmo cenario para todas)
- Cenarios alternativos (dia, deserto, etc.)
- Animacao de transicao entre Menu e Preparacao
- Aplicar o cenario noturno em `BattleScene` ou `ResultScene`
- Tornar a geracao deterministica (seedavel) — variacao por sessao e comportamento aceito
