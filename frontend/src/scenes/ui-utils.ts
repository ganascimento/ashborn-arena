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

export function createNightLandscape(
  scene: Phaser.Scene,
  width: number,
  height: number,
  baseDepth = -3,
) {
  const PIXEL = 4;

  const HORIZON_Y = height * 0.55;
  const RIVER_TOP = HORIZON_Y;
  const RIVER_BOTTOM = height * 0.68;

  const sky = scene.add.graphics();
  sky.setDepth(baseDepth);
  for (let y = 0; y < HORIZON_Y; y += PIXEL) {
    const t = y / HORIZON_Y;
    const r = Math.floor(8 + t * 14);
    const g = Math.floor(8 + t * 10);
    const b = Math.floor(28 + t * 18);
    sky.fillStyle((r << 16) | (g << 8) | b, 1);
    sky.fillRect(0, y, width, PIXEL);
  }

  for (let i = 0; i < 90; i++) {
    const sx = Math.floor((Math.random() * width) / PIXEL) * PIXEL;
    const sy = Math.floor((Math.random() * HORIZON_Y * 0.9) / PIXEL) * PIXEL;
    const size = Math.random() < 0.15 ? PIXEL * 2 : PIXEL;
    const star = scene.add.rectangle(sx, sy, size, size, 0xffffff, 0.7);
    star.setDepth(baseDepth + 0.1);
    scene.tweens.add({
      targets: star,
      alpha: { from: 0.15, to: 0.9 },
      duration: 1200 + Math.random() * 2400,
      yoyo: true,
      repeat: -1,
      delay: Math.random() * 3000,
    });
  }

  const moonR = 44;
  const moonCx = Math.floor((width * 0.82) / PIXEL) * PIXEL;
  const moonCy = Math.floor((height * 0.18) / PIXEL) * PIXEL;
  const moon = scene.add.graphics();
  moon.setDepth(baseDepth + 0.2);
  moon.fillStyle(0xfff4c4, 0.05);
  moon.fillCircle(moonCx, moonCy, moonR * 2);
  moon.fillStyle(0xfff4c4, 0.1);
  moon.fillCircle(moonCx, moonCy, moonR * 1.4);
  moon.fillStyle(0xfff4c4, 0.95);
  drawPixelDisk(moon, moonCx, moonCy, moonR, PIXEL);
  moon.fillStyle(0x10101e, 1);
  drawPixelDisk(moon, moonCx + 22, moonCy - 8, moonR - 2, PIXEL);
  moon.fillStyle(0xfff4c4, 1);
  moon.fillRect(moonCx - 5 * PIXEL, moonCy - 3 * PIXEL, PIXEL, PIXEL);
  moon.fillRect(moonCx - 8 * PIXEL, moonCy + 4 * PIXEL, PIXEL, PIXEL);
  moon.fillRect(moonCx - 4 * PIXEL, moonCy + 7 * PIXEL, PIXEL, PIXEL);

  const mtnBack = scene.add.graphics();
  mtnBack.setDepth(baseDepth + 0.3);
  mtnBack.fillStyle(0x2a2a4c, 1);
  drawMountainRange(mtnBack, width, HORIZON_Y, height * 0.26, 3, 17);

  const mtnFront = scene.add.graphics();
  mtnFront.setDepth(baseDepth + 0.4);
  mtnFront.fillStyle(0x16162e, 1);
  drawMountainRange(mtnFront, width, HORIZON_Y, height * 0.22, 5, 91);

  createRiver(
    scene,
    RIVER_TOP,
    width,
    RIVER_BOTTOM - RIVER_TOP,
    baseDepth + 0.5,
  );

  const ground = scene.add.graphics();
  ground.setDepth(baseDepth + 0.55);
  for (let y = RIVER_BOTTOM; y < height; y += PIXEL) {
    const t = (y - RIVER_BOTTOM) / (height - RIVER_BOTTOM);
    const r = Math.floor(12 - t * 8);
    const g = Math.floor(24 - t * 16);
    const b = Math.floor(20 - t * 14);
    ground.fillStyle((r << 16) | (g << 8) | b, 1);
    ground.fillRect(0, y, width, PIXEL);
  }

  const forest = scene.add.graphics();
  forest.setDepth(baseDepth + 0.6);
  drawForestLayer(forest, width, RIVER_BOTTOM + PIXEL, PIXEL, {
    foliageColor: 0x18302a,
    trunkColor: 0x18302a,
    treeMinSize: 0,
    treeMaxSize: 1,
    spacing: PIXEL * 3,
    seed: 7,
  });
  drawForestLayer(forest, width, height * 0.82, PIXEL, {
    foliageColor: 0x0c1e16,
    trunkColor: 0x0a1410,
    treeMinSize: 1,
    treeMaxSize: 3,
    spacing: PIXEL * 4,
    seed: 13,
  });
  drawForestLayer(forest, width, height + PIXEL * 4, PIXEL, {
    foliageColor: 0x081410,
    trunkColor: 0x05080a,
    treeMinSize: 4,
    treeMaxSize: 7,
    spacing: PIXEL * 7,
    seed: 23,
  });
}

function drawPixelDisk(
  gfx: Phaser.GameObjects.Graphics,
  cx: number,
  cy: number,
  r: number,
  pixel: number,
) {
  const r2 = r * r;
  for (let py = -r; py <= r; py += pixel) {
    for (let px = -r; px <= r; px += pixel) {
      if (px * px + py * py <= r2) {
        gfx.fillRect(cx + px, cy + py, pixel, pixel);
      }
    }
  }
}

