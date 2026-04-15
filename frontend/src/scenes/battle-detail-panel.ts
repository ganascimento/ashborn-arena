import Phaser from "phaser";

const PANEL_DEPTH = 300;
const BG_COLOR = 0x1a1a2e;
const PLAYER_BORDER = 0x4488ff;
const ENEMY_BORDER = 0xff4444;
const PANEL_WIDTH = 280;
const LINE_H = 18;
const PAD = 12;

const ATTR_LABELS: Record<string, string> = {
  str: "FOR",
  dex: "DES",
  con: "CON",
  int_: "INT",
  wis: "SAB",
};

const ATTR_ORDER = ["str", "dex", "con", "int_", "wis"];

export interface DetailPanelData {
  className: string;
  team: string;
  currentHp: number;
  maxHp: number;
  pa?: number;
  attributes?: Record<string, number>;
  effects: { tag: string; duration?: number }[];
  abilities?: { name: string; cooldownRemaining: number }[];
}

export class CharacterDetailPanel {
  private scene: Phaser.Scene;
  private objects: Phaser.GameObjects.GameObject[] = [];
  private visible = false;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  show(data: DetailPanelData) {
    this.hide();

    const isAlly = data.team === "player";
    const borderColor = isAlly ? PLAYER_BORDER : ENEMY_BORDER;

    let lines = 1; // header
    if (data.pa !== undefined) lines++;
    if (isAlly && data.attributes) lines += 3; // separator + 2 rows of attrs
    lines += 2 + Math.max(data.effects.length, 1); // separator + "Efeitos:" + entries
    if (isAlly && data.abilities) {
      lines += 2 + data.abilities.length; // separator + "Habilidades:" + entries
    }

    const panelHeight = lines * LINE_H + PAD * 2;
    const cx = 640;
    const cy = 360;
    const left = cx - PANEL_WIDTH / 2;
    const top = cy - panelHeight / 2;

    const bg = this.scene.add.rectangle(cx, cy, PANEL_WIDTH, panelHeight, BG_COLOR);
    bg.setStrokeStyle(2, borderColor);
    bg.setDepth(PANEL_DEPTH);
    this.objects.push(bg);

    let y = top + PAD;

    y = this.addText(`${data.className}`, left + PAD, y, 14, "#ffffff");
    const hpText = `HP: ${data.currentHp}/${data.maxHp}`;
    const hpObj = this.scene.add.text(left + PANEL_WIDTH - PAD, y - LINE_H, hpText, {
      fontSize: "14px",
      fontFamily: "monospace",
      color: "#ffffff",
    });
    hpObj.setOrigin(1, 0);
    hpObj.setDepth(PANEL_DEPTH + 1);
    this.objects.push(hpObj);

    if (data.pa !== undefined) {
      y = this.addText(`PA: ${data.pa}/4`, left + PAD, y, 13, "#aaaaaa");
    }

    if (isAlly && data.attributes) {
      y = this.addSeparator(left, y);
      const attrs = data.attributes;
      const row1: string[] = [];
      const row2: string[] = [];
      for (let i = 0; i < ATTR_ORDER.length; i++) {
        const key = ATTR_ORDER[i];
        const val = attrs[key] ?? 0;
        const mod = val - 5;
        const sign = mod >= 0 ? "+" : "";
        const label = `${ATTR_LABELS[key]}: ${val} (${sign}${mod})`;
        if (i < 3) row1.push(label);
        else row2.push(label);
      }
      y = this.addText(row1.join("  "), left + PAD, y, 12, "#cccccc");
      y = this.addText(row2.join("  "), left + PAD, y, 12, "#cccccc");
    }

    y = this.addSeparator(left, y);
    y = this.addText("Efeitos:", left + PAD, y, 13, "#dddddd");
    if (data.effects.length === 0) {
      y = this.addText("  Nenhum", left + PAD, y, 12, "#888888");
    } else {
      for (const eff of data.effects) {
        const durStr = eff.duration ? ` (${eff.duration} turno${eff.duration > 1 ? "s" : ""})` : "";
        y = this.addText(`  ${eff.tag}${durStr}`, left + PAD, y, 12, "#cccccc");
      }
    }

    if (isAlly && data.abilities) {
      y = this.addSeparator(left, y);
      y = this.addText("Habilidades:", left + PAD, y, 13, "#dddddd");
      for (const ab of data.abilities) {
        const status = ab.cooldownRemaining > 0 ? `CD: ${ab.cooldownRemaining}` : "OK";
        const color = ab.cooldownRemaining > 0 ? "#ff8800" : "#44ff44";
        const nameObj = this.scene.add.text(left + PAD + 8, y, ab.name, {
          fontSize: "12px",
          fontFamily: "monospace",
          color: "#cccccc",
        });
        nameObj.setDepth(PANEL_DEPTH + 1);
        this.objects.push(nameObj);

        const statusObj = this.scene.add.text(left + PANEL_WIDTH - PAD, y, status, {
          fontSize: "12px",
          fontFamily: "monospace",
          color,
        });
        statusObj.setOrigin(1, 0);
        statusObj.setDepth(PANEL_DEPTH + 1);
        this.objects.push(statusObj);
        y += LINE_H;
      }
    }

    this.visible = true;
  }

  hide() {
    for (const obj of this.objects) {
      obj.destroy();
    }
    this.objects = [];
    this.visible = false;
  }

  isVisible(): boolean {
    return this.visible;
  }

  destroy() {
    this.hide();
  }

  private addText(text: string, x: number, y: number, size: number, color: string): number {
    const obj = this.scene.add.text(x, y, text, {
      fontSize: `${size}px`,
      fontFamily: "monospace",
      color,
    });
    obj.setDepth(PANEL_DEPTH + 1);
    this.objects.push(obj);
    return y + LINE_H;
  }

  private addSeparator(left: number, y: number): number {
    const line = this.scene.add.rectangle(
      left + PANEL_WIDTH / 2,
      y + LINE_H / 2 - 2,
      PANEL_WIDTH - PAD * 2,
      1,
      0x444466,
    );
    line.setDepth(PANEL_DEPTH + 1);
    this.objects.push(line);
    return y + LINE_H;
  }
}
