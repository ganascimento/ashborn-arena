import Phaser from "phaser";

interface CharacterEntry {
  data: { team: string; position: { x: number; y: number }; current_hp: number; max_hp: number };
  sprite: Phaser.GameObjects.Container;
  circle: Phaser.GameObjects.Arc;
  status: "active" | "knocked_out" | "dead";
}

interface MapObjectEntry {
  data: { position: { x: number; y: number } };
  sprite: Phaser.GameObjects.Rectangle;
}

const MOVE_TYPES = new Set(["move", "ability_movement"]);

const DAMAGE_TYPES = new Set([
  "basic_attack",
  "ability",
  "aoe_hit",
  "opportunity_attack",
  "chain_primary",
  "chain_secondary",
]);

const HEAL_TYPES = new Set(["heal", "self_heal", "lifesteal"]);

const DOT_TYPES = new Set(["bleed", "dot_tick"]);

const HOT_TYPES = new Set(["hot_tick"]);

function getTeamColor(team: string): number {
  return team === "player" ? 0x4488ff : 0xff4444;
}

export class BattleAnimations {
  private scene: Phaser.Scene;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  private tweenPromise(config: Phaser.Types.Tweens.TweenBuilderConfig): Promise<void> {
    return new Promise((resolve) => {
      this.scene.tweens.add({
        ...config,
        onComplete: () => resolve(),
      });
    });
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => {
      this.scene.time.delayedCall(ms, () => resolve());
    });
  }

  async animateMove(container: Phaser.GameObjects.Container, toPx: number, toPy: number): Promise<void> {
    await this.tweenPromise({
      targets: container,
      x: toPx,
      y: toPy,
      duration: 300,
      ease: "Quad.InOut",
    });
  }

  async animateDamage(circle: Phaser.GameObjects.Arc, originalColor: number): Promise<void> {
    circle.setFillStyle(0xff4444);
    await this.delay(200);
    circle.setFillStyle(originalColor);
  }

  async animateHeal(circle: Phaser.GameObjects.Arc, originalColor: number): Promise<void> {
    circle.setFillStyle(0x44ff44);
    await this.delay(200);
    circle.setFillStyle(originalColor);
  }

  async animateDot(circle: Phaser.GameObjects.Arc, originalColor: number): Promise<void> {
    circle.setFillStyle(0xcc4444);
    await this.delay(150);
    circle.setFillStyle(originalColor);
  }

  async animateKnockout(container: Phaser.GameObjects.Container): Promise<void> {
    await this.tweenPromise({
      targets: container,
      alpha: 0.4,
      duration: 200,
    });
  }

  async animateRevive(container: Phaser.GameObjects.Container): Promise<void> {
    await this.tweenPromise({
      targets: container,
      alpha: 1.0,
      duration: 200,
    });
  }

  async animateDeath(container: Phaser.GameObjects.Container): Promise<void> {
    await this.tweenPromise({
      targets: container,
      alpha: 0,
      duration: 300,
    });
    container.destroy();
  }

  async animateObjectDestroy(rect: Phaser.GameObjects.Rectangle): Promise<void> {
    await this.tweenPromise({
      targets: rect,
      alpha: 0,
      duration: 200,
    });
    rect.destroy();
  }

  async processEventsAnimated(
    events: unknown[],
    getCharacter: (id: string) => CharacterEntry | undefined,
    getMapObject: (id: string) => MapObjectEntry | undefined,
    gridToPixel: (x: number, y: number) => { px: number; py: number },
    updateState: (event: Record<string, unknown>) => void,
    onFloatingText?: (worldX: number, worldY: number, text: string, color: string, fontSize: string) => void,
  ): Promise<void> {
    if (!events || events.length === 0) return;

    for (const raw of events) {
      const event = raw as Record<string, unknown>;
      const type = event.type as string | undefined;
      if (!type) continue;

      updateState(event);

      if (MOVE_TYPES.has(type)) {
        const entityId = (event.entity ?? event.character) as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        const dest = (event.to ?? event.position) as
          | [number, number]
          | { x: number; y: number }
          | undefined;
        if (!dest) continue;

        const [dx, dy] = Array.isArray(dest) ? dest : [dest.x, dest.y];
        const { px, py } = gridToPixel(dx, dy);
        await this.animateMove(entry.sprite, px, py);
      } else if (DAMAGE_TYPES.has(type)) {
        const targetId = event.target as string | undefined;
        if (!targetId) continue;
        const entry = getCharacter(targetId);
        if (!entry) continue;

        const color = getTeamColor(entry.data.team);
        await this.animateDamage(entry.circle, color);
        if (onFloatingText) {
          const amount = (event.damage ?? event.amount) as number | undefined;
          if (amount !== undefined) {
            const isCrit = event.crit === true;
            if (isCrit) {
              onFloatingText(entry.sprite.x, entry.sprite.y, `-${amount}!`, "#ffd700", "20px");
            } else {
              onFloatingText(entry.sprite.x, entry.sprite.y, `-${amount}`, "#ff4444", "16px");
            }
          }
        }
      } else if (HEAL_TYPES.has(type)) {
        const targetId = event.target as string | undefined;
        if (!targetId) continue;
        const entry = getCharacter(targetId);
        if (!entry) continue;

        const color = getTeamColor(entry.data.team);
        if (entry.status === "active" && entry.sprite.alpha < 1) {
          await this.animateRevive(entry.sprite);
        }
        await this.animateHeal(entry.circle, color);
        if (onFloatingText) {
          const amount = (event.amount ?? event.heal) as number | undefined;
          if (amount !== undefined) {
            onFloatingText(entry.sprite.x, entry.sprite.y, `+${amount}`, "#44ff44", "16px");
          }
        }
      } else if (DOT_TYPES.has(type)) {
        const entityId = event.entity as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        const color = getTeamColor(entry.data.team);
        await this.animateDot(entry.circle, color);
        if (onFloatingText) {
          const amount = (event.damage ?? event.amount) as number | undefined;
          if (amount !== undefined) {
            onFloatingText(entry.sprite.x, entry.sprite.y, `-${amount}`, "#ff4444", "14px");
          }
        }
      } else if (HOT_TYPES.has(type)) {
        const entityId = event.entity as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        const color = getTeamColor(entry.data.team);
        await this.animateHeal(entry.circle, color);
        if (onFloatingText) {
          const amount = (event.heal ?? event.amount) as number | undefined;
          if (amount !== undefined) {
            onFloatingText(entry.sprite.x, entry.sprite.y, `+${amount}`, "#44ff44", "14px");
          }
        }
      } else if (type === "knocked_out") {
        const entityId = event.entity as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        await this.animateKnockout(entry.sprite);
      } else if (type === "death") {
        const entityId = event.entity as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        await this.animateDeath(entry.sprite);
      } else if (type === "object_destroyed") {
        const objId = (event.entity ?? event.object) as string | undefined;
        if (!objId) continue;
        const entry = getMapObject(objId);
        if (!entry) continue;

        await this.animateObjectDestroy(entry.sprite);
      }
      // All other event types: no animation, continue immediately
    }
  }
}