function drawMountainRange(
  gfx: Phaser.GameObjects.Graphics,
  width: number,
  baseY: number,
  maxHeight: number,
  peakCount: number,
  seed: number,
) {
  let s = seed;
  const rand = () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };

  const peaks: Array<{ x: number; height: number; halfWidth: number }> = [];
  const slot = width / peakCount;
  for (let i = 0; i < peakCount; i++) {
    peaks.push({
      x: (i + 0.5) * slot + (rand() - 0.5) * slot * 0.6,
      height: maxHeight * (0.55 + rand() * 0.45),
      halfWidth: slot * (0.7 + rand() * 0.5),
    });
  }

  const pixel = 4;
  for (let x = 0; x < width; x += pixel) {
    let topY = baseY;
    for (const peak of peaks) {
      const dx = Math.abs(x - peak.x);
      if (dx < peak.halfWidth) {
        const t = dx / peak.halfWidth;
        const falloff = 0.5 * (1 + Math.cos(Math.PI * t));
        const peakY = baseY - peak.height * falloff;
        if (peakY < topY) topY = peakY;
      }
    }
    const topYPx = Math.floor(topY / pixel) * pixel;
    if (topYPx < baseY) {
      gfx.fillRect(x, topYPx, pixel, baseY - topYPx);
    }
  }
}

interface ForestLayerOpts {
  foliageColor: number;
  trunkColor: number;
  treeMinSize: number;
  treeMaxSize: number;
  spacing: number;
  seed: number;
}

function drawForestLayer(
  gfx: Phaser.GameObjects.Graphics,
  width: number,
  baseY: number,
  pixel: number,
  opts: ForestLayerOpts,
) {
  let s = opts.seed;
  const rand = () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };

  for (let x = -opts.spacing; x < width + opts.spacing; x += opts.spacing) {
    const xJitter = Math.floor((rand() - 0.5) * opts.spacing * 0.6);
    const treeX = x + xJitter;
    const sizeRange = opts.treeMaxSize - opts.treeMinSize + 1;
    const sizeMul = opts.treeMinSize + Math.floor(rand() * sizeRange);
    const yJitter = Math.floor(rand() * pixel * 2);
    drawTree(
      gfx,
      treeX,
      baseY - yJitter,
      sizeMul,
      pixel,
      opts.foliageColor,
      opts.trunkColor,
    );
  }
}

function drawTree(
  gfx: Phaser.GameObjects.Graphics,
  baseX: number,
  baseY: number,
  sizeMul: number,
  pixel: number,
  foliageColor: number,
  trunkColor: number,
) {
  const trunkH = pixel * Math.max(1, sizeMul);
  const foliageRows = 4 + sizeMul * 2;
  const foliageMaxHalf = 1 + sizeMul;
  const trunkW = sizeMul >= 4 ? pixel * 2 : pixel;

  gfx.fillStyle(trunkColor, 1);
  gfx.fillRect(baseX - trunkW / 2, baseY - trunkH, trunkW, trunkH);

  gfx.fillStyle(foliageColor, 1);
  for (let i = 0; i < foliageRows; i++) {
    const t = (foliageRows - 1 - i) / Math.max(1, foliageRows - 1);
    const half = Math.max(1, Math.round(t * foliageMaxHalf));
    const y = baseY - trunkH - (i + 1) * pixel;
    gfx.fillRect(baseX - half * pixel, y, half * 2 * pixel, pixel);
  }
}

function createRiver(
  scene: Phaser.Scene,
  y: number,
  width: number,
  height: number,
  depth: number,
) {
  const key = "ashborn_river_tile";
  const tw = 64;
  const th = 16;

  if (!scene.textures.exists(key)) {
    const gfx = scene.add.graphics();
    gfx.fillStyle(0x0a1a2e, 1);
    gfx.fillRect(0, 0, tw, th);
    gfx.fillStyle(0x142e48, 1);
    gfx.fillRect(0, 0, tw, 2);
    gfx.fillStyle(0x2a4868, 0.85);
    gfx.fillRect(8, 4, 12, 2);
    gfx.fillRect(34, 8, 8, 2);
    gfx.fillRect(50, 2, 6, 2);
    gfx.fillRect(2, 12, 10, 2);
    gfx.fillStyle(0x4a6a88, 0.6);
    gfx.fillRect(20, 6, 4, 2);
    gfx.fillRect(42, 10, 4, 2);
    gfx.generateTexture(key, tw, th);
    gfx.destroy();
  }

  const river = scene.add.tileSprite(0, y, width, height, key);
  river.setOrigin(0, 0);
  river.setDepth(depth);

  scene.tweens.add({
    targets: river,
    tilePositionX: -tw,
    duration: 7000,
    repeat: -1,
    ease: "Linear",
  });
}

export function createForestParticles(
  scene: Phaser.Scene,
  width: number,
  height: number,
) {
  const key = "ashborn_firefly";
  if (!scene.textures.exists(key)) {
    const gfx = scene.add.graphics();
    gfx.fillStyle(0xffeb70, 1);
    gfx.fillRect(0, 0, 3, 3);
    gfx.generateTexture(key, 3, 3);
    gfx.destroy();
  }

  const forestTop = height * 0.66;
  const forestBottom = height * 0.78;

  const emitter = scene.add.particles(0, 0, key, {
    x: { min: 0, max: width },
    y: { min: forestTop, max: forestBottom },
    alpha: { start: 0.85, end: 0 },
    scale: { min: 0.5, max: 1.4 },
    speed: { min: 6, max: 18 },
    angle: { min: 250, max: 290 },
    lifespan: { min: 3500, max: 7000 },
    frequency: 220,
    blendMode: "ADD",
  });
  emitter.setDepth(-2);
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
