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
import { BattleActiveMarker } from "./battle-active-marker";
import { BattleCombatLog, formatEventForLog } from "./battle-combat-log";
import { CharacterDetailPanel } from "./battle-detail-panel";
import type { DetailPanelData } from "./battle-detail-panel";
import { loadAbilityIcons } from "./ability-icons";
import { updateStateFromEvent } from "./update-state";
import { drawPanel } from "./ui-utils";

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
};

const CLASS_ABBR: Record<string, string> = {
  warrior: "G",
  mage: "M",
  cleric: "C",
  archer: "A",
  assassin: "As",
};

const CLASS_DISPLAY: Record<string, string> = {
  warrior: "Guerreiro",
  mage: "Mago",
  cleric: "Clerigo",
  archer: "Arqueiro",
  assassin: "Assassino",
};

interface CharacterEntry {
  data: CharacterOut;
  sprite: Phaser.GameObjects.Container;
  circle: Phaser.GameObjects.Arc;
  status: "active" | "knocked_out" | "dead";
}

interface MapObjectEntry {
  data: MapObjectOut;
  sprite: Phaser.GameObjects.Rectangle | Phaser.GameObjects.Image;
  canopy?: Phaser.GameObjects.Image;
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
  private activeMarker!: BattleActiveMarker;
  private combatLog!: BattleCombatLog;
  private detailPanel!: CharacterDetailPanel;
  private detailPanelEntityId: string | null = null;
  private activeEffects: Map<string, Set<string>> = new Map();
  private lastHoverTile: { x: number; y: number } | null = null;
  private autoBattle = false;
  private destroyed = false;

  constructor() {
    super("BattleScene");
  }

  init(data: {
    session_id: string;
    initial_state: InitialBattleState;
    auto_battle?: boolean;
  }) {
    this.sessionId = data.session_id;
    this.initialState = data.initial_state;
    this.autoBattle = data.auto_battle ?? false;
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
    this.detailPanelEntityId = null;
    this.destroyed = false;
  }

  preload() {
    this.load.image("big_oak_tree", "assets/spritesheets/Big_Oak_Tree.png");
    this.load.image("barrels", "assets/spritesheets/barrels.png");
    this.load.image("outdoor_decor", "assets/spritesheets/Outdoor_Decor.png");
    this.load.spritesheet("forest_floor", "assets/spritesheets/florest.png", {
      frameWidth: 16,
      frameHeight: 16,
    });
  }

  create() {
    const treeTex = this.textures.get("big_oak_tree");
    treeTex.add("tree_canopy", 0, 64, 0, 64, 48);
    treeTex.add("tree_base", 0, 64, 48, 64, 32);

    const barrelTex = this.textures.get("barrels");
    for (let i = 0; i < 5; i++) {
      barrelTex.add(`barrel_${i}`, 0, i * 16, 0, 16, 32);
    }
    for (let i = 0; i < 6; i++) {
      barrelTex.add(`barrel_${5 + i}`, 0, i * 16, 32, 16, 32);
    }

    const decorTex = this.textures.get("outdoor_decor");
    decorTex.add("bush", 0, 96, 256, 16, 16);
    decorTex.add("rock", 0, 96, 176, 32, 32);

    loadAbilityIcons(this);
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
    this.rangeOverlay = new BattleRangeOverlay(
      this,
      TILE_SIZE,
      GRID_OFFSET_X,
      GRID_OFFSET_Y,
      GRID_COLS,
      GRID_ROWS,
    );
    this.activeMarker = new BattleActiveMarker(this);
    this.combatLog = new BattleCombatLog(this, 700, 500, 548, 210);
    this.detailPanel = new CharacterDetailPanel(this);

    for (const [id, entry] of this.characters) {
      const { px, py } = this.gridToPixel(
        entry.data.position.x,
        entry.data.position.y,
      );
      this.hud.createHpBar(
        id,
        px,
        py,
        entry.data.current_hp,
        entry.data.max_hp,
      );
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
      this.detailPanel.hide();
      this.detailPanelEntityId = null;
    });

