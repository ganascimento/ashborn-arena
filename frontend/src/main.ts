import Phaser from "phaser";
import MenuScene from "./scenes/MenuScene";
import PreparationScene from "./scenes/PreparationScene";
import BattleScene from "./scenes/BattleScene";
import ResultScene from "./scenes/ResultScene";

new Phaser.Game({
  type: Phaser.AUTO,
  backgroundColor: "#1a1a2e",
  pixelArt: true,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    width: 1280,
    height: 720,
  },
  scene: [MenuScene, PreparationScene, BattleScene, ResultScene],
});
