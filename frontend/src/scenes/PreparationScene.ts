import Phaser from "phaser";
import type {
  BuildsDefaultsResponse,
  ClassInfo,
  DefaultBuild,
  AbilityOut,
  CharacterRequest,
} from "../network/types";
import { getDefaults, startBattle } from "../network/api-client";
import { saveBuild, loadBuild, saveLastTeam } from "../network/storage";
import {
  validateAttributePoints,
  validateAbilitySelection,
  validateTeam,
} from "../network/validation";
import { drawPanel } from "./ui-utils";

const CLASS_DISPLAY: Record<string, string> = {
  warrior: "Guerreiro",
  mage: "Mago",
  cleric: "Clerigo",
  archer: "Arqueiro",
  assassin: "Assassino",
};

const ATTR_KEYS = ["str", "dex", "con", "int_", "wis"] as const;

const ATTR_LABELS: Record<string, string> = {
  str: "FOR",
  dex: "DES",
  con: "CON",
  int_: "INT",
  wis: "SAB",
};

const LEFT_PANEL_WIDTH = 250;
const FONT = "monospace";

interface TeamMember {
  classId: string;
  attributePoints: number[];
  abilityIds: string[];
}

export default class PreparationScene extends Phaser.Scene {
  private difficulty = "normal";
  private classesInfo: ClassInfo[] = [];
  private defaultBuilds: DefaultBuild[] = [];
  private teamMembers: TeamMember[] = [];
  private selectedMemberIndex = -1;
  private autoBattle = false;

  private classPanelObjects: Phaser.GameObjects.GameObject[] = [];
  private buildPanelObjects: Phaser.GameObjects.GameObject[] = [];
  private teamListObjects: Phaser.GameObjects.GameObject[] = [];
  private confirmBtnContainer!: Phaser.GameObjects.Container;
  private confirmBtnBg!: Phaser.GameObjects.Graphics;
  private confirmBtnText!: Phaser.GameObjects.Text;
  private confirmValid = false;
  private autoBattleBtn!: Phaser.GameObjects.Text;
  private errorText!: Phaser.GameObjects.Text;

  constructor() {
    super("PreparationScene");
  }

  create() {
    const data = this.scene.settings.data as { difficulty?: string };
    if (data?.difficulty) this.difficulty = data.difficulty;

    this.teamMembers = [];
    this.selectedMemberIndex = -1;
    this.classPanelObjects = [];
    this.buildPanelObjects = [];
    this.teamListObjects = [];

    const loadingText = this.add
      .text(640, 360, "Carregando...", {
        fontSize: "28px",
        color: "#e0e0e0",
        fontFamily: FONT,
      })
      .setOrigin(0.5);

    getDefaults()
      .then((response) => {
        loadingText.destroy();
        this.classesInfo = response.classes;
        this.defaultBuilds = response.default_builds;
        this.renderUI();
      })
      .catch((err) => {
        loadingText.setText(`Erro: ${err.message}`);
        loadingText.setColor("#ff4444");
      });
  }

  private renderUI() {
    drawPanel(this, 10, 55, 232, 425, {
      fill: 0x14142a,
      fillAlpha: 0.85,
      border: 0x2a2a55,
      radius: 8,
    });
    drawPanel(this, LEFT_PANEL_WIDTH + 10, 55, 1280 - LEFT_PANEL_WIDTH - 30, 570, {
      fill: 0x121228,
      fillAlpha: 0.6,
      border: 0x2a2a55,
      borderAlpha: 0.5,
      radius: 8,
    });

    this.renderBackButton();
    this.renderClassPanel();
    this.renderTeamList();
    this.renderAutoBattleToggle();
    this.renderConfirmButton();
    this.renderErrorText();
  }

  private renderBackButton() {
    const btn = this.add
      .text(20, 20, "\u2190 Voltar", {
        fontSize: "18px",
        color: "#7777aa",
        fontFamily: FONT,
      })
      .setInteractive({ useHandCursor: true });

    btn.on("pointerover", () => btn.setColor("#bbbbdd"));
    btn.on("pointerout", () => btn.setColor("#7777aa"));
    btn.on("pointerdown", () => this.scene.start("MenuScene"));
  }

