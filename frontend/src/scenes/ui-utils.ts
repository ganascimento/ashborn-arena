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
  drawMountainRange(mtnBack, width, HORIZON_Y, height * 0.28, 4, 17, {
    shadeColor: 0x22223f,
    snowColor: 0x4c4d74,
    snowAlpha: 0.45,
  });

  const mtnFront = scene.add.graphics();
  mtnFront.setDepth(baseDepth + 0.4);
  mtnFront.fillStyle(0x16162e, 1);
  drawMountainRange(mtnFront, width, HORIZON_Y, height * 0.24, 6, 91, {
    shadeColor: 0x101023,
    snowColor: 0x34365f,
    snowAlpha: 0.38,
  });

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

  const forestBack = scene.add.graphics();
  forestBack.setDepth(baseDepth + 0.6);
  drawForestLayer(forestBack, width, RIVER_BOTTOM + PIXEL, PIXEL, {
    foliageColor: 0x1b3b32,
    trunkColor: 0x14271f,
    highlightColor: 0x2d5346,
    treeMinSize: 0,
    treeMaxSize: 1,
    spacing: PIXEL * 2.4,
    seed: 7,
    style: "mixed",
  });
  drawForestLayer(forestBack, width, RIVER_BOTTOM + PIXEL * 9, PIXEL, {
    foliageColor: 0x142c22,
    trunkColor: 0x0d1a14,
    highlightColor: 0x254234,
    treeMinSize: 1,
    treeMaxSize: 2,
    spacing: PIXEL * 3.1,
    seed: 31,
    style: "pine",
  });

  const forestMid = scene.add.graphics();
  forestMid.setDepth(baseDepth + 0.7);
  drawForestLayer(forestMid, width, height * 0.78, PIXEL, {
    foliageColor: 0x0e251a,
    trunkColor: 0x09130f,
    highlightColor: 0x1b3928,
    treeMinSize: 2,
    treeMaxSize: 4,
    spacing: PIXEL * 3.2,
    seed: 13,
    style: "mixed",
  });
  drawForestUnderbrush(forestMid, width, height * 0.79, PIXEL, 0x10271b, 43);

  const forestFront = scene.add.graphics();
  forestFront.setDepth(baseDepth + 0.8);
  drawForestLayer(forestFront, width, height + PIXEL * 3, PIXEL, {
    foliageColor: 0x06120d,
    trunkColor: 0x030807,
    highlightColor: 0x0b2117,
    treeMinSize: 5,
    treeMaxSize: 8,
    spacing: PIXEL * 4.8,
    seed: 23,
    style: "mixed",
  });
  drawForestUnderbrush(forestFront, width, height * 0.91, PIXEL, 0x020806, 71);
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
  details?: {
    shadeColor: number;
    snowColor: number;
    snowAlpha: number;
  },
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
  const tops: number[] = [];
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
    tops[x / pixel] = topYPx;
    if (topYPx < baseY) {
      gfx.fillRect(x, topYPx, pixel, baseY - topYPx);
    }
  }

  if (!details) return;

  for (const peak of peaks) {
    const topX = Math.floor(peak.x / pixel) * pixel;
    const topY = Math.floor((baseY - peak.height) / pixel) * pixel;
    const ridgeLen = Math.max(8, Math.floor(peak.height * 0.42 / pixel));

    gfx.fillStyle(details.snowColor, details.snowAlpha);
    for (let row = 1; row < ridgeLen; row++) {
      const y = topY + row * pixel;
      const leftX = topX - Math.floor(row * 0.55) * pixel;
      if (row % 2 !== 0) {
        gfx.fillRect(leftX, y, pixel, pixel);
      }
      if (row > 3 && row % 4 === 0) {
        gfx.fillRect(leftX - pixel, y, pixel, pixel);
      }
    }

    gfx.fillStyle(details.shadeColor, 0.34);
    for (let row = 3; row < ridgeLen + 8; row++) {
      const y = topY + row * pixel;
      const rightX = topX + Math.floor(row * 0.68) * pixel;
      const widthPx = row % 3 === 0 ? pixel * 2 : pixel;
      gfx.fillRect(rightX, y, widthPx, pixel);
    }
  }
}

