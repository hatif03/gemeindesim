import * as Phaser from "phaser";
import type { BuildingPositions } from "@/types";
import { eventBridge } from "../bridge/EventBridge";
import {
  CENTER_BOUNDS,
  GAME_HEIGHT,
  GAME_WIDTH,
  TILE_SIZE,
  getMapConfig,
  proceduralMap,
  selectedMap,
} from "../config";
import { SimEventHandler } from "../events/SimEventHandler";
import { ChunkManager } from "../map/ChunkManager";
import { CitypackChunkManager } from "../map/CitypackChunkManager";
import {
  isRoad as citypackIsRoad,
  isVRoadCol as citypackIsVRoadCol,
  isHRoadRow as citypackIsHRoadRow,
} from "../map/CitypackProceduralCity";
import {
  isRoad as ccityIsRoad,
  isVRoadCol as ccityIsVRoadCol,
  isHRoadRow as ccityIsHRoadRow,
} from "../map/ProceduralCity";
import { ROAD_TILES as CITYPACK_ROAD_TILES } from "../map/CitypackRegistry";
import {
  ALL_CHARACTERS,
  ALL_DIRECTIONS,
  getAnimKey,
  getWalkFrames,
} from "../map/NPCCharacterRegistry";
import { NPCManager } from "../systems/NPCManager";

export class WorldScene extends Phaser.Scene {
  // Static map (fallback)
  private staticGroundLayer?: Phaser.Tilemaps.TilemapLayer;
  private staticBuildingLayer?: Phaser.Tilemaps.TilemapLayer;

  // Infinite procedural map
  private chunkManager?: ChunkManager;
  private useChunks = false;

  // Citypack procedural map
  private citypackChunkManager?: CitypackChunkManager;
  private useCitypackChunks = false;

  private phaseOverlay?: Phaser.GameObjects.Rectangle;
  private npcManager?: NPCManager;
  private simEventHandler?: SimEventHandler;
  private cursors?: Phaser.Types.Input.Keyboard.CursorKeys;
  private sceneReady = false;
  private cleanedUp = false;

  constructor() {
    super({ key: "WorldScene" });
  }

