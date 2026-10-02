import * as Phaser from "phaser";
import { proceduralMap, selectedMap } from "../config";

export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: "BootScene" });
  }

  preload() {
    // Show loading bar
    const { width, height } = this.cameras.main;
    const barW = width * 0.6;
    const barH = 12;
    const barX = (width - barW) / 2;
    const barY = height / 2;

    const bg = this.add.graphics();
    bg.fillStyle(0x222244, 1);
    bg.fillRect(barX, barY, barW, barH);

    const fill = this.add.graphics();
    this.load.on("progress", (value: number) => {
      fill.clear();
      fill.fillStyle(0x4488ff, 1);
      fill.fillRect(barX + 2, barY + 2, (barW - 4) * value, barH - 4);
    });

    const text = this.add.text(width / 2, barY - 24, "Loading GemeindeSim...", {
      fontSize: "14px",
      color: "#aabbee",
    });
    text.setOrigin(0.5);

    // Load map + tileset based on selected map
    if (selectedMap === "pico8") {
      this.load.image("pico8", "/assets/citymap_pico8/tilemap_packed.png");
      this.load.tilemapTiledJSON("city", "/assets/maps/pico8-city.json");
    } else if (selectedMap === "citypack") {
      // Load as spritesheet so Car entities can address individual tile frames by 0-indexed ID
      this.load.spritesheet("citypack", "/assets/maps/citypack.png", {
        frameWidth: 16,
        frameHeight: 16,
        margin: 0,
        spacing: 0,
      });
      if (!proceduralMap) {
        this.load.tilemapTiledJSON(
          "citypack-city",
          "/assets/maps/citypack-city.json",
        );
      }
    } else {
      this.load.image("urban", "/assets/citymap_tilesets/CCity_mockup.png");
      this.load.tilemapTiledJSON("city", "/assets/maps/city.json");
    }

    // Keep old spritesheet for NPC sprites (still uses Kenney RPG Urban Pack)
    this.load.spritesheet("city-tiles", "/assets/tilesets/tilemap_packed.png", {
      frameWidth: 16,
      frameHeight: 16,
      margin: 0,
      spacing: 0,
    });
  }

  create() {
    this.scene.start("WorldScene");
  }
}