    this.connectWs();
    this.updateTurnState(this.initialState.current_character);

    if (
      this.isPlayerCharacter(this.initialState.current_character) &&
      !this.autoBattle
    ) {
      const charEntry = this.characters.get(
        this.initialState.current_character,
      );
      if (charEntry) {
        this.abilityBar.show(
          charEntry.data.abilities,
          4,
          this.playerCooldowns.get(this.initialState.current_character) ??
            new Map(),
        );
      }
    }
  }

  private renderGrid() {
    const S = 7;
    const DIRT = 4 * S + 4;

    for (let x = 0; x < GRID_COLS; x++) {
      for (let y = 0; y < GRID_ROWS; y++) {
        const { px, py } = this.gridToPixel(x, y);

        const isT = y === 0;
        const isB = y === GRID_ROWS - 1;
        const isL = x === 0;
        const isR = x === GRID_COLS - 1;

        let frame: number;
        let flipX = false;
        let flipY = false;
        if (isT && isL) frame = 3 * S + 3;
        else if (isT && isR) {
          frame = 3 * S + 3;
          flipX = true;
        } else if (isB && isL) {
          frame = 3 * S + 3;
          flipY = true;
        } else if (isB && isR) {
          frame = 3 * S + 3;
          flipX = true;
          flipY = true;
        } else if (isT) frame = 0 * S + 3;
        else if (isB) {
          frame = 0 * S + 3;
          flipY = true;
        } else if (isL) frame = 3 * S;
        else if (isR) {
          frame = 3 * S;
          flipX = true;
        } else frame = DIRT;

        const tile = this.add.image(px, py, "forest_floor", frame);
        tile.setScale(TILE_SIZE / 16);
        if (flipX) tile.setFlipX(true);
        if (flipY) tile.setFlipY(true);
        tile.setInteractive();
        tile.on("pointerdown", () => this.onTileClick(x, y));
        tile.on("pointermove", () => this.onTileHover(x, y));
      }
    }

    const gridGfx = this.add.graphics();
    gridGfx.setDepth(1);
    gridGfx.lineStyle(1, 0x000000, 0.12);
    for (let gx = 0; gx <= GRID_COLS; gx++) {
      const lx = GRID_OFFSET_X + gx * TILE_SIZE;
      gridGfx.lineBetween(
        lx,
        GRID_OFFSET_Y,
        lx,
        GRID_OFFSET_Y + GRID_ROWS * TILE_SIZE,
      );
    }
    for (let gy = 0; gy <= GRID_ROWS; gy++) {
      const ly = GRID_OFFSET_Y + gy * TILE_SIZE;
      gridGfx.lineBetween(
        GRID_OFFSET_X,
        ly,
        GRID_OFFSET_X + GRID_COLS * TILE_SIZE,
        ly,
      );
    }
  }

  private renderMapObjects() {
    const TREE_SCALE = 2;

    for (const obj of this.initialState.map_objects) {
      const { px, py } = this.gridToPixel(obj.position.x, obj.position.y);

      if (obj.object_type === "tree") {
        const tileBottom = py + TILE_SIZE / 2;
        const baseDisplayH = 32 * TREE_SCALE;

        const base = this.add.image(
          px,
          tileBottom,
          "big_oak_tree",
          "tree_base",
        );
        base.setOrigin(0.5, 1);
        base.setScale(TREE_SCALE);
        base.setDepth(2);

        const canopy = this.add.image(
          px,
          tileBottom - baseDisplayH,
          "big_oak_tree",
          "tree_canopy",
        );
        canopy.setOrigin(0.5, 1);
        canopy.setScale(TREE_SCALE);
        canopy.setDepth(12);

        this.mapObjects.set(obj.entity_id, { data: obj, sprite: base, canopy });
      } else if (obj.object_type === "crate" || obj.object_type === "barrel") {
        const BARREL_SCALE = 3;
        const PLAIN_BARREL_COUNT = 5;
        const frameIdx = Math.floor(Math.random() * PLAIN_BARREL_COUNT);
        const tileBottom = py + TILE_SIZE / 2;

        const barrel = this.add.image(
          px,
          tileBottom,
          "barrels",
          `barrel_${frameIdx}`,
        );
        barrel.setOrigin(0.5, 1);
        barrel.setScale(BARREL_SCALE);
        barrel.setDepth(2);

        this.mapObjects.set(obj.entity_id, { data: obj, sprite: barrel });
      } else if (obj.object_type === "bush") {
        const bush = this.add.image(
          px,
          py + TILE_SIZE / 2,
          "outdoor_decor",
          "bush",
        );
        bush.setOrigin(0.5, 1);
        bush.setScale(3);
        bush.setDepth(2);

        this.mapObjects.set(obj.entity_id, { data: obj, sprite: bush });
      } else if (obj.object_type === "rock") {
        const rock = this.add.image(
          px,
          py + TILE_SIZE / 2,
          "outdoor_decor",
          "rock",
        );
        rock.setOrigin(0.5, 1);
        rock.setScale(2);
        rock.setDepth(2);

        this.mapObjects.set(obj.entity_id, { data: obj, sprite: rock });
      } else {
        const color = OBJECT_COLORS[obj.object_type] ?? 0x666666;
        const size = TILE_SIZE * 0.7;
        const rect = this.add.rectangle(px, py, size, size, color);
        if (obj.blocks_movement) {
          rect.setStrokeStyle(2, 0xffffff);
        }
        this.mapObjects.set(obj.entity_id, { data: obj, sprite: rect });
      }
    }
  }

  private renderCharacters() {
    for (const char of this.initialState.characters) {
      const { px, py } = this.gridToPixel(char.position.x, char.position.y);
      const teamColor = char.team === "player" ? 0x4488ff : 0xff4444;
      const circle = this.add.circle(0, 0, 24, teamColor);
      const abbr = CLASS_ABBR[char.class_id] ?? "?";
      const label = this.add
        .text(0, 0, abbr, {
          fontSize: "16px",
          color: "#ffffff",
          fontFamily: "monospace",
          fontStyle: "bold",
        })
        .setOrigin(0.5);
      const container = this.add.container(px, py, [circle, label]);
      container.setDepth(10);
      container.setSize(48, 48);
      container.setInteractive(
        new Phaser.Geom.Circle(0, 0, 24),
        Phaser.Geom.Circle.Contains,
      );
      container.on(
        "pointerdown",
        (
          _pointer: Phaser.Input.Pointer,
          _lx: number,
          _ly: number,
          event: Phaser.Types.Input.EventData,
        ) => {
          event.stopPropagation();
          this.onCharacterClick(char.entity_id);
        },
      );
      this.characters.set(char.entity_id, {
        data: { ...char },
        sprite: container,
        circle,
        status: "active",
      });
    }
  }

  private createTurnIndicator() {
    drawPanel(this, 16, 10, 290, 78, {
      fill: 0x14142a,
      fillAlpha: 0.85,
      border: 0x333366,
      borderAlpha: 0.6,
      radius: 6,
      depth: 99,
    });

    this.turnIndicator = this.add.text(32, 22, "", {
      fontSize: "18px",
      color: "#ffffff",
      fontFamily: "monospace",
    });
    this.turnIndicator.setDepth(100);
    this.turnSubtext = this.add.text(32, 52, "", {
      fontSize: "14px",
      color: "#ffffff",
      fontFamily: "monospace",
    });
    this.turnSubtext.setDepth(100);
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
      onActionResult: (msg) =>
        this.enqueueOrRun(() => this.handleActionResult(msg)),
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
      try {
        fn();
      } catch (err) {
        console.error("Queued WS handler failed, continuing:", err);
      }
    }
  }

  private updateTurnState(entityId: string) {
    this.currentCharacter = entityId;
    this.isPlayerTurn = this.isPlayerCharacter(entityId);

    const charEntry = this.characters.get(entityId);
    const displayName = charEntry
      ? (CLASS_DISPLAY[charEntry.data.class_id] ?? entityId)
      : entityId;

    const color = this.isPlayerTurn && !this.autoBattle ? "#4488ff" : "#ff4444";
    this.turnIndicator.setText(`Turno de: ${displayName}`).setColor(color);
    this.turnSubtext
      .setText(
        this.autoBattle
          ? "IA vs IA"
          : this.isPlayerTurn
            ? "Seu turno"
            : "Turno da IA",
      )
      .setColor(color);
    this.errorText.setText("");

    if (charEntry) {
      const { px, py } = this.gridToPixel(
        charEntry.data.position.x,
        charEntry.data.position.y,
      );
      this.activeMarker.show(px, py, charEntry.data.team);
    }
  }

  // --- WS Handlers ---

  private async handleTurnStart(msg: WsTurnStart) {
    this.detailPanel.hide();
    this.detailPanelEntityId = null;
    this.updateTurnState(msg.character);

    if (this.isPlayerCharacter(msg.character) && !this.autoBattle) {
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
      this.logEvents(msg.events);
      this.refreshHud();
      this.drainQueue();
    }
  }

  private async handleActionResult(msg: WsActionResult) {
    this.detailPanel.hide();
    this.detailPanelEntityId = null;
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
    this.logEvents(msg.events);
    this.refreshHud();
    this.updatePAFromAction(msg);
    this.abilityBar.clearSelection();
    this.selectedAbility = null;
    this.rangeOverlay.clear();
    this.drainQueue();
  }

  private async handleAiAction(msg: WsAiAction) {
    this.detailPanel.hide();
    this.detailPanelEntityId = null;
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
      this.logEvents(msg.events);
      this.refreshHud();
      await this.delay(800);
    } catch (err) {
      console.error("AI action animation failed, continuing:", err);
    } finally {
      this.isAnimating = false;
      this.wsClient.sendReady();
      this.drainQueue();
    }
  }

  private handleTurnEnd(msg: WsTurnEnd) {
    this.updateTurnState(msg.next);
    if (!this.isPlayerCharacter(msg.next) || this.autoBattle) {
      this.abilityBar.hide();
    }
  }

  private handleSkipEvent(_msg: WsSkipEvent) {
    // no visual action needed
  }

  private handleBattleEnd(msg: WsBattleEnd) {
    this.wsClient.disconnect();
    this.activeMarker.hide();
    this.combatLog.destroy();
    this.detailPanel.hide();
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

  // --- Character Detail Panel ---

  private onCharacterClick(entityId: string) {
    if (this.isAnimating) return;

    if (this.detailPanel.isVisible() && this.detailPanelEntityId === entityId) {
      this.detailPanel.hide();
      this.detailPanelEntityId = null;
      return;
    }

    const entry = this.characters.get(entityId);
    if (!entry || entry.status === "dead") return;

    const isAlly = entry.data.team === "player";
    const effects = this.activeEffects.get(entityId) ?? new Set<string>();

    const data: DetailPanelData = {
      className: CLASS_DISPLAY[entry.data.class_id] ?? entry.data.class_id,
      team: entry.data.team,
      currentHp: entry.data.current_hp,
      maxHp: entry.data.max_hp,
      pa: entityId === this.currentCharacter ? this.currentPA : undefined,
      attributes: isAlly ? entry.data.attributes : undefined,
      effects: [...effects].map((tag) => ({ tag })),
      abilities: isAlly
        ? entry.data.abilities.map((ab) => ({
            name: ab.name,
            cooldownRemaining:
              this.playerCooldowns.get(entityId)?.get(ab.id) ?? 0,
          }))
        : undefined,
    };

    this.detailPanel.show(data);
    this.detailPanelEntityId = entityId;
  }

  // --- Tile Interaction ---

  private onTileClick(x: number, y: number) {
    if (this.detailPanel.isVisible()) {
      this.detailPanel.hide();
      this.detailPanelEntityId = null;
    }
    if (this.isAnimating || !this.isPlayerTurn || this.autoBattle) return;

    if (this.selectedAbility) {
      if (this.selectedAbility.id.startsWith("basic_attack")) {
        this.wsClient.sendBasicAttack(this.currentCharacter, [x, y]);
      } else {
        this.wsClient.sendAbility(
          this.currentCharacter,
          this.selectedAbility.id,
          [x, y],
        );
      }
      return;
    }

    const charAtTile = this.getCharacterAt(x, y);
    if (charAtTile) {
      this.onCharacterClick(charAtTile.data.entity_id);
      return;
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
    updateStateFromEvent(
      event,
      this.characters,
      this.activeEffects,
      this.mapObjects,
    );
  }

  // --- PA and Cooldown Tracking ---

  private updatePAFromAction(msg: WsActionResult) {
    this.currentPA = msg.pa;
    this.abilityBar.setPA(msg.pa);

    if (msg.action === "ability" && msg.ability) {
      const charEntry = this.characters.get(this.currentCharacter);
      if (charEntry) {
        const ability = charEntry.data.abilities.find(
          (a) => a.id === msg.ability,
        );
        if (ability && ability.cooldown > 0) {
          this.startCooldownForCharacter(
            this.currentCharacter,
            ability.id,
            ability.cooldown,
          );
        }
      }
    }
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

  private startCooldownForCharacter(
    charId: string,
    abilityId: string,
    turns: number,
  ) {
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
    this.wsClient.sendAbility(this.currentCharacter, ability.id, [
      pos.x,
      pos.y,
    ]);
    this.abilityBar.clearSelection();
    this.selectedAbility = null;
  }

  // --- HUD Helpers ---

  private floatingTextCallback = (
    worldX: number,
    worldY: number,
    text: string,
    color: string,
    fontSize: string,
  ) => {
    this.hud.spawnFloatingText(worldX, worldY, text, color, fontSize);
  };

  private refreshHud() {
    this.hud.updateAllBars(this.characters, (x, y) => this.gridToPixel(x, y));
    this.hud.updateObjectBars(this.mapObjects, (x, y) =>
      this.gridToPixel(x, y),
    );
    for (const [id, entry] of this.characters) {
      if (entry.status === "dead") {
        entry.sprite.setAlpha(0.25);
        entry.circle.setFillStyle(0x555555);
        continue;
      }
      if (entry.status === "knocked_out") {
        entry.sprite.setAlpha(0.5);
        entry.circle.setFillStyle(0x888888);
      } else {
        entry.sprite.setAlpha(1);
        const teamColor = entry.data.team === "player" ? 0x4488ff : 0xff4444;
        entry.circle.setFillStyle(teamColor);
      }
      const { px, py } = this.gridToPixel(
        entry.data.position.x,
        entry.data.position.y,
      );
      const effects = this.activeEffects.get(id) ?? new Set();
      this.hud.updateStatusIcons(id, px, py, effects);
    }
    const current = this.characters.get(this.currentCharacter);
    if (current && current.status !== "dead") {
      const { px, py } = this.gridToPixel(
        current.data.position.x,
        current.data.position.y,
      );
      this.activeMarker.show(px, py, current.data.team);
    }
  }

  // --- Log + Delay Helpers ---

  private resolveClassName = (entityId: string): string => {
    const entry = this.characters.get(entityId);
    return entry ? (CLASS_DISPLAY[entry.data.class_id] ?? entityId) : entityId;
  };

  private logEvents(events: unknown[]) {
    for (const raw of events) {
      const event = raw as Record<string, unknown>;
      const text = formatEventForLog(event, this.resolveClassName);
      if (text) {
        this.combatLog.addEntry(text);
      }
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => {
      this.time.delayedCall(ms, resolve);
    });
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
      if (entry.data.position.x === x && entry.data.position.y === y) {
        return entry;
      }
    }
    return undefined;
  }

  private getObjectAt(x: number, y: number): MapObjectEntry | undefined {
    for (const entry of this.mapObjects.values()) {
      if (
        entry.data.position.x === x &&
        entry.data.position.y === y &&
        entry.data.hp !== 0
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
    this.activeMarker?.destroy();
    this.combatLog?.destroy();
    this.detailPanel?.destroy();
  }
}
