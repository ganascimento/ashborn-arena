import Phaser from "phaser";

interface CharacterEntry {
  data: {
    class_id: string;
    team: string;
    position: { x: number; y: number };
    current_hp: number;
    max_hp: number;
  };
  sprite: Phaser.GameObjects.Container;
  circle: Phaser.GameObjects.Arc;
  body: Phaser.GameObjects.Sprite;
  status: "active" | "knocked_out" | "dead";
}

interface MapObjectEntry {
  data: {
    position: { x: number; y: number };
    hp: number | null;
    max_hp: number | null;
  };
  sprite: Phaser.GameObjects.Rectangle | Phaser.GameObjects.Image;
  canopy?: Phaser.GameObjects.Image;
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

function distance(
  a: Phaser.GameObjects.Container,
  b: Phaser.GameObjects.Container,
) {
  return Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
}

export class BattleAnimations {
  private scene: Phaser.Scene;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  private tweenPromise(
    config: Phaser.Types.Tweens.TweenBuilderConfig,
  ): Promise<void> {
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

  async animateMove(
    container: Phaser.GameObjects.Container,
    toPx: number,
    toPy: number,
  ): Promise<void> {
    await this.tweenPromise({
      targets: container,
      x: toPx,
      y: toPy,
      duration: 300,
      ease: "Quad.InOut",
    });
  }

  private restoreBodyTint(entry: CharacterEntry): void {
    if (entry.data.team === "player") {
      entry.body.clearTint();
    } else {
      entry.body.setTint(0xffdddd);
    }
  }

  async animateDamage(entry: CharacterEntry): Promise<void> {
    const originalColor = getTeamColor(entry.data.team);
    entry.circle.setFillStyle(0xff4444, 0.55);
    entry.body.setTint(0xff7777);
    await this.tweenPromise({
      targets: entry.sprite,
      x: entry.sprite.x + 3,
      yoyo: true,
      repeat: 2,
      duration: 45,
      ease: "Sine.InOut",
    });
    entry.circle.setFillStyle(originalColor, 0.28);
    this.restoreBodyTint(entry);
  }

  async animateHeal(entry: CharacterEntry): Promise<void> {
    const originalColor = getTeamColor(entry.data.team);
    entry.circle.setFillStyle(0x44ff88, 0.5);
    entry.body.setTint(0xa8ffd0);
    await this.delay(200);
    entry.circle.setFillStyle(originalColor, 0.28);
    this.restoreBodyTint(entry);
  }

  async animateDot(entry: CharacterEntry): Promise<void> {
    const originalColor = getTeamColor(entry.data.team);
    entry.circle.setFillStyle(0xcc4444, 0.48);
    entry.body.setTint(0xcc5555);
    await this.delay(150);
    entry.circle.setFillStyle(originalColor, 0.28);
    this.restoreBodyTint(entry);
  }

  async animateKnockout(
    container: Phaser.GameObjects.Container,
  ): Promise<void> {
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

  async animateObjectHit(
    sprite: Phaser.GameObjects.Rectangle | Phaser.GameObjects.Image,
  ): Promise<void> {
    if (sprite instanceof Phaser.GameObjects.Image) {
      sprite.setTint(0xff4444);
      await this.delay(200);
      sprite.clearTint();
    } else {
      const orig = sprite.fillColor;
      sprite.setFillStyle(0xff4444);
      await this.delay(200);
      sprite.setFillStyle(orig);
    }
  }

  async animateObjectDestroy(
    sprite: Phaser.GameObjects.Rectangle | Phaser.GameObjects.Image,
    canopy?: Phaser.GameObjects.Image,
  ): Promise<void> {
    const targets = canopy ? [sprite, canopy] : sprite;
    await this.tweenPromise({
      targets,
      alpha: 0,
      duration: 200,
    });
    sprite.destroy();
    canopy?.destroy();
  }

  private effectDepthNear(target: Phaser.GameObjects.Container): number {
    return Math.max(20, target.depth + 2);
  }

  private async animatePhysicalStrike(
    attacker: CharacterEntry | undefined,
    target: CharacterEntry,
  ): Promise<void> {
    if (attacker) {
      const dx = target.sprite.x - attacker.sprite.x;
      const dy = target.sprite.y - attacker.sprite.y;
      const mag = Math.max(1, Math.hypot(dx, dy));
      await this.tweenPromise({
        targets: attacker.sprite,
        x: attacker.sprite.x + (dx / mag) * 10,
        y: attacker.sprite.y + (dy / mag) * 10,
        yoyo: true,
        duration: 80,
        ease: "Quad.Out",
      });
    }

    const slash = this.scene.add.graphics();
    slash.setDepth(this.effectDepthNear(target.sprite));
    slash.lineStyle(5, 0xfff1b8, 0.95);
    slash.beginPath();
    slash.arc(target.sprite.x, target.sprite.y - 4, 26, -0.65, 1.15);
    slash.strokePath();
    slash.lineStyle(2, 0xff7640, 0.85);
    slash.beginPath();
    slash.arc(target.sprite.x + 1, target.sprite.y - 4, 19, -0.55, 1.0);
    slash.strokePath();
    await this.tweenPromise({
      targets: slash,
      alpha: 0,
      scale: 1.3,
      duration: 180,
      ease: "Quad.Out",
    });
    slash.destroy();
  }

  private async animateProjectile(
    attacker: CharacterEntry,
    target: CharacterEntry,
    color: number,
    trailColor: number,
  ): Promise<void> {
    const line = this.scene.add.graphics();
    line.setDepth(this.effectDepthNear(target.sprite) - 1);
    line.lineStyle(2, trailColor, 0.35);
    line.lineBetween(
      attacker.sprite.x,
      attacker.sprite.y - 8,
      target.sprite.x,
      target.sprite.y - 8,
    );

    const bolt = this.scene.add.circle(
      attacker.sprite.x,
      attacker.sprite.y - 10,
      5,
      color,
      1,
    );
    bolt.setDepth(this.effectDepthNear(target.sprite));
    await this.tweenPromise({
      targets: bolt,
      x: target.sprite.x,
      y: target.sprite.y - 10,
      duration: 180,
      ease: "Quad.In",
    });
    line.destroy();
    bolt.destroy();

    const impact = this.scene.add.circle(
      target.sprite.x,
      target.sprite.y - 8,
      8,
      color,
      0.85,
    );
    impact.setDepth(this.effectDepthNear(target.sprite));
    await this.tweenPromise({
      targets: impact,
      alpha: 0,
      scale: 2.2,
      duration: 180,
      ease: "Quad.Out",
    });
    impact.destroy();
  }

  private async animateArrowShot(
    attacker: CharacterEntry,
    target: CharacterEntry,
  ): Promise<void> {
    const arrow = this.scene.add.rectangle(
      attacker.sprite.x,
      attacker.sprite.y - 8,
      22,
      3,
      0xe7d7a3,
      1,
    );
    arrow.setDepth(this.effectDepthNear(target.sprite));
    arrow.rotation = Phaser.Math.Angle.Between(
      attacker.sprite.x,
      attacker.sprite.y,
      target.sprite.x,
      target.sprite.y,
    );
    await this.tweenPromise({
      targets: arrow,
      x: target.sprite.x,
      y: target.sprite.y - 8,
      duration: 160,
      ease: "Quad.In",
    });
    arrow.destroy();
    await this.animatePhysicalStrike(undefined, target);
  }

  private async animateHealEffect(
    target: CharacterEntry,
    source?: CharacterEntry,
  ): Promise<void> {
    if (source && source !== target) {
      await this.animateProjectile(source, target, 0x77ffba, 0x77ffba);
    }

    const ring = this.scene.add.circle(
      target.sprite.x,
      target.sprite.y - 3,
      12,
      0x76ff9a,
      0.35,
    );
    ring.setDepth(this.effectDepthNear(target.sprite));
    ring.setStrokeStyle(3, 0xd8ffbf, 0.9);
    const plus = this.scene.add.text(
      target.sprite.x,
      target.sprite.y - 30,
      "+",
      {
        fontSize: "22px",
        color: "#d8ffbf",
        fontFamily: "monospace",
        fontStyle: "bold",
      },
    );
    plus.setOrigin(0.5);
    plus.setDepth(this.effectDepthNear(target.sprite) + 1);

    await Promise.all([
      this.tweenPromise({
        targets: ring,
        alpha: 0,
        scale: 2.1,
        duration: 260,
        ease: "Quad.Out",
      }),
      this.tweenPromise({
        targets: plus,
        y: plus.y - 16,
        alpha: 0,
        duration: 300,
        ease: "Quad.Out",
      }),
    ]);
    ring.destroy();
    plus.destroy();
  }

  private inferDamageFx(
    event: Record<string, unknown>,
    attacker: CharacterEntry | undefined,
    target: CharacterEntry,
  ): "physical" | "magic" | "ranged" {
    const type = event.type as string | undefined;
    const ability = String(event.ability ?? "");
    const attackerClass = attacker?.data.class_id ?? "";
    const isFar = attacker
      ? distance(attacker.sprite, target.sprite) > 72
      : false;

    if (
      type === "chain_primary" ||
      type === "chain_secondary" ||
      attackerClass === "mage" ||
      ability.includes("chama") ||
      ability.includes("arcana") ||
      ability.includes("raio") ||
      ability.includes("gelo") ||
      ability.includes("veneno")
    ) {
      return "magic";
    }
    if (attackerClass === "archer" || ability.includes("tiro") || isFar) {
      return "ranged";
    }
    return "physical";
  }

  private async animateDamageEffect(
    event: Record<string, unknown>,
    attacker: CharacterEntry | undefined,
    target: CharacterEntry,
  ): Promise<void> {
    const fx = this.inferDamageFx(event, attacker, target);
    if (fx === "magic" && attacker) {
      await this.animateProjectile(attacker, target, 0x90d7ff, 0x6b66ff);
    } else if (fx === "ranged" && attacker) {
      await this.animateArrowShot(attacker, target);
    } else {
      await this.animatePhysicalStrike(attacker, target);
    }
  }

  async processEventsAnimated(
    events: unknown[],
    getCharacter: (id: string) => CharacterEntry | undefined,
    getMapObject: (id: string) => MapObjectEntry | undefined,
    gridToPixel: (x: number, y: number) => { px: number; py: number },
    updateState: (event: Record<string, unknown>) => void,
    onFloatingText?: (
      worldX: number,
      worldY: number,
      text: string,
      color: string,
      fontSize: string,
    ) => void,
  ): Promise<void> {
    if (!events || events.length === 0) return;

    for (const raw of events) {
      const event = raw as Record<string, unknown>;
      const type = event.type as string | undefined;
      if (!type) continue;

      updateState(event);

      if (MOVE_TYPES.has(type)) {
        const entityId = (event.entity ?? event.character) as
          | string
          | undefined;
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

        const attackerId = event.attacker as string | undefined;
        const attacker = attackerId ? getCharacter(attackerId) : undefined;
        await this.animateDamageEffect(event, attacker, entry);
        await this.animateDamage(entry);
        if (onFloatingText) {
          const amount = (event.damage ?? event.amount) as number | undefined;
          if (amount !== undefined) {
            const isCrit = event.crit === true;
            if (isCrit) {
              onFloatingText(
                entry.sprite.x,
                entry.sprite.y,
                `-${amount}!`,
                "#ffd700",
                "20px",
              );
            } else {
              onFloatingText(
                entry.sprite.x,
                entry.sprite.y,
                `-${amount}`,
                "#ff4444",
                "16px",
              );
            }
          }
        }
      } else if (HEAL_TYPES.has(type)) {
        const targetId = (event.target ?? event.entity) as string | undefined;
        if (!targetId) continue;
        const entry = getCharacter(targetId);
        if (!entry) continue;

        const healerId = (event.healer ?? event.entity) as string | undefined;
        const healer = healerId ? getCharacter(healerId) : undefined;
        if (entry.status === "active" && entry.sprite.alpha < 1) {
          await this.animateRevive(entry.sprite);
        }
        await this.animateHealEffect(entry, healer);
        await this.animateHeal(entry);
        if (onFloatingText) {
          const amount = (event.amount ?? event.heal) as number | undefined;
          if (amount !== undefined) {
            onFloatingText(
              entry.sprite.x,
              entry.sprite.y,
              `+${amount}`,
              "#44ff44",
              "16px",
            );
          }
        }
      } else if (DOT_TYPES.has(type)) {
        const entityId = event.entity as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        await this.animateDot(entry);
        if (onFloatingText) {
          const amount = (event.damage ?? event.amount) as number | undefined;
          if (amount !== undefined) {
            onFloatingText(
              entry.sprite.x,
              entry.sprite.y,
              `-${amount}`,
              "#ff4444",
              "14px",
            );
          }
        }
      } else if (HOT_TYPES.has(type)) {
        const entityId = event.entity as string | undefined;
        if (!entityId) continue;
        const entry = getCharacter(entityId);
        if (!entry) continue;

        await this.animateHealEffect(entry);
        await this.animateHeal(entry);
        if (onFloatingText) {
          const amount = (event.heal ?? event.amount) as number | undefined;
          if (amount !== undefined) {
            onFloatingText(
              entry.sprite.x,
              entry.sprite.y,
              `+${amount}`,
              "#44ff44",
              "14px",
            );
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
      } else if (type === "object_hit") {
        const objId = event.object as string | undefined;
        if (!objId) continue;
        const entry = getMapObject(objId);
        if (!entry) continue;

        const pos = event.position as { x: number; y: number } | undefined;
        const pixelPos = pos ? gridToPixel(pos.x, pos.y) : null;

        await this.animateObjectHit(entry.sprite);

        if (onFloatingText && pixelPos) {
          const damage = event.damage as number | undefined;
          if (damage !== undefined) {
            onFloatingText(
              pixelPos.px,
              pixelPos.py,
              `-${damage}`,
              "#ff8844",
              "14px",
            );
          }
        }

        const destroyed = event.destroyed as boolean | undefined;
        if (destroyed) {
          await this.animateObjectDestroy(entry.sprite, entry.canopy);
        }
      } else if (type === "object_destroyed") {
        const objId = (event.entity ?? event.object) as string | undefined;
        if (!objId) continue;
        const entry = getMapObject(objId);
        if (!entry) continue;

        await this.animateObjectDestroy(entry.sprite, entry.canopy);
      }
      // All other event types: no animation, continue immediately
    }
  }
}