  private renderClassPanel() {
    this.classPanelObjects.forEach((o) => o.destroy());
    this.classPanelObjects = [];

    const title = this.add.text(22, 70, "Selecionar Classes", {
      fontSize: "16px",
      color: "#8888aa",
      fontFamily: FONT,
    });
    this.classPanelObjects.push(title);

    const titleLine = this.add.graphics();
    titleLine.lineStyle(1, 0x333366, 0.4);
    titleLine.lineBetween(22, 94, 228, 94);
    this.classPanelObjects.push(titleLine);

    const classIds = ["warrior", "mage", "cleric", "archer", "assassin"];
    const startY = 110;

    classIds.forEach((classId, i) => {
      const inTeam = this.teamMembers.some((m) => m.classId === classId);
      const teamFull = this.teamMembers.length >= 3;
      const disabled = inTeam || teamFull;

      const btn = this.add
        .text(30, startY + i * 40, CLASS_DISPLAY[classId], {
          fontSize: "18px",
          color: disabled ? "#555555" : "#44aaff",
          fontFamily: FONT,
        })
        .setInteractive({ useHandCursor: !disabled });

      if (!disabled) {
        btn.on("pointerover", () => btn.setColor("#88ccff"));
        btn.on("pointerout", () => btn.setColor("#44aaff"));
        btn.on("pointerdown", () => this.addClassToTeam(classId));
      }

      this.classPanelObjects.push(btn);
    });
  }

  private renderTeamList() {
    this.teamListObjects.forEach((o) => o.destroy());
    this.teamListObjects = [];

    const headerY = 330;

    const divider = this.add.graphics();
    divider.lineStyle(1, 0x333366, 0.3);
    divider.lineBetween(22, headerY - 10, 228, headerY - 10);
    this.teamListObjects.push(divider);

    const header = this.add.text(
      22,
      headerY,
      `Time: ${this.teamMembers.length}/3`,
      {
        fontSize: "16px",
        color: "#8888aa",
        fontFamily: FONT,
      },
    );
    this.teamListObjects.push(header);

    this.teamMembers.forEach((member, i) => {
      const y = headerY + 35 + i * 35;
      const isSelected = i === this.selectedMemberIndex;

      const nameBtn = this.add
        .text(30, y, CLASS_DISPLAY[member.classId], {
          fontSize: "16px",
          color: isSelected ? "#ffd700" : "#cccccc",
          fontFamily: FONT,
        })
        .setInteractive({ useHandCursor: true });

      nameBtn.on("pointerover", () => {
        if (!isSelected) nameBtn.setColor("#ffffff");
      });
      nameBtn.on("pointerout", () => {
        if (!isSelected) nameBtn.setColor("#cccccc");
      });
      nameBtn.on("pointerdown", () => this.selectMember(i));

      const removeBtn = this.add
        .text(180, y, "X", {
          fontSize: "16px",
          color: "#ff4444",
          fontFamily: FONT,
        })
        .setInteractive({ useHandCursor: true });

      removeBtn.on("pointerover", () => removeBtn.setColor("#ff8888"));
      removeBtn.on("pointerout", () => removeBtn.setColor("#ff4444"));
      removeBtn.on("pointerdown", () => this.removeMember(i));

      this.teamListObjects.push(nameBtn, removeBtn);
    });
  }

  private renderBuildPanel() {
    this.buildPanelObjects.forEach((o) => o.destroy());
    this.buildPanelObjects = [];

    if (this.selectedMemberIndex < 0) return;

    const member = this.teamMembers[this.selectedMemberIndex];
    const classInfo = this.classesInfo.find(
      (c) => c.class_id === member.classId,
    )!;

    const panelX = LEFT_PANEL_WIDTH + 20;
    const panelW = 1280 - panelX - 20;

    const className = this.add.text(
      panelX,
      70,
      CLASS_DISPLAY[member.classId],
      {
        fontSize: "22px",
        color: "#ffd700",
        fontFamily: FONT,
        shadow: {
          offsetX: 0,
          offsetY: 0,
          color: "#ffd700",
          blur: 12,
          fill: true,
        },
      },
    );
    this.buildPanelObjects.push(className);

    this.renderAttributes(panelX, 110, classInfo, member);
    this.renderAbilities(panelX, 340, classInfo, member, panelW);
  }

