import type { AbilityOut } from "../network/types";
import { getIconTextureKey } from "./ability-icons";

export interface AbilityBarCallbacks {
  onAbilitySelected: (ability: AbilityOut) => void;
  onAbilityDeselected: () => void;
  onEndTurn: () => void;
}

const TYPE_COLORS: Record<string, number> = {
  heal: 0x2d7a3a,
  physical: 0x8b2020,
  magical: 0x4a2080,
  fire: 0xb84400,
  ice: 0x1a6080,
  electric: 0x806010,
  poison: 0x407020,
};

function getAbilityType(ability: AbilityOut): string {
  if (ability.heal_base > 0) return "heal";
  if (ability.elemental_tag && ability.elemental_tag !== "none") return ability.elemental_tag;
  return ability.damage_type || "physical";
}

const TOOLTIP_DEPTH = 400;
const BAR_DEPTH = 200;

export class BattleAbilityBar {
  private scene: Phaser.Scene;
  private baseX: number;
  private baseY: number;
  private callbacks: AbilityBarCallbacks;
  private abilities: AbilityOut[] = [];
  private currentPA: number = 4;
  private cooldowns: Map<string, number> = new Map();
  private selectedAbilityId: string | null = null;
  private objects: Phaser.GameObjects.GameObject[] = [];
  private tooltipObjects: Phaser.GameObjects.GameObject[] = [];

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    callbacks: AbilityBarCallbacks,
  ) {
    this.scene = scene;
    this.baseX = x;
    this.baseY = y;
    this.callbacks = callbacks;
  }

  show(
    abilities: AbilityOut[],
    pa: number,
    cooldowns: Map<string, number>,
  ) {
    for (const obj of this.objects) {
      obj.destroy();
    }
    this.objects = [];
    this.hideTooltip();

    this.abilities = abilities;
    this.currentPA = pa;
    this.cooldowns = cooldowns;

    const paText = this.scene.add.text(this.baseX, this.baseY, `PA: ${pa} / 4`, {
      fontSize: "18px",
      color: "#e0e0e0",
      fontFamily: "monospace",
    });
    paText.setDepth(BAR_DEPTH);
    this.objects.push(paText);

    for (let i = 0; i < abilities.length; i++) {
      const ability = abilities[i];
      const y = this.baseY + 35 + i * 48;
      const abilityType = getAbilityType(ability);
      const typeColor = TYPE_COLORS[abilityType] ?? 0x2a2a4c;

      const cd = this.cooldowns.get(ability.id) ?? 0;
      const enabled = this.currentPA >= ability.pa_cost && cd <= 0;
      const selected = this.selectedAbilityId === ability.id;

      const bg = this.scene.add.rectangle(this.baseX + 140, y + 21, 280, 42, 0x2a2a4c);
      bg.setDepth(BAR_DEPTH);
      this.objects.push(bg);

      const iconBg = this.scene.add.circle(this.baseX + 22, y + 21, 16, typeColor);
      iconBg.setDepth(BAR_DEPTH + 1);
      this.objects.push(iconBg);

      const texKey = getIconTextureKey(abilityType);
      if (this.scene.textures.exists(texKey)) {
        const icon = this.scene.add.image(this.baseX + 22, y + 21, texKey);
        icon.setDisplaySize(22, 22);
        icon.setDepth(BAR_DEPTH + 2);
        this.objects.push(icon);
      }

      let nameColor: string;
      if (selected) nameColor = "#ffd700";
      else if (enabled) nameColor = "#cccccc";
      else nameColor = "#555555";

      const nameText = this.scene.add.text(this.baseX + 44, y + 6, ability.name, {
        fontSize: "13px",
        color: nameColor,
        fontFamily: "monospace",
      });
      nameText.setDepth(BAR_DEPTH + 1);
      this.objects.push(nameText);

      let statusStr = `PA:${ability.pa_cost}`;
      if (cd > 0) statusStr = `CD:${cd}`;
      const statusColor = cd > 0 ? "#ff8800" : (enabled ? "#88cc88" : "#555555");
      const statusText = this.scene.add.text(this.baseX + 270, y + 6, statusStr, {
        fontSize: "12px",
        color: statusColor,
        fontFamily: "monospace",
      }).setOrigin(1, 0);
      statusText.setDepth(BAR_DEPTH + 1);
      this.objects.push(statusText);

      const hitZone = this.scene.add.rectangle(this.baseX + 140, y + 21, 280, 42, 0x000000, 0);
      hitZone.setDepth(BAR_DEPTH + 3);
      hitZone.setInteractive({ useHandCursor: enabled });

      if (enabled) {
        hitZone.on("pointerdown", () => this.handleSelect(ability));
      }
      hitZone.on("pointerover", () => {
        if (enabled && !selected) nameText.setColor("#ffffff");
        this.showTooltip(ability, y);
      });
      hitZone.on("pointerout", () => {
        if (selected) nameText.setColor("#ffd700");
        else if (enabled) nameText.setColor("#cccccc");
        else nameText.setColor("#555555");
        this.hideTooltip();
      });

      this.objects.push(hitZone);
    }

    const endY = this.baseY + 35 + abilities.length * 48 + 15;
    const endBg = this.scene.add.rectangle(this.baseX + 140, endY + 21, 280, 42, 0x2a2a4c);
    endBg.setDepth(BAR_DEPTH);
    this.objects.push(endBg);

    const endText = this.scene.add.text(this.baseX + 10, endY + 8, "Encerrar Turno", {
      fontSize: "14px",
      color: "#ffd700",
      fontFamily: "monospace",
    });
    endText.setDepth(BAR_DEPTH + 1);
    endText.setInteractive({ useHandCursor: true });
    endText.on("pointerdown", () => this.callbacks.onEndTurn());
    this.objects.push(endText);
  }

  hide() {
    for (const obj of this.objects) {
      obj.destroy();
    }
    this.objects = [];
    this.selectedAbilityId = null;
    this.hideTooltip();
  }

  private handleSelect(ability: AbilityOut) {
    if (this.selectedAbilityId === ability.id) {
      this.clearSelection();
      return;
    }
    this.selectedAbilityId = ability.id;
    this.callbacks.onAbilitySelected(ability);
    this.refresh();
  }

  clearSelection() {
    if (this.selectedAbilityId !== null) {
      this.selectedAbilityId = null;
      this.callbacks.onAbilityDeselected();
      this.refresh();
    }
  }

  getSelectedAbility(): AbilityOut | null {
    if (this.selectedAbilityId === null) return null;
    return this.abilities.find((a) => a.id === this.selectedAbilityId) ?? null;
  }

  setPA(pa: number) {
    this.currentPA = pa;
    this.refresh();
  }

  deductPA(cost: number) {
    this.currentPA = Math.max(0, this.currentPA - cost);
    this.refresh();
  }

  startCooldown(abilityId: string, turns: number) {
    this.cooldowns.set(abilityId, turns);
    this.refresh();
  }

  tickCooldowns() {
    for (const [id, remaining] of this.cooldowns) {
      const next = remaining - 1;
      if (next <= 0) {
        this.cooldowns.delete(id);
      } else {
        this.cooldowns.set(id, next);
      }
    }
    this.refresh();
  }

  destroy() {
    for (const obj of this.objects) {
      obj.destroy();
    }
    this.objects = [];
    this.hideTooltip();
  }

  private showTooltip(ability: AbilityOut, rowY: number) {
    this.hideTooltip();

    const abilityType = getAbilityType(ability);
    const lines: string[] = [ability.name];

    if (ability.damage_base > 0) {
      let dmgLine = `Dano: ${ability.damage_base} (${ability.damage_type})`;
      if (ability.elemental_tag && ability.elemental_tag !== "none") {
        dmgLine += ` [${ability.elemental_tag}]`;
      }
      lines.push(dmgLine);
    }
    if (ability.heal_base > 0) {
      lines.push(`Cura: ${ability.heal_base}`);
    }
    for (const effect of ability.effects) {
      lines.push(`Aplica: ${effect.tag} (${effect.duration} turnos)`);
    }
    if (ability.movement_type === "charge") {
      lines.push("Investida: move ate o alvo");
    } else if (ability.movement_type === "retreat") {
      lines.push("Recuo: move para tras");
    } else if (ability.movement_type === "teleport") {
      lines.push("Teleporte");
    }
    lines.push(`Alcance: ${ability.max_range}  Alvo: ${ability.target}`);
    lines.push(`PA: ${ability.pa_cost}  CD: ${ability.cooldown > 0 ? ability.cooldown + " turnos" : "nenhum"}`);

    const text = lines.join("\n");
    const tipX = this.baseX - 10;
    const tipY = rowY + 4;

    const tipText = this.scene.add.text(tipX, tipY, text, {
      fontSize: "12px",
      fontFamily: "monospace",
      color: "#eeeeee",
      backgroundColor: "#111122",
      padding: { x: 8, y: 6 },
      lineSpacing: 3,
    });
    tipText.setOrigin(1, 0);
    tipText.setDepth(TOOLTIP_DEPTH);

    const typeColor = TYPE_COLORS[abilityType] ?? 0x2a2a4c;
    const typeBar = this.scene.add.rectangle(
      tipText.x - tipText.width,
      tipText.y + tipText.height / 2,
      4,
      tipText.height,
      typeColor,
    );
    typeBar.setOrigin(1, 0.5);
    typeBar.setDepth(TOOLTIP_DEPTH);

    this.tooltipObjects.push(tipText, typeBar);
  }

  private hideTooltip() {
    for (const obj of this.tooltipObjects) {
      obj.destroy();
    }
    this.tooltipObjects = [];
  }

  private refresh() {
    this.show(this.abilities, this.currentPA, this.cooldowns);
  }
}
