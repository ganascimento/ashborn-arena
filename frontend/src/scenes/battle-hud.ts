import Phaser from "phaser";

const HP_BAR_WIDTH = 48;
const HP_BAR_HEIGHT = 6;
const HP_BAR_OFFSET_Y = 30;

const OBJ_HP_BAR_WIDTH = 32;
const OBJ_HP_BAR_HEIGHT = 3;
const OBJ_HP_BAR_OFFSET_Y = 28;

const STATUS_ABBR: Record<string, string> = {
  bleed: "BLD",
  poison: "PSN",
  slow: "SLW",
  immobilize: "IMB",
  silence: "SIL",
  taunt: "TNT",
  wet: "WET",
  frozen: "FRZ",
  burn: "BRN",
};

const STATUS_COLORS: Record<string, string> = {
  bleed: "#ff4444",
  poison: "#ff4444",
  slow: "#ff8800",
  silence: "#ff8800",
  immobilize: "#aa44ff",
  taunt: "#aa44ff",
  frozen: "#aa44ff",
  wet: "#88ccff",
  burn: "#ff8800",
};

const PRIORITY_ORDER: string[][] = [
  ["immobilize", "taunt", "frozen"],
  ["slow", "silence"],
  ["bleed", "poison"],
  ["wet", "burn"],
];

interface CharacterInfo {
  data: {
    position: { x: number; y: number };
    current_hp: number;
    max_hp: number;
  };
  status: string;
}

function hpColor(pct: number): number {
  if (pct > 0.5) return 0x44ff44;
  if (pct >= 0.25) return 0xffaa00;
  return 0xff4444;
}

export class BattleHud {
  private scene: Phaser.Scene;
  private hpBars: Map<
    string,
    { bg: Phaser.GameObjects.Rectangle; fill: Phaser.GameObjects.Rectangle }
  > = new Map();
  private objHpBars: Map<
    string,
    { bg: Phaser.GameObjects.Rectangle; fill: Phaser.GameObjects.Rectangle }
  > = new Map();
  private statusLabels: Map<string, Phaser.GameObjects.Text> = new Map();
  private floatingOffset: number = 0;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  createHpBar(
    entityId: string,
    worldX: number,
    worldY: number,
    currentHp: number,
    maxHp: number,
  ) {
    const barY = worldY + HP_BAR_OFFSET_Y;
    const bg = this.scene.add.rectangle(
      worldX,
      barY,
      HP_BAR_WIDTH,
      HP_BAR_HEIGHT,
      0x333333,
    );
    bg.setOrigin(0.5);
    bg.setDepth(100);

    const pct = Math.max(0, currentHp / maxHp);
    const fillWidth = pct * HP_BAR_WIDTH;
    const fillX = worldX - HP_BAR_WIDTH / 2 + fillWidth / 2;
    const fill = this.scene.add.rectangle(
      fillX,
      barY,
      fillWidth,
      HP_BAR_HEIGHT,
      hpColor(pct),
    );
    fill.setOrigin(0.5);
    fill.setDepth(100);

    this.hpBars.set(entityId, { bg, fill });
  }

  updateHpBar(
    entityId: string,
    worldX: number,
    worldY: number,
    currentHp: number,
    maxHp: number,
  ) {
    const entry = this.hpBars.get(entityId);
    if (!entry) {
      this.createHpBar(entityId, worldX, worldY, currentHp, maxHp);
      return;
    }

    const barY = worldY + HP_BAR_OFFSET_Y;
    entry.bg.setPosition(worldX, barY);

    const pct = Math.max(0, currentHp / maxHp);
    const fillWidth = pct * HP_BAR_WIDTH;
    entry.fill.setDisplaySize(fillWidth, HP_BAR_HEIGHT);
    entry.fill.setPosition(worldX - HP_BAR_WIDTH / 2 + fillWidth / 2, barY);
    entry.fill.setFillStyle(hpColor(pct));

    if (currentHp <= 0) {
      entry.fill.setDisplaySize(0, HP_BAR_HEIGHT);
      entry.bg.setStrokeStyle(1, 0xff4444);
    } else {
      entry.bg.setStrokeStyle(0);
    }
  }

  removeHpBar(entityId: string) {
    const entry = this.hpBars.get(entityId);
    if (entry) {
      entry.bg.destroy();
      entry.fill.destroy();
      this.hpBars.delete(entityId);
    }

    const label = this.statusLabels.get(entityId);
    if (label) {
      label.destroy();
      this.statusLabels.delete(entityId);
    }
  }