  private renderAttributes(
    x: number,
    startY: number,
    classInfo: ClassInfo,
    member: TeamMember,
  ) {
    const remaining =
      10 - member.attributePoints.reduce((a, b) => a + b, 0);

    const remainLabel = this.add.text(
      x,
      startY,
      `Pontos restantes: ${remaining}`,
      {
        fontSize: "16px",
        color: remaining === 0 ? "#44ff44" : "#ffaa00",
        fontFamily: FONT,
      },
    );
    this.buildPanelObjects.push(remainLabel);

    const conBase = classInfo.base_attributes["con"] ?? 0;
    const conAlloc = member.attributePoints[2];
    const conMod = conBase + conAlloc - 5;
    const hp = classInfo.hp_base + conMod * 5;

    const hpLabel = this.add.text(x + 500, startY, `HP: ${hp}`, {
      fontSize: "16px",
      color: "#ff6666",
      fontFamily: FONT,
    });
    this.buildPanelObjects.push(hpLabel);

    ATTR_KEYS.forEach((key, i) => {
      const y = startY + 35 + i * 36;
      const base = classInfo.base_attributes[key] ?? 0;
      const alloc = member.attributePoints[i];
      const final_ = base + alloc;
      const mod = final_ - 5;
      const modStr = mod >= 0 ? `+${mod}` : `${mod}`;

      const label = this.add.text(x, y, ATTR_LABELS[key], {
        fontSize: "15px",
        color: "#cccccc",
        fontFamily: FONT,
      });
      this.buildPanelObjects.push(label);

      const baseText = this.add.text(x + 50, y, `Base: ${base}`, {
        fontSize: "15px",
        color: "#888888",
        fontFamily: FONT,
      });
      this.buildPanelObjects.push(baseText);

      const minusDisabled = alloc <= 0;
      const minusBtn = this.add
        .text(x + 140, y, "[-]", {
          fontSize: "15px",
          color: minusDisabled ? "#444444" : "#ff8888",
          fontFamily: FONT,
        })
        .setInteractive({ useHandCursor: !minusDisabled });

      if (!minusDisabled) {
        minusBtn.on("pointerdown", () => {
          member.attributePoints[i] = Math.max(0, alloc - 1);
          this.refreshBuildPanel();
        });
      }
      this.buildPanelObjects.push(minusBtn);

      const allocText = this.add.text(x + 180, y, `${alloc}`, {
        fontSize: "15px",
        color: "#ffffff",
        fontFamily: FONT,
      });
      this.buildPanelObjects.push(allocText);

      const plusDisabled = alloc >= 5 || remaining <= 0;
      const plusBtn = this.add
        .text(x + 200, y, "[+]", {
          fontSize: "15px",
          color: plusDisabled ? "#444444" : "#88ff88",
          fontFamily: FONT,
        })
        .setInteractive({ useHandCursor: !plusDisabled });

      if (!plusDisabled) {
        plusBtn.on("pointerdown", () => {
          member.attributePoints[i] = Math.min(5, alloc + 1);
          this.refreshBuildPanel();
        });
      }
      this.buildPanelObjects.push(plusBtn);

      const finalText = this.add.text(
        x + 250,
        y,
        `= ${final_}  (mod: ${modStr})`,
        {
          fontSize: "15px",
          color: "#e0e0e0",
          fontFamily: FONT,
        },
      );
      this.buildPanelObjects.push(finalText);
    });
  }

