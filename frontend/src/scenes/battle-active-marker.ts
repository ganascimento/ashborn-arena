import Phaser from "phaser";

const RING_RADIUS = 30;
const RING_STROKE = 3;
const ARROW_OFFSET_Y = -40;
const ARROW_FLOAT = 4;
const MARKER_DEPTH = 150;

const TEAM_COLORS: Record<string, number> = {
  player: 0x4488ff,
};
const DEFAULT_COLOR = 0xff4444;

export class BattleActiveMarker {
  private scene: Phaser.Scene;
  private ring: Phaser.GameObjects.Arc | null = null;
  private arrow: Phaser.GameObjects.Triangle | null = null;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  show(worldX: number, worldY: number, team: string) {
    this.hide();

    const color = TEAM_COLORS[team] ?? DEFAULT_COLOR;

    this.ring = this.scene.add.circle(worldX, worldY, RING_RADIUS);
    this.ring.setFillStyle();
    this.ring.setStrokeStyle(RING_STROKE, color);
    this.ring.setDepth(MARKER_DEPTH);

    this.scene.tweens.add({
      targets: this.ring,
      scaleX: 1.15,
      scaleY: 1.15,
      duration: 600,
      yoyo: true,
      loop: -1,
      ease: "Sine.InOut",
    });

    const arrowY = worldY + ARROW_OFFSET_Y;
    this.arrow = this.scene.add.triangle(worldX, arrowY, 0, 0, 16, 0, 8, 10, color);
    this.arrow.setDepth(MARKER_DEPTH);

    this.scene.tweens.add({
      targets: this.arrow,
      y: arrowY - ARROW_FLOAT,
      duration: 800,
      yoyo: true,
      loop: -1,
      ease: "Sine.InOut",
    });
  }

  hide() {
    if (this.ring) {
      this.scene.tweens.killTweensOf(this.ring);
      this.ring.destroy();
      this.ring = null;
    }
    if (this.arrow) {
      this.scene.tweens.killTweensOf(this.arrow);
      this.arrow.destroy();
      this.arrow = null;
    }
  }

  destroy() {
    this.hide();
  }
}
