import * as Phaser from "phaser";
import type { NPCHoverInfo, NPCState } from "@/types";
import { eventBridge } from "../bridge/EventBridge";
import { TILE_SIZE } from "../config";
import {
  type CharacterType,
  type Direction as NPCDirection,
  getAnimKey,
  getIdleFrame,
} from "../map/NPCCharacterRegistry";

function dirToNPCDir(dir: NPCState["direction"]): NPCDirection {
  switch (dir) {
    case "up":
      return "north";
    case "down":
      return "south";
    case "left":
      return "west";
    case "right":
      return "east";
  }
}

export class NPC extends Phaser.GameObjects.Sprite {
  readonly npcId: string;
  readonly npcName: string;
  readonly charIndex: number;
  readonly characterType: CharacterType;
  profession = "";
  role = "";
  category = "";
  reputation = 0.5;
  sentiment: NPCHoverInfo["sentiment"] = "neutral";

  /** Grid position (in tile coordinates) */
  tileX: number;
  tileY: number;

  direction: NPCState["direction"] = "down";
  npcState: NPCState["state"] = "idle";
  message?: string;

  /** True while a movement tween is running */
  isMoving = false;

  /** True while the pointer is over this NPC */
  isHovered = false;

  /** Active bob tween, stopped on walk completion */
  private bobTween?: Phaser.Tweens.Tween;

  private getMainCamera(): Phaser.Cameras.Scene2D.Camera | null {
    return this.scene?.cameras?.main ?? null;
  }

  constructor(
    scene: Phaser.Scene,
    id: string,
    name: string,
    characterType: CharacterType,
    charIndex: number,
    tileX: number,
    tileY: number,
  ) {
    const idleFrame = getIdleFrame(characterType, "south");
    super(
      scene,
      tileX * TILE_SIZE + TILE_SIZE / 2,
      tileY * TILE_SIZE + TILE_SIZE / 2,
      "city-tiles",
      idleFrame,
    );

    this.npcId = id;
    this.npcName = name;
    this.characterType = characterType;
    this.charIndex = charIndex;
    this.tileX = tileX;
    this.tileY = tileY;

    // NPCs render above everything: ground=0, buildings=1, phase overlay=5
    this.setDepth(10);

    // Interactive for hover + click
    this.setInteractive({ useHandCursor: true });
    this.on("pointerover", this.onHover, this);
    this.on("pointerout", this.onHoverOut, this);
    this.on("pointerdown", this.onClick, this);

    scene.add.existing(this);
  }

  face(dir: NPCState["direction"]) {
    this.direction = dir;
    const npcDir = dirToNPCDir(dir);
    if (!this.isMoving) {
      this.setFrame(getIdleFrame(this.characterType, npcDir));
    }
  }

  /** Tween-move to an adjacent tile with bob animation. Rejects moves > 2 tiles to prevent teleporting. */
  walkTo(col: number, row: number): Promise<void> {
    if (this.isMoving) return Promise.resolve();

    // Determine direction from delta
    const dx = col - this.tileX;
    const dy = row - this.tileY;

    // Guard: reject long-distance moves to prevent teleporting
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) return Promise.resolve();

    let dir: NPCState["direction"];
    if (dx > 0) dir = "right";
    else if (dx < 0) dir = "left";
    else if (dy > 0) dir = "down";
    else dir = "up";

    this.direction = dir;
    const npcDir = dirToNPCDir(dir);

    this.tileX = col;
    this.tileY = row;
    this.isMoving = true;

    this.play(getAnimKey(this.characterType, npcDir));

    const targetY = row * TILE_SIZE + TILE_SIZE / 2;

    // Bob animation: squash-stretch + sway to simulate walking (no Y conflict)
    this.bobTween = this.scene.tweens.add({
      targets: this,
      scaleY: { from: 1.0, to: 0.9 },
      scaleX: { from: 1.0, to: 1.1 },
      angle: { from: -3, to: 3 },
      duration: 80,
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    return new Promise((resolve) => {
      this.scene.tweens.add({
        targets: this,
        x: col * TILE_SIZE + TILE_SIZE / 2,
        y: targetY,
        duration: 300,
        ease: "Linear",
        onUpdate: () => {
          if (this.isHovered) {
            this.emitHoverEvent();
          }
        },
        onComplete: () => {
          // Stop bob and reset to neutral
          this.bobTween?.stop();
          this.bobTween = undefined;
          this.setScale(1, 1);
          this.setAngle(0);
          this.stop();
          this.setFrame(getIdleFrame(this.characterType, npcDir));
          this.isMoving = false;
          resolve();
        },
      });
    });
  }

  private emitHoverEvent() {
    const cam = this.getMainCamera();
    if (!cam) return;

    eventBridge.emitNPCHover({
      id: this.npcId,
      name: this.npcName,
      profession: this.profession,
      role: this.role,
      reputation: this.reputation,
      x: (this.x - cam.scrollX) * cam.zoom,
      y: (this.y - cam.scrollY) * cam.zoom,
      sentiment: this.sentiment,
      state: this.npcState,
    });
  }

  private onHover() {
    this.isHovered = true;
    this.emitHoverEvent();
  }

  private onHoverOut() {
    this.isHovered = false;
    eventBridge.emitNPCHoverOut();
  }

  private onClick() {
    eventBridge.emitNPCClick(this.npcId);
  }

  /** Snapshot for EventBridge → React chat bubbles (camera-relative screen coords) */
  toState(): NPCState | null {
    const cam = this.getMainCamera();
    if (!cam) return null;

    return {
      id: this.npcId,
      name: this.npcName,
      profession: this.profession,
      role: this.role,
      reputation: this.reputation,
      category: this.category,
      x: (this.x - cam.scrollX) * cam.zoom,
      y: (this.y - cam.scrollY) * cam.zoom,
      direction: this.direction,
      state: this.npcState,
      message: this.message,
    };
  }
}
