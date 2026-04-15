import Phaser from "phaser";
import type {
  AbilityOut,
  InitialBattleState,
  CharacterOut,
  MapObjectOut,
  WsTurnStart,
  WsActionResult,
  WsAiAction,
  WsTurnEnd,
  WsSkipEvent,
  WsBattleEnd,
  WsError,
} from "../network/types";
import { BattleWsClient } from "../network/ws-client";
import { BattleAnimations } from "./battle-animations";
import { BattleAbilityBar } from "./battle-ability-bar";
import { BattleHud } from "./battle-hud";
import { BattleRangeOverlay } from "./battle-range-overlay";
import { updateStateFromEvent } from "./update-state";

const TILE_SIZE = 64;
const GRID_OFFSET_X = 32;
const GRID_OFFSET_Y = 104;
const GRID_COLS = 10;
const GRID_ROWS = 8;

const OBJECT_COLORS: Record<string, number> = {
  crate: 0x8b4513,
  barrel: 0x8b4513,
  tree: 0x228b22,
  rock: 0x808080,
  bush: 0x90ee90,
  puddle: 0x87ceeb,
};

const CLASS_ABBR: Record<string, string> = {
  warrior: "G",
  mage: "M",
  cleric: "C",
  archer: "A",
  assassin: "As",
};

interface CharacterEntry {
  data: CharacterOut;
  sprite: Phaser.GameObjects.Container;
  circle: Phaser.GameObjects.Arc;
  status: "active" | "knocked_out" | "dead";
}

interface MapObjectEntry {
  data: MapObjectOut;
  sprite: Phaser.GameObjects.Rectangle;
}

export default class BattleScene extends Phaser.Scene {
  private characters: Map<string, CharacterEntry> = new Map();
  private mapObjects: Map<string, MapObjectEntry> = new Map();
  private currentCharacter = "";
  private isPlayerTurn = false;
  private wsClient!: BattleWsClient;
  private turnIndicator!: Phaser.GameObjects.Text;
  private turnSubtext!: Phaser.GameObjects.Text;
  private errorText!: Phaser.GameObjects.Text;
  private sessionId!: string;
  private initialState!: InitialBattleState;
  private animations!: BattleAnimations;
  private abilityBar!: BattleAbilityBar;
  private isAnimating = false;
  private wsQueue: (() => void)[] = [];
  private playerCooldowns: Map<string, Map<string, number>> = new Map();
  private currentPA = 4;
  private selectedAbility: AbilityOut | null = null;
  private hud!: BattleHud;
  private rangeOverlay!: BattleRangeOverlay;
  private activeEffects: Map<string, Set<string>> = new Map();
  private lastHoverTile: { x: number; y: number } | null = null;
  private destroyed = false;

  constructor() {
    super("BattleScene");
  }

  init(data: { session_id: string; initial_state: InitialBattleState }) {
    this.sessionId = data.session_id;
    this.initialState = data.initial_state;
    this.characters = new Map();
    this.mapObjects = new Map();
    this.isAnimating = false;
    this.wsQueue = [];
    this.playerCooldowns = new Map();
    this.activeEffects = new Map();
    this.selectedAbility = null;
    this.currentPA = 4;
    this.currentCharacter = "";
    this.isPlayerTurn = false;
    this.lastHoverTile = null;
    this.destroyed = false;
  }

  create() {
    this.renderGrid();
    this.renderMapObjects();
    this.renderCharacters();
    this.createTurnIndicator();
    this.createErrorText();

    this.animations = new BattleAnimations(this);
    this.abilityBar = new BattleAbilityBar(this, 700, 104, {
      onAbilitySelected: (ability) => {
        this.selectedAbility = ability;
        if (ability.target !== "self") {
          const charEntry = this.characters.get(this.currentCharacter);
          if (charEntry) {
            const pos = charEntry.data.position;
            if (ability.target === "adjacent") {
              this.rangeOverlay.showAdjacentRange(pos.x, pos.y);
            } else {
              this.rangeOverlay.showRange(pos.x, pos.y, ability.max_range);
            }
          }
        }
        if (ability.target === "self") {
          this.useSelfAbility(ability);
        }
      },
      onAbilityDeselected: () => {
        this.selectedAbility = null;
        this.rangeOverlay.clear();
      },
      onEndTurn: () => {
        this.wsClient.sendEndTurn(this.currentCharacter);
      },
    });

    this.hud = new BattleHud(this);
    this.rangeOverlay = new BattleRangeOverlay(this, TILE_SIZE, GRID_OFFSET_X, GRID_OFFSET_Y, GRID_COLS, GRID_ROWS);

    for (const [id, entry] of this.characters) {
      const { px, py } = this.gridToPixel(entry.data.position.x, entry.data.position.y);
      this.hud.createHpBar(id, px, py, entry.data.current_hp, entry.data.max_hp);
    }

    for (const char of this.initialState.characters) {
      if (char.team === "player") {
        this.playerCooldowns.set(char.entity_id, new Map());
      }
    }

    this.input.keyboard?.on("keydown-ESC", () => {
      this.abilityBar.clearSelection();
      this.selectedAbility = null;
      this.rangeOverlay.clear();
    });

    this.connectWs();
    this.updateTurnState(this.initialState.current_character);

    if (this.isPlayerCharacter(this.initialState.current_character)) {
      const charEntry = this.characters.get(this.initialState.current_character);
      if (charEntry) {
        this.abilityBar.show(
          charEntry.data.abilities,
          4,
          this.playerCooldowns.get(this.initialState.current_character) ?? new Map(),
        );
      }
    }
  }