  create() {
    this.sceneReady = false;
    this.cleanedUp = false;
    this.staticGroundLayer = undefined;
    this.staticBuildingLayer = undefined;
    this.chunkManager = undefined;
    this.citypackChunkManager = undefined;
    this.phaseOverlay = undefined;
    this.npcManager = undefined;
    this.simEventHandler = undefined;
    this.useChunks = false;
    this.useCitypackChunks = false;

    this.events.once(Phaser.Scenes.Events.SHUTDOWN, this.cleanupScene, this);
    this.events.once(Phaser.Scenes.Events.DESTROY, this.cleanupScene, this);

    if (selectedMap === "citypack") {
      if (proceduralMap) {
        try {
          this.citypackChunkManager = new CitypackChunkManager(this);
          if (this.citypackChunkManager.isReady()) {
            this.useCitypackChunks = true;
            this.citypackChunkManager.update(this.cameras.main);
          }
        } catch (e) {
          console.warn("CitypackChunkManager failed:", e);
        }
      }
      // If !proceduralMap, fall through to initStaticMap()
    } else if (selectedMap !== "pico8") {
      try {
        this.chunkManager = new ChunkManager(this);
        if (this.chunkManager.isReady()) {
          this.useChunks = true;
          this.chunkManager.update(this.cameras.main);
        }
      } catch (e) {
        console.warn("ChunkManager failed, falling back to static map:", e);
        this.useChunks = false;
      }
    }

    // Fallback or pico8: load static Tiled JSON map
    if (!this.useChunks && !this.useCitypackChunks) {
      this.initStaticMap();
    }

    // Pico-8 map is 440×240px — zoom and center it to fill the canvas
    if (!this.useChunks && selectedMap === "pico8") {
      const mc = getMapConfig(); // { tileSize: 8, cols: 55, rows: 30 }
      const mapPixelW = mc.cols * mc.tileSize; // 440
      const mapPixelH = mc.rows * mc.tileSize; // 240
      const zoom = Math.min(GAME_WIDTH / mapPixelW, GAME_HEIGHT / mapPixelH);
      this.cameras.main.setZoom(zoom);
      this.cameras.main.centerOn(mapPixelW / 2, mapPixelH / 2);
    }

    // Citypack static map is 100×80 at 16px = 1600×1280px — center camera on map
    if (
      !this.useChunks &&
      !this.useCitypackChunks &&
      selectedMap === "citypack"
    ) {
      this.cameras.main.centerOn((100 * 16) / 2, (80 * 16) / 2);
    }

    if (selectedMap === "citypack") {
      const MAP_PX_W = 100 * TILE_SIZE; // 1600
      const MAP_PX_H = 80 * TILE_SIZE; // 1280
      const minZoom = Math.max(GAME_WIDTH / MAP_PX_W, GAME_HEIGHT / MAP_PX_H);
      this.cameras.main.setZoom(Math.max(this.cameras.main.zoom, minZoom));
      this.cameras.main.setBounds(0, 0, MAP_PX_W, MAP_PX_H, true);
      (this as any)._minZoom = minZoom;
      (this as any)._mapPxW = MAP_PX_W;
      (this as any)._mapPxH = MAP_PX_H;
    }

    // Snap camera to integer pixels to prevent tile seams during pan/zoom
    this.cameras.main.roundPixels = true;

    // Phase-change color overlay (sits above buildings, below NPCs)
    this.phaseOverlay = this.add.rectangle(
      GAME_WIDTH / 2,
      GAME_HEIGHT / 2,
      GAME_WIDTH * 4, // larger to cover zoom-out
      GAME_HEIGHT * 4,
      0x000000,
      0,
    );
    this.phaseOverlay.setDepth(5);
    this.phaseOverlay.setScrollFactor(0); // stays fixed on screen

    // Listen for simulation events via the bridge
    eventBridge.on("sim:phase-change", this.onPhaseChange, this);
    eventBridge.on("sim:camera-pan", this.onCameraPan, this);
    eventBridge.on("sim:camera-zoom", this.onCameraZoom, this);

    eventBridge.on("sim:camera-snap-npc", this.onCameraSnapNPC, this);

    // ─── NPC Animations & System ───
    this.registerNPCAnimations();
    this.npcManager = new NPCManager(
      this,
      this.getBuildingPositions(),
      this.isWalkable.bind(this),
      this.getIsRoad(),
      this.getRoadTypeFn(),
    );
    this.simEventHandler = new SimEventHandler(this, this.npcManager);

    // Keyboard controls
    if (this.input?.keyboard) {
      this.cursors = this.input.keyboard.createCursorKeys();
    }

    // Emit ready state
    this.sceneReady = true;
    this.events.emit("world-ready");
  }

  update() {
    if (!this.sceneReady || this.cleanedUp) return;

    if (this.useChunks && this.chunkManager) {
      this.chunkManager.update(this.cameras.main);
    }
    if (this.useCitypackChunks && this.citypackChunkManager) {
      this.citypackChunkManager.update(this.cameras.main);
    }

    this.npcManager?.refreshActiveBubblePositions();

    // Camera spring bounce for citypack
    if (selectedMap === "citypack") {
      const cam = this.cameras.main;
      const SOFT_X_MIN = 160;
      const SOFT_X_MAX = 1440;
      const SOFT_Y_MIN = 80;
      const SOFT_Y_MAX = 1200;
      const SPRING = 0.08;

      const cx = cam.scrollX + cam.width / (2 * cam.zoom);
      const cy = cam.scrollY + cam.height / (2 * cam.zoom);

      let tx = cx;
      let ty = cy;
      if (cx < SOFT_X_MIN) tx = cx + (SOFT_X_MIN - cx) * SPRING;
      else if (cx > SOFT_X_MAX) tx = cx + (SOFT_X_MAX - cx) * SPRING;
      if (cy < SOFT_Y_MIN) ty = cy + (SOFT_Y_MIN - cy) * SPRING;
      else if (cy > SOFT_Y_MAX) ty = cy + (SOFT_Y_MAX - cy) * SPRING;

      if (tx !== cx || ty !== cy) {
        cam.scrollX = Math.round(tx - cam.width / (2 * cam.zoom));
        cam.scrollY = Math.round(ty - cam.height / (2 * cam.zoom));
      }
    }

    // Keyboard panning
    if (this.cursors) {
      const cam = this.cameras.main;
      const speed = 10 / cam.zoom;
      if (this.cursors.left.isDown) cam.scrollX -= speed;
      if (this.cursors.right.isDown) cam.scrollX += speed;
      if (this.cursors.up.isDown) cam.scrollY -= speed;
      if (this.cursors.down.isDown) cam.scrollY += speed;
    }
  }

