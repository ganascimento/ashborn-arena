import type { AbilityOut } from "../network/types";

export interface AbilityBarCallbacks {
  onAbilitySelected: (ability: AbilityOut) => void;
  onAbilityDeselected: () => void;
  onEndTurn: () => void;
}

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

    this.abilities = abilities;
    this.currentPA = pa;
    this.cooldowns = cooldowns;

    const paText = this.scene.add.text(this.baseX, this.baseY, `PA: ${pa} / 4`, {
      fontSize: "18px",
      color: "#e0e0e0",
      fontFamily: "monospace",
    });
    this.objects.push(paText);

    for (let i = 0; i < abilities.length; i++) {
      const ability = abilities[i];
      const y = this.baseY + 35 + i * 48;

      const bg = this.scene.add.rectangle(
        this.baseX + 140,
        y + 21,
        280,
        42,
        0x2a2a4c,
      );
      this.objects.push(bg);

      const cd = this.cooldowns.get(ability.id) ?? 0;
      let label = `${ability.name}  PA:${ability.pa_cost}`;
      if (cd > 0) {
        label += `  CD:${cd}`;
      }

      const enabled =
        this.currentPA >= ability.pa_cost && cd <= 0;

      let color: string;
      if (this.selectedAbilityId === ability.id) {
        color = "#ffd700";
      } else if (enabled) {
        color = "#cccccc";
      } else {
        color = "#555555";
      }

      const text = this.scene.add.text(this.baseX + 10, y + 8, label, {
        fontSize: "14px",
        color,
        fontFamily: "monospace",
      });

      if (enabled) {
        text.setInteractive({ useHandCursor: true });
        text.on("pointerdown", () => this.handleSelect(ability));
        text.on("pointerover", () => {
          if (this.selectedAbilityId !== ability.id) {
            text.setColor("#ffffff");
          }
        });
        text.on("pointerout", () => {
          if (this.selectedAbilityId === ability.id) {
            text.setColor("#ffd700");
          } else {
            text.setColor("#cccccc");
          }
        });
      }

      this.objects.push(text);
    }

    const endY = this.baseY + 35 + abilities.length * 48 + 15;
    const endBg = this.scene.add.rectangle(
      this.baseX + 140,
      endY + 21,
      280,
      42,
      0x2a2a4c,
    );
    this.objects.push(endBg);

    const endText = this.scene.add.text(
      this.baseX + 10,
      endY + 8,
      "Encerrar Turno",
      {
        fontSize: "14px",
        color: "#ffd700",
        fontFamily: "monospace",
      },
    );
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
    return (
      this.abilities.find((a) => a.id === this.selectedAbilityId) ?? null
    );
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
  }

  private refresh() {
    this.show(this.abilities, this.currentPA, this.cooldowns);
  }
}