  private renderGrid() {
    for (let x = 0; x < GRID_COLS; x++) {
      for (let y = 0; y < GRID_ROWS; y++) {
        const { px, py } = this.gridToPixel(x, y);
        const color = (x + y) % 2 === 0 ? 0x3a3a5c : 0x2a2a4c;
        const tile = this.add.rectangle(px, py, TILE_SIZE, TILE_SIZE, color);
        tile.setInteractive();
        tile.on("pointerdown", () => this.onTileClick(x, y));
        tile.on("pointermove", () => this.onTileHover(x, y));
      }
    }
  }

  private renderMapObjects() {
    for (const obj of this.initialState.map_objects) {
      const { px, py } = this.gridToPixel(obj.position.x, obj.position.y);
      const color = OBJECT_COLORS[obj.object_type] ?? 0x666666;
      const size = TILE_SIZE * 0.7;
      const rect = this.add.rectangle(px, py, size, size, color);
      if (obj.blocks_movement) {
        rect.setStrokeStyle(2, 0xffffff);
      }
      this.mapObjects.set(obj.entity_id, { data: obj, sprite: rect });
    }
  }

  private renderCharacters() {
    for (const char of this.initialState.characters) {
      const { px, py } = this.gridToPixel(char.position.x, char.position.y);
      const teamColor = char.team === "player" ? 0x4488ff : 0xff4444;
      const circle = this.add.circle(0, 0, 24, teamColor);
      const abbr = CLASS_ABBR[char.class_id] ?? "?";
      const label = this.add.text(0, 0, abbr, {
        fontSize: "16px",
        color: "#ffffff",
        fontFamily: "monospace",
        fontStyle: "bold",
      }).setOrigin(0.5);
      const container = this.add.container(px, py, [circle, label]);
      this.characters.set(char.entity_id, {
        data: { ...char },
        sprite: container,
        circle,
        status: "active",
      });
    }
  }

  private createTurnIndicator() {
    this.turnIndicator = this.add.text(32, 20, "", {
      fontSize: "20px",
      color: "#ffffff",
      fontFamily: "monospace",
    });
    this.turnSubtext = this.add.text(32, 50, "", {
      fontSize: "16px",
      color: "#ffffff",
      fontFamily: "monospace",
    });
  }

  private createErrorText() {
    const errorY = GRID_OFFSET_Y + GRID_ROWS * TILE_SIZE + 10;
    this.errorText = this.add.text(32, errorY, "", {
      fontSize: "14px",
      color: "#ff4444",
      fontFamily: "monospace",
    });
  }

  private connectWs() {
    this.wsClient = new BattleWsClient(this.sessionId, {
      onTurnStart: (msg) => this.enqueueOrRun(() => this.handleTurnStart(msg)),
      onActionResult: (msg) => this.enqueueOrRun(() => this.handleActionResult(msg)),
      onAiAction: (msg) => this.enqueueOrRun(() => this.handleAiAction(msg)),
      onTurnEnd: (msg) => this.enqueueOrRun(() => this.handleTurnEnd(msg)),
      onSkipEvent: (msg) => this.handleSkipEvent(msg),
      onBattleEnd: (msg) => this.handleBattleEnd(msg),
      onError: (msg) => this.handleError(msg),
      onDisconnect: () => this.handleDisconnect(),
    });
    this.wsClient.connect();
  }

  private enqueueOrRun(fn: () => void) {
    if (this.destroyed) return;
    if (this.isAnimating) {
      this.wsQueue.push(fn);
    } else {
      fn();
    }
  }

  private drainQueue() {
    while (this.wsQueue.length > 0 && !this.isAnimating && !this.destroyed) {
      const fn = this.wsQueue.shift()!;
      fn();
    }
  }

  private updateTurnState(entityId: string) {
    this.currentCharacter = entityId;
    this.isPlayerTurn = this.isPlayerCharacter(entityId);

    const color = this.isPlayerTurn ? "#4488ff" : "#ff4444";
    this.turnIndicator.setText(`Turno de: ${entityId}`).setColor(color);
    this.turnSubtext
      .setText(this.isPlayerTurn ? "Seu turno" : "Turno da IA")
      .setColor(color);
    this.errorText.setText("");
  }