  private registerNPCAnimations() {
    for (const char of ALL_CHARACTERS) {
      for (const dir of ALL_DIRECTIONS) {
        const key = getAnimKey(char, dir);
        if (this.anims.exists(key)) continue;
        const [frameA, frameB] = getWalkFrames(char, dir);
        this.anims.create({
          key,
          frames: [
            { key: "city-tiles", frame: frameA },
            { key: "city-tiles", frame: frameB },
          ],
          frameRate: 6,
          repeat: -1,
        });
      }
    }
  }

  // ─── Static map initialization (fallback) ───

  private initStaticMap() {
    let mapKey: string;
    let tilesetKey: string;
    let tilesetName: string;
    let groundLayerName: string;
    let buildingLayerName: string;

    if (selectedMap === "citypack") {
      mapKey = "citypack-city";
      tilesetKey = "citypack";
      tilesetName = "citypack";
      groundLayerName = "Terrain";
      buildingLayerName = "Objects";
    } else if (selectedMap === "pico8") {
      mapKey = "city";
      tilesetKey = "pico8";
      tilesetName = "city-tileset";
      groundLayerName = "Terrain";
      buildingLayerName = "Objects";
    } else {
      mapKey = "city";
      tilesetKey = "urban";
      tilesetName = "urban";
      groundLayerName = "ground";
      buildingLayerName = "buildings";
    }

    const mc = getMapConfig();
    const map = this.make.tilemap({ key: mapKey });

    const tileset = map.addTilesetImage(
      tilesetName,
      tilesetKey,
      mc.tileSize,
      mc.tileSize,
      0,
      mc.spacing,
    );
    if (!tileset) {
      console.error("Failed to load tileset");
      return;
    }

    const groundLayer = map.createLayer(groundLayerName, tileset);
    if (!groundLayer) {
      console.error("Failed to create ground layer");
      return;
    }
    this.staticGroundLayer = groundLayer;

    const buildingLayer = map.createLayer(buildingLayerName, tileset);
    if (!buildingLayer) {
      console.error("Failed to create building layer");
      return;
    }
    this.staticBuildingLayer = buildingLayer;
    this.staticBuildingLayer.setDepth(1);
  }

  // ─── Shared tile queries (delegate to chunks or static) ───

  getBuildingPositions(): BuildingPositions {
    if (this.useCitypackChunks && this.citypackChunkManager) {
      return this.citypackChunkManager.getBuildingPositions(
        CENTER_BOUNDS.minCol,
        CENTER_BOUNDS.minRow,
        CENTER_BOUNDS.maxCol,
        CENTER_BOUNDS.maxRow,
      );
    }

    if (this.useChunks && this.chunkManager) {
      return this.chunkManager.getBuildingPositions(
        CENTER_BOUNDS.minCol,
        CENTER_BOUNDS.minRow,
        CENTER_BOUNDS.maxCol,
        CENTER_BOUNDS.maxRow,
      );
    }

    // Static map scan
    const positions: BuildingPositions = {
      government: { x: 9, y: 5 },
      shops: [],
      factories: [],
      houses: [],
    };

    if (!this.staticBuildingLayer) return positions;

    const SHOP1_TL = 177;
    const SHOP2_TL = 249;
    const LONG_SHOP_TL = 253;
    const FACTORY_TL = 227;
    const HOUSE_TL = 271;

    let shopIdx = 0;
    let factoryIdx = 0;
    let houseIdx = 0;

    const mc = getMapConfig();
    for (let r = 0; r < mc.rows; r++) {
      for (let c = 0; c < mc.cols; c++) {
        const tile = this.staticBuildingLayer.getTileAt(c, r);
        if (!tile) continue;
        const g = tile.index;

        if (g === FACTORY_TL) {
          positions.factories.push({
            id: `factory-${factoryIdx++}`,
            x: c,
            y: r,
          });
        } else if (g === SHOP1_TL || g === SHOP2_TL || g === LONG_SHOP_TL) {
          positions.shops.push({ id: `shop-${shopIdx++}`, x: c, y: r });
        } else if (g === HOUSE_TL) {
          positions.houses.push({ id: `house-${houseIdx++}`, x: c, y: r });
        }
      }
    }

    return positions;
  }