interface ForestLayerOpts {
  foliageColor: number;
  trunkColor: number;
  highlightColor: number;
  treeMinSize: number;
  treeMaxSize: number;
  spacing: number;
  seed: number;
  style: "pine" | "mixed";
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
      opts.highlightColor,
      opts.style === "pine" || rand() < 0.55 ? "pine" : "round",
      rand,
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
  highlightColor: number,
  style: "pine" | "round",
  rand: () => number,
) {
  if (style === "round") {
    drawRoundTree(
      gfx,
      baseX,
      baseY,
      sizeMul,
      pixel,
      foliageColor,
      trunkColor,
      highlightColor,
      rand,
    );
    return;
  }

  const trunkH = pixel * Math.max(2, sizeMul + 1);
  const foliageRows = 5 + sizeMul * 2;
  const foliageMaxHalf = 1.5 + sizeMul;
  const trunkW = sizeMul >= 4 ? pixel * 2 : pixel;
  const topY = baseY - trunkH - foliageRows * pixel;

  gfx.fillStyle(trunkColor, 1);
  gfx.fillRect(baseX - trunkW / 2, baseY - trunkH, trunkW, trunkH);
  if (sizeMul >= 3) {
    gfx.fillStyle(0x0a100c, 0.5);
    gfx.fillRect(baseX - trunkW / 2, baseY - trunkH, pixel / 2, trunkH);
  }

  gfx.fillStyle(foliageColor, 1);
  for (let i = 0; i < foliageRows; i++) {
    const t = i / Math.max(1, foliageRows - 1);
    const wave = i % 3 === 1 ? 1 : 0;
    const half = Math.max(1, Math.round(t * foliageMaxHalf) + wave);
    const y = baseY - trunkH - (i + 1) * pixel;
    const leftNib = rand() < 0.25 ? pixel : 0;
    const rightNib = rand() < 0.25 ? pixel : 0;
    gfx.fillRect(
      baseX - half * pixel + leftNib,
      y,
      half * 2 * pixel - leftNib - rightNib,
      pixel,
    );
  }

  gfx.fillStyle(highlightColor, 0.65);
  for (let i = 2; i < foliageRows - 1; i += 4) {
    const t = i / Math.max(1, foliageRows - 1);
    const half = Math.max(1, Math.round(t * foliageMaxHalf));
    const y = baseY - trunkH - (i + 1) * pixel;
    gfx.fillRect(baseX - half * pixel, y, pixel, pixel);
    if (sizeMul > 2) {
      gfx.fillRect(baseX + (half - 1) * pixel, y + pixel, pixel, pixel);
    }
  }

  gfx.fillStyle(foliageColor, 1);
  gfx.fillRect(baseX - pixel / 2, topY - pixel, pixel, pixel);
}

function drawRoundTree(
  gfx: Phaser.GameObjects.Graphics,
  baseX: number,
  baseY: number,
  sizeMul: number,
  pixel: number,
  foliageColor: number,
  trunkColor: number,
  highlightColor: number,
  rand: () => number,
) {
  const trunkH = pixel * Math.max(2, sizeMul + 1);
  const trunkW = sizeMul >= 4 ? pixel * 2 : pixel;
  const radius = Math.max(2, sizeMul + 2);
  const canopyY = baseY - trunkH - radius * pixel * 0.45;

  gfx.fillStyle(trunkColor, 1);
  gfx.fillRect(baseX - trunkW / 2, baseY - trunkH, trunkW, trunkH);

  gfx.fillStyle(foliageColor, 1);
  for (let row = -radius; row <= radius; row++) {
    const rowAbs = Math.abs(row);
    const half =
      Math.max(1, Math.round((radius - rowAbs * 0.62) * (0.75 + rand() * 0.18)));
    const y = Math.floor((canopyY + row * pixel) / pixel) * pixel;
    const wobble = Math.floor((rand() - 0.5) * pixel * 1.2);
    gfx.fillRect(baseX + wobble - half * pixel, y, half * 2 * pixel, pixel);
  }

  gfx.fillStyle(highlightColor, 0.55);
  gfx.fillRect(baseX - radius * pixel * 0.55, canopyY - pixel, pixel * 2, pixel);
  if (sizeMul > 2) {
    gfx.fillRect(baseX + pixel, canopyY + pixel, pixel * 2, pixel);
  }
}

function drawForestUnderbrush(
  gfx: Phaser.GameObjects.Graphics,
  width: number,
  baseY: number,
  pixel: number,
  color: number,
  seed: number,
) {
  let s = seed;
  const rand = () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };

  gfx.fillStyle(color, 1);
  for (let x = -pixel; x < width + pixel; x += pixel * 2) {
    const h = pixel * (1 + Math.floor(rand() * 5));
    const w = pixel * (1 + Math.floor(rand() * 2));
    const y = Math.floor((baseY - h + rand() * pixel * 2) / pixel) * pixel;
    gfx.fillRect(x, y, w, h);
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

  const forestTop = height * 0.72;
  const forestBottom = height * 0.88;

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
