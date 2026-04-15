import Phaser from "phaser";

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
    const isVictory = this.resultData.result === "victory";

    this.add
      .text(640, 150, isVictory ? "VITORIA!" : "DERROTA!", {
        fontSize: "52px",
        color: isVictory ? "#44ff44" : "#ff4444",
        fontFamily: "monospace",
        fontStyle: "bold",
      })
      .setOrigin(0.5);

    this.add
      .text(640, 220, "Resumo da Batalha", {
        fontSize: "18px",
        color: "#888888",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    this.renderTeamBlock(
      400,
      280,
      "Seu Time",
      this.resultData.characters.filter((c) => c.team === "player"),
    );

    this.renderTeamBlock(
      880,
      280,
      "Time da IA",
      this.resultData.characters.filter((c) => c.team !== "player"),
    );

    const backBtn = this.add
      .text(640, 600, "Voltar ao Menu", {
        fontSize: "24px",
        color: "#aaaaaa",
        fontFamily: "monospace",
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });

    backBtn.on("pointerover", () => {
      backBtn.setColor("#ffffff");
      backBtn.setScale(1.1);
    });

    backBtn.on("pointerout", () => {
      backBtn.setColor("#aaaaaa");
      backBtn.setScale(1);
    });

    backBtn.on("pointerdown", () => {
      this.scene.start("MenuScene");
    });
  }

  private renderTeamBlock(
    x: number,
    y: number,
    title: string,
    chars: BattleSummaryChar[],
  ) {
    this.add
      .text(x, y, title, {
        fontSize: "22px",
        color: "#e0e0e0",
        fontFamily: "monospace",
      })
      .setOrigin(0.5);

    chars.forEach((char, i) => {
      const charY = y + 50 + i * 40;
      const className = CLASS_DISPLAY[char.class_id] ?? char.class_id;
      const statusInfo = STATUS_DISPLAY[char.status] ?? {
        text: char.status,
        color: "#cccccc",
      };

      this.add
        .text(x, charY, `${className}  —  ${statusInfo.text}`, {
          fontSize: "18px",
          color: statusInfo.color,
          fontFamily: "monospace",
        })
        .setOrigin(0.5);
    });
  }
}