  /** Returns road orientation at a tile: "v"=vertical, "h"=horizontal, "none"=not a road */
  private getRoadTypeFn(): (col: number, row: number) => "v" | "h" | "none" {
    const ROAD_V_GID = 2440; // ROAD_DASH_V + 1
    const ROAD_H_GID = 2438; // ROAD_DASH_H + 1
    const ROAD_INT_GID = 2436; // ROAD_BLANK + 1

    if (this.useCitypackChunks) {
      return (col, row) => {
        if (citypackIsVRoadCol(col) && citypackIsHRoadRow(row)) return "none"; // intersection
        if (citypackIsVRoadCol(col)) return "v";
        if (citypackIsHRoadRow(row)) return "h";
        return "none";
      };
    }
    if (this.useChunks) {
      return (col, row) => {
        if (ccityIsVRoadCol(col) && ccityIsHRoadRow(row)) return "none"; // intersection
        if (ccityIsVRoadCol(col)) return "v";
        if (ccityIsHRoadRow(row)) return "h";
        return "none";
      };
    }
    // Static citypack: read tile GID
    if (selectedMap === "citypack" && this.staticGroundLayer) {
      return (col, row) => {
        const tile = this.staticGroundLayer!.getTileAt(col, row);
        if (!tile) return "none";
        if (tile.index === ROAD_V_GID) return "v";
        if (tile.index === ROAD_H_GID) return "h";
        // ROAD_INT (intersection) falls through to "none" — cars should not spawn at crossroads
        return "none";
      };
    }
    return () => "none";
  }

  /** Returns a road-check function based on the active map type */
  private getIsRoad(): (col: number, row: number) => boolean {
    if (this.useCitypackChunks) {
      // CitypackProceduralCity.isRoad takes (worldRow, worldCol) — swap
      return (col, row) => citypackIsRoad(row, col);
    }
    if (this.useChunks) {
      // ProceduralCity.isRoad takes (worldRow, worldCol) — swap
      return (col, row) => ccityIsRoad(row, col);
    }
    // Static citypack: check ground tile GID against known road GIDs
    if (selectedMap === "citypack" && this.staticGroundLayer) {
      return (col, row) => {
        const tile = this.staticGroundLayer!.getTileAt(col, row);
        return tile !== null && CITYPACK_ROAD_TILES.has(tile.index);
      };
    }
    // pico8 / ccity static fallback: any non-building tile is walkable-as-road
    return (col, row) => this.isWalkable(col, row);
  }

  isWalkable(col: number, row: number): boolean {
    if (this.useCitypackChunks && this.citypackChunkManager) {
      return this.citypackChunkManager.isWalkable(col, row);
    }

    if (this.useChunks && this.chunkManager) {
      return this.chunkManager.isWalkable(col, row);
    }

    // Static JSON map — fail closed until the tile layer exists.
    const mc = getMapConfig();
    if (col < 0 || col >= mc.cols || row < 0 || row >= mc.rows) return false;
    const layer = this.staticBuildingLayer;
    if (!layer) return false;
    return !layer.getTileAt(col, row);
  }

  // ─── Internal event handlers ───

