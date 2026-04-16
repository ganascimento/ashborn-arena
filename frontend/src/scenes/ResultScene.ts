import Phaser from "phaser";
import { createParticleTexture, drawPanel } from "./ui-utils";

const CLASS_DISPLAY: Record<string, string> = {
  warrior: "Guerreiro",
  mage: "Mago",
  cleric: "Clerigo",
  archer: "Arqueiro",
  assassin: "Assassino",
};

const STATUS_DISPLAY: Record<string, { text: string; color: string }> = {
  active: { text: "Vivo", color: "#44ff44" },
  knocked_out: { text: "Caido", color: "#ffaa00" },
  dead: { text: "Morto", color: "#ff4444" },
};

interface BattleSummaryChar {
  class_id: string;
  team: string;
  status: "active" | "knocked_out" | "dead";
}

interface ResultSceneData {
  result: "victory" | "defeat";
  characters: BattleSummaryChar[];
}

export default class ResultScene extends Phaser.Scene {
  private resultData!: ResultSceneData;

  constructor() {
    super("ResultScene");
  }

  init(data: ResultSceneData) {
    this.resultData = data;
  }

  create() {
    const { width, height } = this.scale;
    const isVictory = this.resultData.result === "victory";

    if (isVictory) {
      createParticleTexture(this, "result_particle", 3, 0xffd700);
      this.add.particles(0, 0, "result_particle", {
        x: { min: 0, max: width },
        y: height + 10,
        alpha: { start: 0.35, end: 0 },
        scale: { min: 0.1, max: 0.5 },
        speed: { min: 15, max: 35 },
        angle: { min: 260, max: 280 },
        lifespan: { min: 4000, max: 8000 },
        frequency: 250,
        blendMode: "ADD",
      });
    }

    const titleColor = isVictory ? "#ffd700" : "#ff4444";
    const glowColor = isVictory ? "#ffd700" : "#ff4444";

    this.add
      .text(width / 2, 120, isVictory ? "VITORIA!" : "DERROTA!", {
        fontSize: "56px",
        color: titleColor,
        fontFamily: "monospace",
        fontStyle: "bold",
        shadow: {
          offsetX: 0,
          offsetY: 0,
          color: glowColor,
          blur: 28,
          fill: true,
        },
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, 190, "Resumo da Batalha", {
        fontSize: "16px",
        color: "#7777aa",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    const lineGfx = this.add.graphics();
    lineGfx.lineStyle(1, 0x444466, 0.5);
    lineGfx.lineBetween(width / 2 - 180, 215, width / 2 + 180, 215);

    const playerChars = this.resultData.characters.filter(
      (c) => c.team === "player",
    );
    const aiChars = this.resultData.characters.filter(
      (c) => c.team !== "player",
    );

    this.renderTeamPanel(
      width / 2 - 170,
      245,
      "Seu Time",
      playerChars,
      0x4488ff,
    );
    this.renderTeamPanel(
      width / 2 + 170,
      245,
      "Time da IA",
      aiChars,
      0xff4444,
    );

    this.createBackButton(width / 2, 580);
  }

  private renderTeamPanel(
    cx: number,
    startY: number,
    title: string,
    chars: BattleSummaryChar[],
    accentColor: number,
  ) {
    const w = 260;
    const h = 50 + chars.length * 44 + 16;
    const x = cx - w / 2;

    drawPanel(this, x, startY, w, h, {
      fill: 0x16162a,
      fillAlpha: 0.9,
      border: accentColor,
      borderAlpha: 0.5,
      radius: 8,
    });

    const accentGfx = this.add.graphics();
    accentGfx.fillStyle(accentColor, 0.5);
    accentGfx.fillRoundedRect(x + 2, startY + 2, w - 4, 3, {
      tl: 8,
      tr: 8,
      bl: 0,
      br: 0,
    });

    this.add
      .text(cx, startY + 25, title, {
        fontSize: "17px",
        color: "#e0e0e0",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    chars.forEach((char, i) => {
      const charY = startY + 56 + i * 44;
      const className = CLASS_DISPLAY[char.class_id] ?? char.class_id;
      const statusInfo = STATUS_DISPLAY[char.status] ?? {
        text: char.status,
        color: "#cccccc",
      };

      const dotColor = Phaser.Display.Color.HexStringToColor(
        statusInfo.color,
      ).color;
      this.add.circle(x + 22, charY + 8, 5, dotColor);

      this.add.text(x + 36, charY, className, {
        fontSize: "15px",
        color: "#cccccc",
        fontFamily: "monospace",
      });

      this.add
        .text(x + w - 16, charY, statusInfo.text, {
          fontSize: "13px",
          color: statusInfo.color,
          fontFamily: "monospace",
        })
        .setOrigin(1, 0);
    });
  }

  private createBackButton(x: number, y: number) {
    const w = 220;
    const h = 44;
    const radius = 6;

    const bg = this.add.graphics();
    bg.fillStyle(0x1a1a30, 1);
    bg.fillRoundedRect(-w / 2, -h / 2, w, h, radius);
    bg.lineStyle(1, 0x3a3a5c, 0.5);
    bg.strokeRoundedRect(-w / 2, -h / 2, w, h, radius);

    const text = this.add
      .text(0, 0, "Voltar ao Menu", {
        fontSize: "18px",
        color: "#aaaacc",
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
      bg.fillStyle(0x1a1a30, 1);
      bg.fillRoundedRect(-w / 2, -h / 2, w, h, radius);
      bg.lineStyle(1, 0x3a3a5c, 0.5);
      bg.strokeRoundedRect(-w / 2, -h / 2, w, h, radius);
      text.setColor("#aaaacc");
      container.setScale(1);
    });

    container.on("pointerdown", () => this.scene.start("MenuScene"));
  }
}