  private renderAbilities(
    x: number,
    startY: number,
    classInfo: ClassInfo,
    member: TeamMember,
    panelW: number,
  ) {
    const selectedCount = member.abilityIds.length;

    const abilitiesHeader = this.add.text(
      x,
      startY,
      `Habilidades: ${selectedCount}/5`,
      {
        fontSize: "16px",
        color: selectedCount === 5 ? "#44ff44" : "#ffaa00",
        fontFamily: FONT,
      },
    );
    this.buildPanelObjects.push(abilitiesHeader);

    const cols = 3;
    const colWidth = Math.floor(panelW / cols);
    const rowsPerCol = 4;
    const rowHeight = 48;

    classInfo.abilities.forEach((ability, i) => {
      const col = Math.floor(i / rowsPerCol);
      const row = i % rowsPerCol;
      const ax = x + col * colWidth;
      const ay = startY + 30 + row * rowHeight;

      const isSelected = member.abilityIds.includes(ability.id);
      const maxReached = selectedCount >= 5 && !isSelected;

      const checkbox = isSelected ? "[x]" : "[ ]";
      const stats = this.formatAbilityStats(ability);
      const line1 = `${checkbox} ${ability.name}`;
      const line2 = `    ${stats}`;

      const color = maxReached
        ? "#555555"
        : isSelected
          ? "#44ff44"
          : "#cccccc";

      const abilityText = this.add
        .text(ax, ay, `${line1}\n${line2}`, {
          fontSize: "12px",
          color,
          fontFamily: FONT,
          lineSpacing: 1,
        })
        .setInteractive({ useHandCursor: !maxReached });

      if (!maxReached) {
        abilityText.on("pointerover", () => {
          if (!member.abilityIds.includes(ability.id)) {
            abilityText.setColor("#ffffff");
          }
        });
        abilityText.on("pointerout", () => {
          const sel = member.abilityIds.includes(ability.id);
          abilityText.setColor(sel ? "#44ff44" : "#cccccc");
        });
        abilityText.on("pointerdown", () =>
          this.toggleAbility(member, ability.id),
        );
      }

      this.buildPanelObjects.push(abilityText);
    });
  }

  private formatAbilityStats(ability: AbilityOut): string {
    const parts = [`PA:${ability.pa_cost}`, `CD:${ability.cooldown}`, `R:${ability.max_range}`];

    if (ability.damage_base > 0) {
      parts.push(`D:${ability.damage_base}`);
    }
    if (ability.heal_base > 0) {
      parts.push(`H:${ability.heal_base}`);
    }
    if (ability.elemental_tag && ability.elemental_tag !== "none") {
      parts.push(`[${ability.elemental_tag}]`);
    }

    return parts.join(" ");
  }

  private toggleAbility(member: TeamMember, abilityId: string) {
    const idx = member.abilityIds.indexOf(abilityId);
    if (idx >= 0) {
      member.abilityIds.splice(idx, 1);
    } else if (member.abilityIds.length < 5) {
      member.abilityIds.push(abilityId);
    }
    this.refreshBuildPanel();
  }

  private refreshBuildPanel() {
    this.renderBuildPanel();
    this.updateConfirmButton();
  }

  private addClassToTeam(classId: string) {
    if (this.teamMembers.length >= 3) return;
    if (this.teamMembers.some((m) => m.classId === classId)) return;

    const saved = loadBuild(classId);
    const defaultBuild = this.defaultBuilds.find(
      (b) => b.class_id === classId,
    );

    let attributePoints: number[];
    let abilityIds: string[];

    if (saved) {
      attributePoints = [...saved.attribute_points];
      abilityIds = [...saved.ability_ids];
    } else if (defaultBuild) {
      attributePoints = [...defaultBuild.attribute_points];
      abilityIds = [...defaultBuild.ability_ids];
    } else {
      attributePoints = [2, 2, 2, 2, 2];
      abilityIds = [];
    }

    this.teamMembers.push({ classId, attributePoints, abilityIds });
    this.selectedMemberIndex = this.teamMembers.length - 1;

    this.renderClassPanel();
    this.renderTeamList();
    this.renderBuildPanel();
    this.updateConfirmButton();
  }

  private removeMember(index: number) {
    this.teamMembers.splice(index, 1);

    if (this.teamMembers.length === 0) {
      this.selectedMemberIndex = -1;
    } else if (this.selectedMemberIndex >= this.teamMembers.length) {
      this.selectedMemberIndex = this.teamMembers.length - 1;
    } else if (this.selectedMemberIndex === index) {
      this.selectedMemberIndex = Math.min(
        index,
        this.teamMembers.length - 1,
      );
    }

    this.renderClassPanel();
    this.renderTeamList();
    this.renderBuildPanel();
    this.updateConfirmButton();
  }

  private selectMember(index: number) {
    this.selectedMemberIndex = index;
    this.renderTeamList();
    this.renderBuildPanel();
  }