  private onCameraPan(data: { dx: number; dy: number }) {
    const cam = this.getMainCamera();
    if (!cam) return;

    cam.scrollX = Math.round(cam.scrollX + data.dx);
    cam.scrollY = Math.round(cam.scrollY + data.dy);
    this.npcManager?.refreshActiveBubblePositions();
  }

  private onCameraZoom(data: { delta: number; x?: number; y?: number }) {
    const cam = this.getMainCamera();
    if (!cam) return;

    const zoomStep = 0.2;
    const minZoom = (this as any)._minZoom ?? 0.5;
    const maxZoom = 5.0;

    const oldZoom = cam.zoom;
    const nextZoom = Phaser.Math.Clamp(
      oldZoom + data.delta * zoomStep,
      minZoom,
      maxZoom,
    );

    if (oldZoom === nextZoom) return;

    if (data.x !== undefined && data.y !== undefined) {
      // Zoom to mouse: adjust scroll so the point under the mouse stays fixed
      // pointWorld = (pointScreen / zoom) + scroll
      // We want pointWorldBefore == pointWorldAfter
      // (mouseX / oldZoom) + oldScrollX == (mouseX / nextZoom) + nextScrollX
      // nextScrollX = oldScrollX + mouseX * (1/oldZoom - 1/nextZoom)

      const mouseX = data.x;
      const mouseY = data.y;

      cam.setZoom(nextZoom);
      cam.scrollX += mouseX * (1 / oldZoom - 1 / nextZoom);
      cam.scrollY += mouseY * (1 / oldZoom - 1 / nextZoom);
    } else {
      cam.setZoom(nextZoom);
    }
    this.npcManager?.refreshActiveBubblePositions();
  }

  private onCameraSnapNPC(data: { npcId: string }) {
    const npc = this.npcManager?.getNPC(data.npcId);
    if (!npc) return;
    const targetX = npc.tileX * TILE_SIZE + TILE_SIZE / 2;
    const targetY = npc.tileY * TILE_SIZE + TILE_SIZE / 2;
    this.cameras.main.pan(targetX, targetY, 400, "Power2");
    this.npcManager?.refreshActiveBubblePositions();
  }

  private onPhaseChange(data: { phase: number; round: number; sentiment?: number }) {
    const overlay = this.phaseOverlay;
    if (!this.sceneReady || this.cleanedUp || !overlay) return;

    const sentiment = data.sentiment ?? 0.5;
    if (data.phase <= 1) {
      overlay.setFillStyle(0x000000, 0);
    } else {
      const color =
        sentiment >= 0.6 ? 0x00ff44 : sentiment <= 0.35 ? 0xff2200 : 0xff8800;
      const alpha = 0.08 + (1 - sentiment) * 0.1;
      overlay.setFillStyle(color, alpha);
    }
  }

  private getMainCamera(): Phaser.Cameras.Scene2D.Camera | null {
    if (!this.sceneReady || this.cleanedUp) return null;
    return this.cameras?.main ?? null;
  }

  private cleanupScene() {
    if (this.cleanedUp) return;

    this.cleanedUp = true;
    this.sceneReady = false;

    eventBridge.off("sim:phase-change", this.onPhaseChange, this);
    eventBridge.off("sim:camera-pan", this.onCameraPan, this);
    eventBridge.off("sim:camera-zoom", this.onCameraZoom, this);

    eventBridge.off("sim:camera-snap-npc", this.onCameraSnapNPC, this);
    this.simEventHandler?.destroy();
    this.simEventHandler = undefined;
    this.cursors = undefined;
    this.npcManager?.destroy();
    this.npcManager = undefined;
    this.chunkManager?.destroy();
    this.chunkManager = undefined;
    this.citypackChunkManager?.destroy();
    this.citypackChunkManager = undefined;
    this.staticGroundLayer = undefined;
    this.staticBuildingLayer = undefined;
    this.phaseOverlay = undefined;
    this.useChunks = false;
    this.useCitypackChunks = false;
  }

  shutdown() {
    this.cleanupScene();
  }
}
