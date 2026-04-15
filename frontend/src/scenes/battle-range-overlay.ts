export class BattleRangeOverlay {
  private scene: Phaser.Scene;
  private tileSize: number;
  private gridOffsetX: number;
  private gridOffsetY: number;
  private gridCols: number;
  private gridRows: number;
  private rangeOverlays: Phaser.GameObjects.Rectangle[] = [];
  private aoeOverlays: Phaser.GameObjects.Rectangle[] = [];

  constructor(
    scene: Phaser.Scene,
    tileSize: number,
    gridOffsetX: number,
    gridOffsetY: number,
    gridCols: number,
    gridRows: number,
  ) {
    this.scene = scene;
    this.tileSize = tileSize;
    this.gridOffsetX = gridOffsetX;
    this.gridOffsetY = gridOffsetY;
    this.gridCols = gridCols;
    this.gridRows = gridRows;
  }

  showRange(centerX: number, centerY: number, maxRange: number) {
    this.clearRange();

    for (let tx = 0; tx < this.gridCols; tx++) {
      for (let ty = 0; ty < this.gridRows; ty++) {
        const dist = Math.max(Math.abs(tx - centerX), Math.abs(ty - centerY));
        if (dist <= maxRange && dist > 0) {
          const { px, py } = this.gridToPixel(tx, ty);
          const rect = this.scene.add.rectangle(
            px,
            py,
            this.tileSize,
            this.tileSize,
            0x4488ff,
            0.25,
          );
          rect.setDepth(50);
          this.rangeOverlays.push(rect);
        }
      }
    }
  }

  showAdjacentRange(centerX: number, centerY: number) {
    this.showRange(centerX, centerY, 1);
  }

  clearRange() {
    for (const rect of this.rangeOverlays) {
      rect.destroy();
    }
    this.rangeOverlays = [];
  }

  showAoePreview(centerX: number, centerY: number) {
    this.clearAoePreview();

    for (let dx = -1; dx <= 1; dx++) {
      for (let dy = -1; dy <= 1; dy++) {
        const tx = centerX + dx;
        const ty = centerY + dy;
        if (tx >= 0 && tx < this.gridCols && ty >= 0 && ty < this.gridRows) {
          const { px, py } = this.gridToPixel(tx, ty);
          const rect = this.scene.add.rectangle(
            px,
            py,
            this.tileSize,
            this.tileSize,
            0xff8800,
            0.3,
          );
          rect.setDepth(51);
          this.aoeOverlays.push(rect);
        }
      }
    }
  }

  clearAoePreview() {
    for (const rect of this.aoeOverlays) {
      rect.destroy();
    }
    this.aoeOverlays = [];
  }

  clear() {
    this.clearRange();
    this.clearAoePreview();
  }

  destroy() {
    this.clear();
  }

  private gridToPixel(gx: number, gy: number): { px: number; py: number } {
    const px = this.gridOffsetX + gx * this.tileSize + this.tileSize / 2;
    const py = this.gridOffsetY + gy * this.tileSize + this.tileSize / 2;
    return { px, py };
  }
}
