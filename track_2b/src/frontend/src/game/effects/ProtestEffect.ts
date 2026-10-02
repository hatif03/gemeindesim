import { TILE_SIZE } from "../config";
import type { NPCManager } from "../systems/NPCManager";

/**
 * On "protest" event: affected NPCs walk toward the government building,
 * clustering in a small area in front of it.
 */
export class ProtestEffect {
  private scene: Phaser.Scene;
  private npcManager: NPCManager;

  constructor(scene: Phaser.Scene, npcManager: NPCManager) {
    this.scene = scene;
    this.npcManager = npcManager;
  }

  trigger(affectedNpcIds: string[]) {
    const gov = this.npcManager.getBuildings().government;
    // Cluster NPCs in front of the government building (below it)
    const baseRow = gov.y + 3;
    const baseCol = gov.x;

    for (let i = 0; i < affectedNpcIds.length; i++) {
      const id = affectedNpcIds[i];
      // Spread NPCs in a small area around the rally point
      const offsetCol = (i % 4) - 1;
      const offsetRow = Math.floor(i / 4);
      const targetCol = baseCol + offsetCol;
      const targetRow = baseRow + offsetRow;

      this.npcManager.sendTo(id, targetCol, targetRow);
    }

    // Add a floating protest sign text
    const px = (gov.x + 1) * TILE_SIZE;
    const py = (gov.y + 3) * TILE_SIZE;
    const sign = this.scene.add
      .text(px, py - 12, "PROTEST!", {
        fontSize: "8px",
        color: "#ff4444",
        fontStyle: "bold",
        stroke: "#000000",
        strokeThickness: 2,
      })
      .setDepth(10)
      .setOrigin(0.5);

    // Animate sign bobbing, then fade out
    this.scene.tweens.add({
      targets: sign,
      y: py - 24,
      alpha: { from: 1, to: 0 },
      duration: 4000,
      ease: "Sine.easeOut",
      onComplete: () => sign.destroy(),
    });

    // Release NPCs after some time
    this.scene.time.delayedCall(8000, () => {
      for (const id of affectedNpcIds) {
        this.npcManager.releaseNPC(id);
      }
    });
  }
}
