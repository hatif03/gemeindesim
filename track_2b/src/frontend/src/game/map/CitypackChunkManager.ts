/**
 * CitypackChunkManager — manages infinite procedural tilemap chunks for the citypack tileset.
 * Mirrors ChunkManager.ts but uses CitypackProceduralCity and the "citypack" tileset.
 */
import * as Phaser from "phaser";
import { TILE_SIZE } from "../config";
import type { BuildingPositions } from "@/types";
import {
  CHUNK_SIZE,
  generateCitypackChunk,
  isRoad,
} from "./CitypackProceduralCity";
import type { ChunkData } from "./CitypackProceduralCity";

const LOAD_RADIUS = 3;
const UNLOAD_RADIUS = 5;

const MAP_CHUNKS = 20;
const MAP_TILES = MAP_CHUNKS * CHUNK_SIZE; // 400 tiles
const TILE_OFFSET = MAP_TILES / 2;

// Top-left GIDs for building detection (0-indexed tile + 1 = GID, since firstgid=1)
const OFFICE1_TL = 131;
const OFFICE2_TL = 136;
const OFFICE3_TL = 141;
const OFFICE4_TL = 1107;
const SHOP1_TL = 706;
const SHOP2_TL = 712;
const HOUSE1_TL = 1096;

const OFFICE_TLS = new Set([OFFICE1_TL, OFFICE2_TL, OFFICE3_TL, OFFICE4_TL]);
const SHOP_TLS = new Set([SHOP1_TL, SHOP2_TL]);

interface LoadedChunk {
  cx: number;
  cy: number;
  data: ChunkData;
}

export class CitypackChunkManager {
  private scene: Phaser.Scene;
  private map!: Phaser.Tilemaps.Tilemap;
  private tileset!: Phaser.Tilemaps.Tileset;
  private groundLayer!: Phaser.Tilemaps.TilemapLayer;
  private buildingLayer!: Phaser.Tilemaps.TilemapLayer;
  private loadedChunks = new Map<string, LoadedChunk>();
  private initOk = false;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;

    this.map = scene.make.tilemap({
      tileWidth: TILE_SIZE,
      tileHeight: TILE_SIZE,
      width: MAP_TILES,
      height: MAP_TILES,
    });

    const tileset = this.map.addTilesetImage(
      "citypack",
      "citypack",
      TILE_SIZE,
      TILE_SIZE,
      0,
      0,
      1,
    );
    if (!tileset) {
      console.error("CitypackChunkManager: Failed to load tileset");
      return;
    }
    this.tileset = tileset;

    const gl = this.map.createBlankLayer("ground", tileset);
    if (!gl) {
      console.error("CitypackChunkManager: Failed to create ground layer");
      return;
    }
    this.groundLayer = gl;

    const bl = this.map.createBlankLayer("buildings", tileset);
    if (!bl) {
      console.error("CitypackChunkManager: Failed to create building layer");
      return;
    }
    this.buildingLayer = bl;
    this.buildingLayer.setDepth(1);

    this.groundLayer.setPosition(
      -TILE_OFFSET * TILE_SIZE,
      -TILE_OFFSET * TILE_SIZE,
    );
    this.buildingLayer.setPosition(
      -TILE_OFFSET * TILE_SIZE,
      -TILE_OFFSET * TILE_SIZE,
    );

