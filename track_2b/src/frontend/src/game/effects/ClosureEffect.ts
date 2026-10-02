import { TILE_SIZE } from "../config";

/**
 * On "closure" event: darken a shop tile and show a "CLOSED" overlay.
 */
export class ClosureEffect {
  private scene: Phaser.Scene;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  trigger(shopX: number, shopY: number) {
    // Dark overlay on the shop building (3 wide x 2 tall)
    const overlay = this.scene.add.rectangle(
      shopX * TILE_SIZE + (TILE_SIZE * 3) / 2,
      shopY * TILE_SIZE + TILE_SIZE,
      TILE_SIZE * 3,
      TILE_SIZE * 2,
      0x000000,
      0,
    );
    overlay.setDepth(3);

    // Fade in darkness
    this.scene.tweens.add({
      targets: overlay,
      alpha: { from: 0, to: 0.5 },
      duration: 1000,
      ease: "Sine.easeIn",
    });

    // "CLOSED" text
    const closedText = this.scene.add
      .text(
        shopX * TILE_SIZE + (TILE_SIZE * 3) / 2,
        shopY * TILE_SIZE + TILE_SIZE,
        "CLOSED",
        {
          fontSize: "7px",
          color: "#ff6666",
          fontStyle: "bold",
          stroke: "#000000",
          strokeThickness: 2,
        },
      )
      .setOrigin(0.5)
      .setDepth(4)
      .setAlpha(0);

    this.scene.tweens.add({
      targets: closedText,
      alpha: 1,
      delay: 500,
      duration: 500,
    });
  }
}
