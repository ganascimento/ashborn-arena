import Phaser from "phaser";

class BootScene extends Phaser.Scene {
  constructor() {
    super("boot");
  }

  create() {
    this.add
      .text(400, 300, "Ashborn Arena", {
        fontSize: "32px",
        color: "#ffffff",
      })
      .setOrigin(0.5);
  }
}

new Phaser.Game({
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  backgroundColor: "#1a1a2e",
  scene: [BootScene],
});
