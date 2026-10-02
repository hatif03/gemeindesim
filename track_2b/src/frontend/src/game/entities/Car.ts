import * as Phaser from "phaser";
import type { NPCHoverInfo, NPCState } from "@/types";
import { eventBridge } from "../bridge/EventBridge";
import { TILE_SIZE } from "../config";
import type { CarTemplate } from "../map/CarRegistry";

export class Car extends Phaser.GameObjects.Container {
  readonly npcId: string;
  readonly npcName: string;
  readonly template: CarTemplate;
  profession = "";
  role = "driver";
  category = "";
  reputation = 0.5;
  sentiment: NPCHoverInfo["sentiment"] = "neutral";
  tileX: number;
  tileY: number;
  isMoving = false;
  isHovered = false;
  npcState: NPCState["state"] = "idle";
  message?: string;
  direction: NPCState["direction"] = "down";

  private children_tiles: Phaser.GameObjects.Image[] = [];

  private getMainCamera(): Phaser.Cameras.Scene2D.Camera | null {
    return this.scene?.cameras?.main ?? null;
  }

  constructor(
    scene: Phaser.Scene,
    id: string,
    name: string,
    template: CarTemplate,
    tileX: number,
    tileY: number,
  ) {
    // Container origin = center of the car's bounding box
    const pixelX = tileX * TILE_SIZE + (template.cols * TILE_SIZE) / 2;
    const pixelY = tileY * TILE_SIZE + (template.rows * TILE_SIZE) / 2;
    super(scene, pixelX, pixelY);

    this.npcId = id;
    this.npcName = name;
    this.template = template;
    this.tileX = tileX;
    this.tileY = tileY;

    // Build child tile images centered around container origin
    const offsetX = -(template.cols * TILE_SIZE) / 2;
    const offsetY = -(template.rows * TILE_SIZE) / 2;

    for (let r = 0; r < template.rows; r++) {
      for (let c = 0; c < template.cols; c++) {
        const tileIndex = template.tiles[r][c]; // 0-indexed
        const img = scene.add.image(
          offsetX + c * TILE_SIZE + TILE_SIZE / 2,
          offsetY + r * TILE_SIZE + TILE_SIZE / 2,
          "citypack",
          tileIndex,
        );
        this.add(img);
        this.children_tiles.push(img);
      }
    }

    this.setDepth(10);
    this.setInteractive(
      new Phaser.Geom.Rectangle(
        offsetX,
        offsetY,
        template.cols * TILE_SIZE,
        template.rows * TILE_SIZE,
      ),
      Phaser.Geom.Rectangle.Contains,
    );
    this.on("pointerover", this.onHover, this);
    this.on("pointerout", this.onHoverOut, this);
    this.on("pointerdown", this.onClick, this);

    scene.add.existing(this);
  }

  /** Apply flip based on movement direction */
  /** NPC-compatible alias so NPCManager can call face() on cars and NPCs uniformly */
  face(dir: NPCState["direction"]) {
    this.updateDirection(dir);
  }

  updateDirection(dir: NPCState["direction"]) {
    this.direction = dir;
    if (this.template.orientation === "portrait") {
      // Default faces down (south); flip Y for up (north)
      this.setScale(1, dir === "up" ? -1 : 1);
    } else {
      // Default faces left (west); flip X for right (east)
      this.setScale(dir === "right" ? -1 : 1, 1);
    }
  }

  walkTo(col: number, row: number): Promise<void> {
    if (this.isMoving) return Promise.resolve();
    const dx = col - this.tileX;
    const dy = row - this.tileY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) return Promise.resolve();

    // Determine direction
    let dir: NPCState["direction"] = this.direction;
    if (Math.abs(dx) >= Math.abs(dy)) {
      dir = dx > 0 ? "right" : "left";
    } else {
      dir = dy > 0 ? "down" : "up";
    }
    this.updateDirection(dir);

    this.tileX = col;
    this.tileY = row;
    this.isMoving = true;

    return new Promise((resolve) => {
      this.scene.tweens.add({
        targets: this,
        x: col * TILE_SIZE + (this.template.cols * TILE_SIZE) / 2,
        y: row * TILE_SIZE + (this.template.rows * TILE_SIZE) / 2,
        duration: 350,
        ease: "Linear",
        onComplete: () => {
          this.isMoving = false;
          resolve();
        },
      });
    });
  }

  toState(): NPCState | null {
    const cam = this.getMainCamera();
    if (!cam) return null;
    return {
      id: this.npcId,
      name: this.npcName,
      profession: this.profession,
      role: this.role,
      reputation: this.reputation,
      x: (this.x - cam.scrollX) * cam.zoom,
      y: (this.y - cam.scrollY) * cam.zoom,
      direction: this.direction,
      state: this.npcState,
      message: this.message,
    };
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
}
