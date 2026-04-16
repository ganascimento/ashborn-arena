import Phaser from "phaser";

export function createParticleTexture(
  scene: Phaser.Scene,
  key: string,
  radius: number,
  color: number,
) {
  if (scene.textures.exists(key)) return;
  const gfx = scene.add.graphics();
  gfx.fillStyle(color, 1);
  gfx.fillCircle(radius, radius, radius);
  gfx.generateTexture(key, radius * 2, radius * 2);
  gfx.destroy();
}

export function drawPanel(
  scene: Phaser.Scene,
  x: number,
  y: number,
  w: number,
  h: number,
  opts: {
    fill?: number;
    fillAlpha?: number;
    border?: number;
    borderAlpha?: number;
    borderWidth?: number;
    radius?: number;
    depth?: number;
  } = {},
): Phaser.GameObjects.Graphics {
  const fill = opts.fill ?? 0x16162a;
  const fillAlpha = opts.fillAlpha ?? 0.9;
  const border = opts.border ?? 0x333366;
  const borderAlpha = opts.borderAlpha ?? 0.8;
  const borderWidth = opts.borderWidth ?? 1;
  const radius = opts.radius ?? 8;
  const depth = opts.depth ?? 0;

  const gfx = scene.add.graphics();
  gfx.setDepth(depth);
  gfx.fillStyle(fill, fillAlpha);
  gfx.fillRoundedRect(x, y, w, h, radius);
  if (borderWidth > 0) {
    gfx.lineStyle(borderWidth, border, borderAlpha);
    gfx.strokeRoundedRect(x, y, w, h, radius);
  }
  return gfx;
}