  updateStatusIcons(
    entityId: string,
    worldX: number,
    worldY: number,
    effects: Set<string>,
  ) {
    const existing = this.statusLabels.get(entityId);
    if (existing) {
      existing.destroy();
      this.statusLabels.delete(entityId);
    }

    if (effects.size === 0) return;

    const abbrs: string[] = [];
    for (const eff of effects) {
      const abbr = STATUS_ABBR[eff];
      if (abbr) abbrs.push(abbr);
    }
    if (abbrs.length === 0) return;

    let color = "#cccccc";
    for (const group of PRIORITY_ORDER) {
      for (const tag of group) {
        if (effects.has(tag)) {
          color = STATUS_COLORS[tag] ?? "#cccccc";
          break;
        }
      }
      if (color !== "#cccccc") break;
    }

    const label = this.scene.add.text(
      worldX,
      worldY + HP_BAR_OFFSET_Y - 14,
      abbrs.join(" "),
      {
        fontSize: "10px",
        color,
        fontFamily: "monospace",
      },
    );
    label.setOrigin(0.5);
    label.setDepth(101);
    this.statusLabels.set(entityId, label);
  }

  updateObjectHpBar(
    objId: string,
    worldX: number,
    worldY: number,
    currentHp: number,
    maxHp: number,
  ) {
    if (currentHp >= maxHp) {
      this.removeObjectHpBar(objId);
      return;
    }

    const barY = worldY + OBJ_HP_BAR_OFFSET_Y;
    const pct = Math.max(0, currentHp / maxHp);
    const fillWidth = pct * OBJ_HP_BAR_WIDTH;

    const existing = this.objHpBars.get(objId);
    if (existing) {
      existing.bg.setPosition(worldX, barY);
      existing.fill.setDisplaySize(fillWidth, OBJ_HP_BAR_HEIGHT);
      existing.fill.setPosition(
        worldX - OBJ_HP_BAR_WIDTH / 2 + fillWidth / 2,
        barY,
      );
      existing.fill.setFillStyle(hpColor(pct));
      return;
    }

    const bg = this.scene.add.rectangle(
      worldX,
      barY,
      OBJ_HP_BAR_WIDTH,
      OBJ_HP_BAR_HEIGHT,
      0x222222,
    );
    bg.setOrigin(0.5);
    bg.setDepth(100);
    bg.setAlpha(0.7);

    const fillX = worldX - OBJ_HP_BAR_WIDTH / 2 + fillWidth / 2;
    const fill = this.scene.add.rectangle(
      fillX,
      barY,
      fillWidth,
      OBJ_HP_BAR_HEIGHT,
      hpColor(pct),
    );
    fill.setOrigin(0.5);
    fill.setDepth(100);
    fill.setAlpha(0.85);

    this.objHpBars.set(objId, { bg, fill });
  }

  removeObjectHpBar(objId: string) {
    const entry = this.objHpBars.get(objId);
    if (entry) {
      entry.bg.destroy();
      entry.fill.destroy();
      this.objHpBars.delete(objId);
    }
  }

  updateObjectBars(
    mapObjects: Map<
      string,
      {
        data: {
          hp: number | null;
          max_hp: number | null;
          position: { x: number; y: number };
        };
      }
    >,
    gridToPixel: (x: number, y: number) => { px: number; py: number },
  ) {
    for (const [objId, entry] of mapObjects) {
      if (entry.data.hp === null || entry.data.max_hp === null) continue;
      if (entry.data.hp <= 0) {
        this.removeObjectHpBar(objId);
        continue;
      }
      if (entry.data.hp >= entry.data.max_hp) continue;
      const { px, py } = gridToPixel(
        entry.data.position.x,
        entry.data.position.y,
      );
      this.updateObjectHpBar(objId, px, py, entry.data.hp, entry.data.max_hp);
    }
  }

  spawnFloatingText(
    worldX: number,
    worldY: number,
    text: string,
    color: string,
    fontSize: string,
  ) {
    this.floatingOffset += 12;
    const textObj = this.scene.add.text(
      worldX,
      worldY - 20 - this.floatingOffset,
      text,
      {
        fontSize,
        color,
        fontFamily: "monospace",
        fontStyle: "bold",
      },
    );
    textObj.setOrigin(0.5);
    textObj.setDepth(200);

    this.scene.tweens.add({
      targets: textObj,
      y: textObj.y - 30,
      alpha: 0,
      duration: 800,
      ease: "Quad.Out",
      onComplete: () => textObj.destroy(),
    });

    this.scene.time.delayedCall(200, () => {
      this.floatingOffset = Math.max(0, this.floatingOffset - 12);
    });
  }

  updateAllBars(
    characters: Map<string, CharacterInfo>,
    gridToPixel: (x: number, y: number) => { px: number; py: number },
  ) {
    for (const [entityId, entry] of characters) {
      if (entry.status === "dead") {
        this.removeHpBar(entityId);
        continue;
      }
      const { px, py } = gridToPixel(
        entry.data.position.x,
        entry.data.position.y,
      );
      this.updateHpBar(
        entityId,
        px,
        py,
        entry.data.current_hp,
        entry.data.max_hp,
      );
    }
  }

  destroy() {
    for (const entry of this.hpBars.values()) {
      entry.bg.destroy();
      entry.fill.destroy();
    }
    this.hpBars.clear();

    for (const entry of this.objHpBars.values()) {
      entry.bg.destroy();
      entry.fill.destroy();
    }
    this.objHpBars.clear();

    for (const label of this.statusLabels.values()) {
      label.destroy();
    }
    this.statusLabels.clear();
  }
}
