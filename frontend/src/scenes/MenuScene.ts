import Phaser from "phaser";
import { loadDifficulty, saveDifficulty } from "../network/storage";
import { createParticleTexture } from "./ui-utils";

const DIFFICULTIES = [
  { label: "Facil", value: "easy" },
  { label: "Normal", value: "normal" },
  { label: "Dificil", value: "hard" },
] as const;

export default class MenuScene extends Phaser.Scene {
  constructor() {
    super("MenuScene");
  }

  create() {
    const { width, height } = this.scale;
    const saved = loadDifficulty();
    const activeIndex = DIFFICULTIES.findIndex((d) => d.value === saved);

    this.createBackground(width, height);
    this.createParticles(width, height);

    this.add
      .text(width / 2, height * 0.18, "ASHBORN ARENA", {
        fontSize: "52px",
        color: "#e8d5a3",
        fontFamily: "monospace",
        fontStyle: "bold",
        shadow: {
          offsetX: 0,
          offsetY: 0,
          color: "#ffd700",
          blur: 24,
          fill: true,
        },
      })
      .setOrigin(0.5);

    const lineY = height * 0.245;
    const lineGfx = this.add.graphics();
    lineGfx.lineStyle(1, 0x665533, 0.5);
    lineGfx.lineBetween(width / 2 - 140, lineY, width / 2 - 6, lineY);
    lineGfx.lineBetween(width / 2 + 6, lineY, width / 2 + 140, lineY);
    lineGfx.fillStyle(0xffd700, 0.7);
    lineGfx.fillCircle(width / 2, lineY, 3);

    this.add
      .text(width / 2, height * 0.29, "Arena Tatica por Turnos", {
        fontSize: "15px",
        color: "#7777aa",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, height * 0.40, "DIFICULDADE", {
        fontSize: "12px",
        color: "#555577",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    const startY = height * 0.50;
    const spacing = 70;

    DIFFICULTIES.forEach((diff, i) => {
      const isActive = i === activeIndex;
      this.createDifficultyButton(
        width / 2,
        startY + i * spacing,
        diff.label,
        isActive,
        () => {
          saveDifficulty(diff.value);
          this.scene.start("PreparationScene", { difficulty: diff.value });
        },
      );
    });

    this.add
      .text(width / 2, height - 28, "MAPPO AI  \u00b7  v0.1", {
        fontSize: "11px",
        color: "#333355",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);
  }

  private createBackground(width: number, height: number) {
    const gfx = this.add.graphics();
    gfx.setDepth(-2);

    const steps = 10;
    for (let i = 0; i < steps; i++) {
      const alpha = 0.025 * (1 - i / steps);
      gfx.fillStyle(0x000000, alpha);
      gfx.fillRect(0, i * 14, width, 14);
      gfx.fillRect(0, height - (i + 1) * 14, width, 14);
      gfx.fillRect(i * 14, 0, 14, height);
      gfx.fillRect(width - (i + 1) * 14, 0, 14, height);
    }

    gfx.fillStyle(0x2244aa, 0.03);
    gfx.fillEllipse(width / 2, height * 0.35, width * 0.5, height * 0.5);
  }

  private createParticles(width: number, height: number) {
    createParticleTexture(this, "menu_particle", 3, 0xffd700);

    this.add.particles(0, 0, "menu_particle", {
      x: { min: 0, max: width },
      y: height + 10,
      alpha: { start: 0.3, end: 0 },
      scale: { min: 0.1, max: 0.4 },
      speed: { min: 10, max: 25 },
      angle: { min: 265, max: 275 },
      lifespan: { min: 5000, max: 9000 },
      frequency: 400,
      blendMode: "ADD",
    });
  }

  private createDifficultyButton(
    x: number,
    y: number,
    label: string,
    isActive: boolean,
    onClick: () => void,
  ) {
    const w = 260;
    const h = 50;
    const radius = 6;
    const defaultBorder = isActive ? 0xffd700 : 0x3a3a5c;
    const defaultBg = isActive ? 0x2a2a40 : 0x1a1a30;
    const defaultTextColor = isActive ? "#ffd700" : "#aaaacc";
    const defaultBorderAlpha = isActive ? 0.8 : 0.4;

    const bg = this.add.graphics();
    bg.fillStyle(defaultBg, 1);
    bg.fillRoundedRect(-w / 2, -h / 2, w, h, radius);
    bg.lineStyle(1, defaultBorder, defaultBorderAlpha);
    bg.strokeRoundedRect(-w / 2, -h / 2, w, h, radius);

    const text = this.add
      .text(0, 0, label, {
        fontSize: "22px",
        color: defaultTextColor,
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    const container = this.add.container(x, y, [bg, text]);
    container.setSize(w, h);
    container.setInteractive({ useHandCursor: true });

    container.on("pointerover", () => {
      bg.clear();
      bg.fillStyle(0x2a2a50, 1);
      bg.fillRoundedRect(-w / 2, -h / 2, w, h, radius);
      bg.lineStyle(1.5, 0x8888cc, 0.9);
      bg.strokeRoundedRect(-w / 2, -h / 2, w, h, radius);
      text.setColor("#ffffff");
      container.setScale(1.05);
    });

    container.on("pointerout", () => {
      bg.clear();
      bg.fillStyle(defaultBg, 1);
      bg.fillRoundedRect(-w / 2, -h / 2, w, h, radius);
      bg.lineStyle(1, defaultBorder, defaultBorderAlpha);
      bg.strokeRoundedRect(-w / 2, -h / 2, w, h, radius);
      text.setColor(defaultTextColor);
      container.setScale(1);
    });

    container.on("pointerdown", onClick);
  }
}