  // --- WS Handlers ---

  private async handleTurnStart(msg: WsTurnStart) {
    this.updateTurnState(msg.character);

    if (this.isPlayerCharacter(msg.character)) {
      this.tickCooldownsForCharacter(msg.character);
      this.currentPA = msg.pa;
      const charEntry = this.characters.get(msg.character);
      if (charEntry) {
        this.abilityBar.show(
          charEntry.data.abilities,
          msg.pa,
          this.playerCooldowns.get(msg.character) ?? new Map(),
        );
      }
    } else {
      this.abilityBar.hide();
    }

    if (msg.events && msg.events.length > 0) {
      this.isAnimating = true;
      try {
        await this.animations.processEventsAnimated(
          msg.events,
          (id) => this.characters.get(id),
          (id) => this.mapObjects.get(id),
          (x, y) => this.gridToPixel(x, y),
          (event) => this.updateStateFromEvent(event),
          this.floatingTextCallback,
        );
      } finally {
        this.isAnimating = false;
      }
      this.refreshHud();
      this.drainQueue();
    }
  }

  private async handleActionResult(msg: WsActionResult) {
    this.isAnimating = true;
    try {
      await this.animations.processEventsAnimated(
        msg.events,
        (id) => this.characters.get(id),
        (id) => this.mapObjects.get(id),
        (x, y) => this.gridToPixel(x, y),
        (event) => this.updateStateFromEvent(event),
        this.floatingTextCallback,
      );
    } finally {
      this.isAnimating = false;
    }
    this.refreshHud();
    this.updatePAFromAction(msg);
    this.abilityBar.clearSelection();
    this.selectedAbility = null;
    this.rangeOverlay.clear();
    this.drainQueue();
  }

  private async handleAiAction(msg: WsAiAction) {
    this.isAnimating = true;
    try {
      await this.animations.processEventsAnimated(
        msg.events,
        (id) => this.characters.get(id),
        (id) => this.mapObjects.get(id),
        (x, y) => this.gridToPixel(x, y),
        (event) => this.updateStateFromEvent(event),
        this.floatingTextCallback,
      );
    } finally {
      this.isAnimating = false;
    }
    this.refreshHud();
    this.wsClient.sendReady();
    this.drainQueue();
  }

  private handleTurnEnd(msg: WsTurnEnd) {
    this.updateTurnState(msg.next);
    if (!this.isPlayerCharacter(msg.next)) {
      this.abilityBar.hide();
    }
  }

  private handleSkipEvent(_msg: WsSkipEvent) {
    // no visual action needed
  }

  private handleBattleEnd(msg: WsBattleEnd) {
    this.wsClient.disconnect();
    const characters: { class_id: string; team: string; status: string }[] = [];
    for (const [, entry] of this.characters) {
      characters.push({
        class_id: entry.data.class_id,
        team: entry.data.team,
        status: entry.status,
      });
    }
    this.scene.start("ResultScene", { result: msg.result, characters });
  }

  private handleError(msg: WsError) {
    this.errorText.setText(msg.message);
  }

  private handleDisconnect() {
    this.errorText.setText("Conexao perdida");
  }

  // --- Tile Interaction ---

  private onTileClick(x: number, y: number) {
    if (this.isAnimating || !this.isPlayerTurn) return;

    if (this.selectedAbility) {
      if (this.selectedAbility.id === "basic_attack") {
        this.wsClient.sendBasicAttack(this.currentCharacter, [x, y]);
      } else {
        this.wsClient.sendAbility(this.currentCharacter, this.selectedAbility.id, [x, y]);
      }
      return;
    }

    const enemy = this.getCharacterAt(x, y);
    if (enemy && enemy.data.team !== "player" && enemy.status === "active") {
      this.wsClient.sendBasicAttack(this.currentCharacter, [x, y]);
      return;
    }

    const anyChar = this.getCharacterAt(x, y);
    if (anyChar) return;

    for (const entry of this.mapObjects.values()) {
      if (
        entry.data.position.x === x &&
        entry.data.position.y === y &&
        entry.data.blocks_movement
      ) {
        return;
      }
    }

    this.wsClient.sendMove(this.currentCharacter, [x, y]);
  }

  private onTileHover(x: number, y: number) {
    if (!this.selectedAbility || this.isAnimating) {
      this.lastHoverTile = null;
      this.rangeOverlay.clearAoePreview();
      return;
    }
    if (this.lastHoverTile?.x === x && this.lastHoverTile?.y === y) return;
    this.lastHoverTile = { x, y };
    if (this.selectedAbility.target === "aoe") {
      const charEntry = this.characters.get(this.currentCharacter);
      if (charEntry) {
        const pos = charEntry.data.position;
        const dist = Math.max(Math.abs(x - pos.x), Math.abs(y - pos.y));
        if (dist <= this.selectedAbility.max_range) {
          this.rangeOverlay.showAoePreview(x, y);
        } else {
          this.rangeOverlay.clearAoePreview();
        }
      }
    }
  }

