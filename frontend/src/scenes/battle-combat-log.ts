import Phaser from "phaser";

const MAX_ENTRIES = 50;
const LINE_HEIGHT = 16;
const PADDING = 5;
const LOG_DEPTH = 250;

export class BattleCombatLog {
  private scene: Phaser.Scene;
  private entries: string[] = [];
  private bg: Phaser.GameObjects.Graphics;
  private textObj: Phaser.GameObjects.Text;
  private visibleLines: number;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    width: number,
    height: number,
  ) {
    this.scene = scene;
    this.visibleLines = Math.floor((height - PADDING * 2) / LINE_HEIGHT);

    this.bg = scene.add.graphics();
    this.bg.setDepth(LOG_DEPTH);
    this.bg.fillStyle(0x14142a, 0.88);
    this.bg.fillRoundedRect(x, y, width, height, 6);
    this.bg.lineStyle(1, 0x333366, 0.5);
    this.bg.strokeRoundedRect(x, y, width, height, 6);

    this.textObj = scene.add.text(x + PADDING, y + PADDING, "", {
      fontSize: "12px",
      fontFamily: "monospace",
      color: "#cccccc",
      wordWrap: { width: width - PADDING * 2 },
      lineSpacing: 2,
    });
    this.textObj.setDepth(LOG_DEPTH + 1);
  }

  addEntry(text: string) {
    this.entries.push(text);
    if (this.entries.length > MAX_ENTRIES) {
      this.entries.shift();
    }
    const visible = this.entries.slice(-this.visibleLines);
    this.textObj.setText(visible.join("\n"));
  }

  destroy() {
    this.bg.destroy();
    this.textObj.destroy();
  }
}

export function formatEventForLog(
  event: Record<string, unknown>,
  resolveClass: (entityId: string) => string,
): string | null {
  const type = event.type as string;

  const entity = (event.entity ??
    event.character ??
    event.attacker ??
    event.healer) as string | undefined;
  const target = event.target as string | undefined;
  const cls = entity ? resolveClass(entity) : "???";
  const tgt = target ? resolveClass(target) : undefined;

  switch (type) {
    case "move":
    case "ability_movement": {
      const to = (event.to ?? event.position) as
        | [number, number]
        | { x: number; y: number }
        | undefined;
      if (to) {
        const [x, y] = Array.isArray(to) ? to : [to.x, to.y];
        return `${cls} moveu para (${x},${y})`;
      }
      return null;
    }
    case "basic_attack": {
      const dmg = (event.damage ?? event.amount ?? 0) as number;
      return `${cls} atacou ${tgt ?? "?"} — ${dmg} dano`;
    }
    case "ability": {
      const name = event.ability_name as string | undefined;
      const dmg = (event.damage ?? event.amount ?? 0) as number;
      const heal = (event.heal ?? 0) as number;
      if (heal > 0) {
        return `${cls} usou ${name ?? "habilidade"} em ${tgt ?? cls} — +${heal} cura`;
      }
      return `${cls} usou ${name ?? "habilidade"} em ${tgt ?? "?"} — ${dmg} dano`;
    }
    case "aoe_hit": {
      const dmg = (event.damage ?? event.amount ?? 0) as number;
      return `${cls} recebeu ${dmg} dano [AoE]`;
    }
    case "bleed":
    case "dot_tick": {
      const dmg = (event.damage ?? event.amount ?? 0) as number;
      const tag = (event.tag ?? type) as string;
      return `${cls} sofreu ${dmg} dano (${tag})`;
    }
    case "heal":
    case "hot_tick": {
      const heal = (event.heal ?? event.amount ?? 0) as number;
      return `${cls} recuperou ${heal} HP`;
    }
    case "knocked_out":
      return `${cls} foi nocauteado!`;
    case "death":
      return `${cls} morreu!`;
    case "effect_applied": {
      const tag = event.tag as string | undefined;
      return `${tgt ?? cls} recebeu efeito: ${tag ?? "?"}`;
    }
    case "effect_expired": {
      const tag = event.tag as string | undefined;
      return `Efeito ${tag ?? "?"} expirou em ${cls}`;
    }
    case "object_hit": {
      const dmg = (event.damage ?? 0) as number;
      const destroyed = event.destroyed as boolean | undefined;
      const objId = event.object as string | undefined;
      const label = objId?.replace(/_\d+$/, "") ?? "objeto";
      if (destroyed) {
        return `${cls} destruiu ${label} — ${dmg} dano`;
      }
      return `${cls} atingiu ${label} — ${dmg} dano`;
    }
    default:
      return null;
  }
}
