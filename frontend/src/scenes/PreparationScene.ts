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

  private classPanelObjects: Phaser.GameObjects.GameObject[] = [];
  private buildPanelObjects: Phaser.GameObjects.GameObject[] = [];
  private teamListObjects: Phaser.GameObjects.GameObject[] = [];
  private confirmBtn!: Phaser.GameObjects.Text;
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
    this.renderBackButton();
    this.renderClassPanel();
    this.renderTeamList();
    this.renderConfirmButton();
    this.renderErrorText();
  }

  private renderBackButton() {
    const btn = this.add
      .text(20, 20, "\u2190 Voltar", {
        fontSize: "20px",
        color: "#aaaaaa",
        fontFamily: FONT,
      })
      .setInteractive({ useHandCursor: true });

    btn.on("pointerover", () => btn.setColor("#ffffff"));
    btn.on("pointerout", () => btn.setColor("#aaaaaa"));
    btn.on("pointerdown", () => this.scene.start("MenuScene"));
  }

  private renderClassPanel() {
    this.classPanelObjects.forEach((o) => o.destroy());
    this.classPanelObjects = [];

    const title = this.add.text(20, 70, "Selecionar Classes", {
      fontSize: "20px",
      color: "#e0e0e0",
      fontFamily: FONT,
    });
    this.classPanelObjects.push(title);

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
    const header = this.add.text(
      20,
      headerY,
      `Time: ${this.teamMembers.length}/3`,
      {
        fontSize: "18px",
        color: "#e0e0e0",
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
        fontSize: "24px",
        color: "#ffd700",
        fontFamily: FONT,
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

    const colWidth = Math.floor(panelW / 2);
    const rowsPerCol = 6;

    classInfo.abilities.forEach((ability, i) => {
      const col = i < rowsPerCol ? 0 : 1;
      const row = col === 0 ? i : i - rowsPerCol;
      const ax = x + col * colWidth;
      const ay = startY + 30 + row * 55;

      const isSelected = member.abilityIds.includes(ability.id);
      const maxReached = selectedCount >= 5 && !isSelected;

      const checkbox = isSelected ? "[x]" : "[ ]";
      const dmgInfo = this.formatAbilityInfo(ability);
      const line1 = `${checkbox} ${ability.name}`;
      const line2 = `    PA:${ability.pa_cost} CD:${ability.cooldown} Alcance:${ability.max_range} ${dmgInfo}`;

      const color = maxReached
        ? "#555555"
        : isSelected
          ? "#44ff44"
          : "#cccccc";

      const abilityText = this.add
        .text(ax, ay, `${line1}\n${line2}`, {
          fontSize: "13px",
          color,
          fontFamily: FONT,
          lineSpacing: 2,
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

  private formatAbilityInfo(ability: AbilityOut): string {
    const parts: string[] = [];

    if (ability.damage_base > 0) {
      parts.push(`Dano:${ability.damage_base} ${ability.damage_type}`);
    }
    if (ability.heal_base > 0) {
      parts.push(`Cura:${ability.heal_base}`);
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

  private renderConfirmButton() {
    this.confirmBtn = this.add
      .text(640, 690, "Confirmar", {
        fontSize: "24px",
        color: "#1a1a2e",
        fontFamily: FONT,
        backgroundColor: "#555555",
        padding: { x: 20, y: 8 },
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });

    this.confirmBtn.on("pointerdown", () => this.onConfirm());
    this.updateConfirmButton();
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
    if (!this.confirmBtn) return;

    const valid = this.isTeamValid();
    this.confirmBtn.setStyle({
      backgroundColor: valid ? "#44ff44" : "#555555",
      color: "#1a1a2e",
    });
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
      this.confirmBtn.setText("Iniciando...");
      this.confirmBtn.disableInteractive();

      const response = await startBattle(this.difficulty, team);

      this.scene.start("BattleScene", {
        session_id: response.session_id,
        initial_state: response.initial_state,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Erro desconhecido";
      this.errorText.setText(`Erro ao iniciar batalha: ${msg}`);
      this.confirmBtn.setText("Confirmar");
      this.confirmBtn.setInteractive({ useHandCursor: true });
    }
  }
}