  // --- State Update from Events ---

  private updateStateFromEvent(event: Record<string, unknown>) {
    updateStateFromEvent(event, this.characters, this.activeEffects);
  }

  // --- PA and Cooldown Tracking ---

  private updatePAFromAction(msg: WsActionResult) {
    let cost = 0;
    if (msg.action === "move") {
      for (const raw of msg.events) {
        const event = raw as Record<string, unknown>;
        if (event.type === "move" || event.type === "ability_movement") {
          const from = event.from as [number, number] | { x: number; y: number } | undefined;
          const to = (event.to ?? event.position) as [number, number] | { x: number; y: number } | undefined;
          if (from && to) {
            const [fx, fy] = Array.isArray(from) ? from : [from.x, from.y];
            const [tx, ty] = Array.isArray(to) ? to : [to.x, to.y];
            const dist = Math.max(Math.abs(tx - fx), Math.abs(ty - fy));
            cost += Math.ceil(dist / 2);
          }
        }
      }
    } else if (msg.action === "basic_attack") {
      cost = 2;
    } else if (msg.action === "ability") {
      const abilityId = msg.ability;
      if (abilityId) {
        const charEntry = this.characters.get(this.currentCharacter);
        if (charEntry) {
          const ability = charEntry.data.abilities.find(a => a.id === abilityId);
          if (ability) {
            cost = ability.pa_cost;
            if (ability.cooldown > 0) {
              this.startCooldownForCharacter(this.currentCharacter, ability.id, ability.cooldown);
            }
          }
        }
      }
    }

    this.currentPA = Math.max(0, this.currentPA - cost);
    this.abilityBar.deductPA(cost);
  }

  private tickCooldownsForCharacter(charId: string) {
    const cds = this.playerCooldowns.get(charId);
    if (!cds) return;
    for (const [abilityId, remaining] of cds) {
      const next = remaining - 1;
      if (next <= 0) {
        cds.delete(abilityId);
      } else {
        cds.set(abilityId, next);
      }
    }
  }

  private startCooldownForCharacter(charId: string, abilityId: string, turns: number) {
    let cds = this.playerCooldowns.get(charId);
    if (!cds) {
      cds = new Map();
      this.playerCooldowns.set(charId, cds);
    }
    cds.set(abilityId, turns);
    this.abilityBar.startCooldown(abilityId, turns);
  }

  // --- Self-targeting ---

  private useSelfAbility(ability: AbilityOut) {
    const charEntry = this.characters.get(this.currentCharacter);
    if (!charEntry) return;
    const pos = charEntry.data.position;
    this.wsClient.sendAbility(this.currentCharacter, ability.id, [pos.x, pos.y]);
    this.abilityBar.clearSelection();
    this.selectedAbility = null;
  }

  // --- HUD Helpers ---

  private floatingTextCallback = (worldX: number, worldY: number, text: string, color: string, fontSize: string) => {
    this.hud.spawnFloatingText(worldX, worldY, text, color, fontSize);
  };

  private refreshHud() {
    this.hud.updateAllBars(this.characters, (x, y) => this.gridToPixel(x, y));
    for (const [id, entry] of this.characters) {
      if (entry.status === "dead") continue;
      const { px, py } = this.gridToPixel(entry.data.position.x, entry.data.position.y);
      const effects = this.activeEffects.get(id) ?? new Set();
      this.hud.updateStatusIcons(id, px, py, effects);
    }
  }

  // --- Helpers ---

  private gridToPixel(x: number, y: number): { px: number; py: number } {
    return {
      px: GRID_OFFSET_X + x * TILE_SIZE + TILE_SIZE / 2,
      py: GRID_OFFSET_Y + y * TILE_SIZE + TILE_SIZE / 2,
    };
  }

  private isPlayerCharacter(entityId: string): boolean {
    const entry = this.characters.get(entityId);
    return entry?.data.team === "player";
  }

  private getCharacterAt(x: number, y: number): CharacterEntry | undefined {
    for (const entry of this.characters.values()) {
      if (
        entry.data.position.x === x &&
        entry.data.position.y === y &&
        entry.status !== "dead"
      ) {
        return entry;
      }
    }
    return undefined;
  }

  shutdown() {
    this.destroyed = true;
    this.wsQueue = [];
    this.wsClient?.disconnect();
    this.abilityBar?.destroy();
    this.hud?.destroy();
    this.rangeOverlay?.destroy();
  }
}