  private renderAutoBattleToggle() {
    const checkbox = this.autoBattle ? "[x]" : "[ ]";
    this.autoBattleBtn = this.add
      .text(30, 495, `${checkbox} IA joga por mim`, {
        fontSize: "14px",
        color: this.autoBattle ? "#44ff44" : "#8888aa",
        fontFamily: FONT,
      })
      .setInteractive({ useHandCursor: true });

    this.autoBattleBtn.on("pointerover", () =>
      this.autoBattleBtn.setColor(this.autoBattle ? "#88ff88" : "#bbbbdd"),
    );
    this.autoBattleBtn.on("pointerout", () =>
      this.autoBattleBtn.setColor(this.autoBattle ? "#44ff44" : "#8888aa"),
    );
    this.autoBattleBtn.on("pointerdown", () => {
      this.autoBattle = !this.autoBattle;
      const cb = this.autoBattle ? "[x]" : "[ ]";
      this.autoBattleBtn.setText(`${cb} IA joga por mim`);
      this.autoBattleBtn.setColor(this.autoBattle ? "#44ff44" : "#8888aa");
    });
  }

  private renderConfirmButton() {
    const cx = 640;
    const cy = 690;

    this.confirmBtnBg = this.add.graphics();
    this.confirmBtnText = this.add
      .text(0, 0, "Confirmar", {
        fontSize: "20px",
        color: "#1a1a2e",
        fontFamily: FONT,
        fontStyle: "bold",
      })
      .setOrigin(0.5);

    this.confirmBtnContainer = this.add.container(cx, cy, [
      this.confirmBtnBg,
      this.confirmBtnText,
    ]);
    this.confirmBtnContainer.setSize(220, 48);
    this.confirmBtnContainer.setInteractive({ useHandCursor: true });

    this.confirmBtnContainer.on("pointerover", () => {
      if (this.confirmValid) this.confirmBtnContainer.setScale(1.05);
    });
    this.confirmBtnContainer.on("pointerout", () =>
      this.confirmBtnContainer.setScale(1),
    );
    this.confirmBtnContainer.on("pointerdown", () => this.onConfirm());

    this.updateConfirmButton();
  }

  private drawConfirmBg(color: number) {
    const w = 220;
    const h = 48;
    const radius = 14;
    this.confirmBtnBg.clear();
    this.confirmBtnBg.fillStyle(color, 1);
    this.confirmBtnBg.fillRoundedRect(-w / 2, -h / 2, w, h, radius);
  }

  private renderErrorText() {
    this.errorText = this.add
      .text(640, 650, "", {
        fontSize: "16px",
        color: "#ff4444",
        fontFamily: FONT,
      })
      .setOrigin(0.5);
  }

  private isTeamValid(): boolean {
    const classIds = this.teamMembers.map((m) => m.classId);
    if (!validateTeam(classIds)) return false;

    return this.teamMembers.every((member) => {
      const classInfo = this.classesInfo.find(
        (c) => c.class_id === member.classId,
      );
      if (!classInfo) return false;

      if (!validateAttributePoints(member.attributePoints)) return false;

      const availableIds = classInfo.abilities.map((a) => a.id);
      return validateAbilitySelection(member.abilityIds, availableIds);
    });
  }

  private updateConfirmButton() {
    if (!this.confirmBtnBg) return;

    this.confirmValid = this.isTeamValid();
    this.drawConfirmBg(this.confirmValid ? 0x44ff44 : 0x555555);
    this.confirmBtnText.setColor(this.confirmValid ? "#1a1a2e" : "#888888");
  }

  private async onConfirm() {
    if (!this.isTeamValid()) return;

    this.errorText.setText("");

    this.teamMembers.forEach((member) => {
      saveBuild(member.classId, {
        attribute_points: member.attributePoints,
        ability_ids: member.abilityIds,
      });
    });

    saveLastTeam(this.teamMembers.map((m) => m.classId));

    const team: CharacterRequest[] = this.teamMembers.map((m) => ({
      class_id: m.classId,
      attribute_points: m.attributePoints,
      ability_ids: m.abilityIds,
    }));

    try {
      this.confirmBtnText.setText("Iniciando...");
      this.confirmBtnContainer.disableInteractive();

      const response = await startBattle(this.difficulty, team, this.autoBattle);

      this.scene.start("BattleScene", {
        session_id: response.session_id,
        initial_state: response.initial_state,
        auto_battle: this.autoBattle,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido";
      this.errorText.setText(`Erro ao iniciar batalha: ${msg}`);
      this.confirmBtnText.setText("Confirmar");
      this.confirmBtnContainer.setInteractive({ useHandCursor: true });
    }
  }
}
