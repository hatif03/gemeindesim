import { TILE_SIZE } from "../config";

/**
 * On "price_change" event: floating price text rises from a shop location.
 */
export class PriceSpikeEffect {
  private scene: Phaser.Scene;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
  }

  trigger(shopX: number, shopY: number, message: string) {
    // Extract a short price indicator from the message
    const priceMatch = message.match(/(\d+%?)/);
    const label = priceMatch ? `+${priceMatch[1]}` : "+$$$";

    const px = shopX * TILE_SIZE + TILE_SIZE;
    const py = shopY * TILE_SIZE;

    const text = this.scene.add
      .text(px, py, label, {
        fontSize: "8px",
        color: "#ffcc00",
        fontStyle: "bold",
        stroke: "#000000",
        strokeThickness: 2,
      })
      .setOrigin(0.5)
      .setDepth(10);

    // Float upward and fade out
    this.scene.tweens.add({
      targets: text,
      y: py - 28,
      alpha: { from: 1, to: 0 },
      duration: 2500,
      ease: "Sine.easeOut",
      onComplete: () => text.destroy(),
    });
  }
}