    this.initOk = true;
  }

  isReady(): boolean {
    return this.initOk;
  }

  getGroundLayer(): Phaser.Tilemaps.TilemapLayer {
    return this.groundLayer;
  }

  getBuildingLayer(): Phaser.Tilemaps.TilemapLayer {
    return this.buildingLayer;
  }

  private toLocal(worldTile: number): number {
    return worldTile + TILE_OFFSET;
  }

  private inBounds(worldCol: number, worldRow: number): boolean {
    const lc = this.toLocal(worldCol);
    const lr = this.toLocal(worldRow);
    return lc >= 0 && lc < MAP_TILES && lr >= 0 && lr < MAP_TILES;
  }

  update(camera: Phaser.Cameras.Scene2D.Camera) {
    if (!this.initOk) return;

    const camCenterX = camera.scrollX + camera.width / (2 * camera.zoom);
    const camCenterY = camera.scrollY + camera.height / (2 * camera.zoom);

    const centerWorldCol = Math.floor(camCenterX / TILE_SIZE);
    const centerWorldRow = Math.floor(camCenterY / TILE_SIZE);

    const centerCX = Math.floor(centerWorldCol / CHUNK_SIZE);
    const centerCY = Math.floor(centerWorldRow / CHUNK_SIZE);

    for (let dy = -LOAD_RADIUS; dy <= LOAD_RADIUS; dy++) {
      for (let dx = -LOAD_RADIUS; dx <= LOAD_RADIUS; dx++) {
        const cx = centerCX + dx;
        const cy = centerCY + dy;
        const key = `${cx},${cy}`;
        if (!this.loadedChunks.has(key)) {
          this.loadChunk(cx, cy);
        }
      }
    }

    const toRemove: string[] = [];
    for (const [key, chunk] of this.loadedChunks) {
      const dist = Math.max(
        Math.abs(chunk.cx - centerCX),
        Math.abs(chunk.cy - centerCY),
      );
      if (dist > UNLOAD_RADIUS) {
        toRemove.push(key);
      }
    }
    for (const key of toRemove) {
      const chunk = this.loadedChunks.get(key)!;
      this.unloadChunk(key, chunk);
    }
  }

  private loadChunk(cx: number, cy: number) {
    const data = generateCitypackChunk(cx, cy);
    const key = `${cx},${cy}`;
    this.loadedChunks.set(key, { cx, cy, data });

    for (let lr = 0; lr < CHUNK_SIZE; lr++) {
      for (let lc = 0; lc < CHUNK_SIZE; lc++) {
        const worldCol = cx * CHUNK_SIZE + lc;
        const worldRow = cy * CHUNK_SIZE + lr;

        if (!this.inBounds(worldCol, worldRow)) continue;

        const tileCol = this.toLocal(worldCol);
        const tileRow = this.toLocal(worldRow);

        const groundGID = data.ground[lr][lc];
        if (groundGID > 0) {
          this.groundLayer.putTileAt(groundGID, tileCol, tileRow);
        }

        const buildingGID = data.buildings[lr][lc];
        if (buildingGID > 0) {
          this.buildingLayer.putTileAt(buildingGID, tileCol, tileRow);
        }
      }
    }
  }

  private unloadChunk(key: string, chunk: LoadedChunk) {
    for (let lr = 0; lr < CHUNK_SIZE; lr++) {
      for (let lc = 0; lc < CHUNK_SIZE; lc++) {
        const worldCol = chunk.cx * CHUNK_SIZE + lc;
        const worldRow = chunk.cy * CHUNK_SIZE + lr;

        if (!this.inBounds(worldCol, worldRow)) continue;

        const tileCol = this.toLocal(worldCol);
        const tileRow = this.toLocal(worldRow);
        this.groundLayer.removeTileAt(tileCol, tileRow);
        this.buildingLayer.removeTileAt(tileCol, tileRow);
      }
    }
    this.loadedChunks.delete(key);
  }

  hasBuildingAt(worldCol: number, worldRow: number): boolean {
    if (!this.inBounds(worldCol, worldRow)) return false;
    const tile = this.buildingLayer.getTileAt(
      this.toLocal(worldCol),
      this.toLocal(worldRow),
    );
    return tile !== null;
  }

  isWalkable(worldCol: number, worldRow: number): boolean {
    return !this.hasBuildingAt(worldCol, worldRow);
  }

  getGroundTile(worldCol: number, worldRow: number): number {
    if (!this.inBounds(worldCol, worldRow)) return 0;
    const tile = this.groundLayer.getTileAt(
      this.toLocal(worldCol),
      this.toLocal(worldRow),
    );
    return tile ? tile.index : 0;
  }

  getGroundGrid(
    minCol: number,
    minRow: number,
    maxCol: number,
    maxRow: number,
  ): number[][] {
    const grid: number[][] = [];
    for (let r = minRow; r <= maxRow; r++) {
      const row: number[] = [];
      for (let c = minCol; c <= maxCol; c++) {
        row.push(this.getGroundTile(c, r));
      }
      grid.push(row);
    }
    return grid;
  }

  getBuildingPositions(
    minCol: number,
    minRow: number,
    maxCol: number,
    maxRow: number,
  ): BuildingPositions {
    const positions: BuildingPositions = {
      government: {
        x: Math.floor((minCol + maxCol) / 2),
        y: Math.floor((minRow + maxRow) / 2),
      },
      shops: [],
      factories: [],
      houses: [],
    };

    let shopIdx = 0;
    let govIdx = 0;
    let houseIdx = 0;

    for (let r = minRow; r <= maxRow; r++) {
      for (let c = minCol; c <= maxCol; c++) {
        if (!this.inBounds(c, r)) continue;
        const tile = this.buildingLayer.getTileAt(
          this.toLocal(c),
          this.toLocal(r),
        );
        if (!tile) continue;
        const g = tile.index;

        if (OFFICE_TLS.has(g)) {
          // Use the first office found as the government position
          if (govIdx === 0) {
            positions.government = { x: c, y: r };
          }
          govIdx++;
        } else if (SHOP_TLS.has(g)) {
          positions.shops.push({ id: `shop-${shopIdx++}`, x: c, y: r });
        } else if (g === HOUSE1_TL) {
          positions.houses.push({ id: `house-${houseIdx++}`, x: c, y: r });
        }
      }
    }

    return positions;
  }

  destroy() {
    this.loadedChunks.clear();
  }
}
