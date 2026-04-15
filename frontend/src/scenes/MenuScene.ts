import Phaser from "phaser";
import { loadDifficulty, saveDifficulty } from "../network/storage";

const DIFFICULTIES = [
  { label: "Facil", value: "easy" },
  { label: "Normal", value: "normal" },
  { label: "Dificil", value: "hard" },
] as const;

const COLOR_HIGHLIGHT = "#ffd700";
const COLOR_DEFAULT = "#aaaaaa";
const COLOR_HOVER = "#ffffff";

export default class MenuScene extends Phaser.Scene {
  constructor() {
    super("MenuScene");
  }

  create() {
    const { width, height } = this.scale;
    const saved = loadDifficulty();
    const activeIndex = DIFFICULTIES.findIndex((d) => d.value === saved);

    this.add
      .text(width / 2, height * 0.2, "Ashborn Arena", {
        fontSize: "48px",
        color: "#e0e0e0",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    const startY = height * 0.45;
    const spacing = 60;

    DIFFICULTIES.forEach((diff, i) => {
      const btn = this.add
        .text(width / 2, startY + i * spacing, diff.label, {
          fontSize: "32px",
          color: i === activeIndex ? COLOR_HIGHLIGHT : COLOR_DEFAULT,
          fontFamily: "monospace",
        })
        .setOrigin(0.5)
        .setInteractive({ useHandCursor: true });

      btn.on("pointerover", () => {
        btn.setScale(1.15);
        if (i !== activeIndex) btn.setColor(COLOR_HOVER);
      });

      btn.on("pointerout", () => {
        btn.setScale(1);
        if (i !== activeIndex) btn.setColor(COLOR_DEFAULT);
      });

      btn.on("pointerdown", () => {
        saveDifficulty(diff.value);
        this.scene.start("PreparationScene", { difficulty: diff.value });
      });
    });
  }
}
