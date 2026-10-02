/**
 * ChunkManager — manages infinite procedural tilemap chunks.
 *
 * Strategy: Creates a large blank tilemap (400x400 tiles = 20 chunks each way)
 * centered at origin. Chunks are generated on-demand as the camera moves.
 * The tilemap position is offset so that world coordinate (0,0) maps to the
 * center of the tilemap. This gives a 6400x6400 px explorable area from
 * (-3200, -3200) to (3200, 3200) which feels infinite for the demo.
 *
 * Chunks are 20x20 tiles. Distant chunks have their tiles cleared to save memory.
 */
import type * as Phaser from "phaser";
import { TILE_SIZE } from "../config";
import type { ChunkData } from "./ProceduralCity";
import {
  CHUNK_SIZE,
  generateChunk,
  isRiverRow,
  isRoad,
} from "./ProceduralCity";

const LOAD_RADIUS = 3; // chunks around camera to keep loaded
const UNLOAD_RADIUS = 5; // chunks beyond this are removed

// Total tilemap size in chunks (must be large enough for exploration)
const MAP_CHUNKS = 20;
const MAP_TILES = MAP_CHUNKS * CHUNK_SIZE; // 400 tiles
// Offset: world tile 0 maps to tilemap tile MAP_TILES/2
const TILE_OFFSET = MAP_TILES / 2;

interface LoadedChunk {
  cx: number;
  cy: number;
  data: ChunkData;
}

export class ChunkManager {
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
      "urban",
      "urban",
      TILE_SIZE,
      TILE_SIZE,
      0,
      0,
      1,
    );
    if (!tileset) {
      console.error("ChunkManager: Failed to load tileset");
      return;
    }
    this.tileset = tileset;

    const gl = this.map.createBlankLayer("ground", tileset);
    if (!gl) {
      console.error("ChunkManager: Failed to create ground layer");
      return;
    }
    this.groundLayer = gl;

    const bl = this.map.createBlankLayer("buildings", tileset);
    if (!bl) {
      console.error("ChunkManager: Failed to create building layer");
      return;
    }
    this.buildingLayer = bl;
    this.buildingLayer.setDepth(1);

    // Position the tilemap so that world (0,0) is at tilemap tile (TILE_OFFSET, TILE_OFFSET)
    // Tilemap pixel position = -(TILE_OFFSET * TILE_SIZE) to shift origin
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

  /** Convert world tile coordinate to internal tilemap coordinate */
  private toLocal(worldTile: number): number {
    return worldTile + TILE_OFFSET;
  }

  /** Check if a world tile coordinate is within the tilemap bounds */
  private inBounds(worldCol: number, worldRow: number): boolean {
    const lc = this.toLocal(worldCol);
    const lr = this.toLocal(worldRow);
    return lc >= 0 && lc < MAP_TILES && lr >= 0 && lr < MAP_TILES;
  }

  /** Update chunks based on camera position. Call from scene update(). */
  update(camera: Phaser.Cameras.Scene2D.Camera) {
    if (!this.initOk) return;

    const camCenterX = camera.scrollX + camera.width / (2 * camera.zoom);
    const camCenterY = camera.scrollY + camera.height / (2 * camera.zoom);

    // Convert pixel to world tile coords
    const centerWorldCol = Math.floor(camCenterX / TILE_SIZE);
    const centerWorldRow = Math.floor(camCenterY / TILE_SIZE);

    // Convert to chunk coords
    const centerCX = Math.floor(centerWorldCol / CHUNK_SIZE);
    const centerCY = Math.floor(centerWorldRow / CHUNK_SIZE);

    // Load chunks within radius
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

    // Unload distant chunks
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
    const data = generateChunk(cx, cy);
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

  /** Check if a world tile position has a building */
  hasBuildingAt(worldCol: number, worldRow: number): boolean {
    if (!this.inBounds(worldCol, worldRow)) return false;
    const tile = this.buildingLayer.getTileAt(
      this.toLocal(worldCol),
      this.toLocal(worldRow),
    );
    return tile !== null;
  }

  /** Check if a world tile is walkable (no building, not river) */
  isWalkable(worldCol: number, worldRow: number): boolean {
    if (isRoad(worldRow, worldCol)) return true;
    if (isRiverRow(worldRow)) return false;
    return !this.hasBuildingAt(worldCol, worldRow);
  }

  /** Get the ground tile GID at a world position */
  getGroundTile(worldCol: number, worldRow: number): number {
    if (!this.inBounds(worldCol, worldRow)) return 0;
    const tile = this.groundLayer.getTileAt(
      this.toLocal(worldCol),
      this.toLocal(worldRow),
    );
    return tile ? tile.index : 0;
  }

  /** Get ground grid for the NPC area (used by MovementSystem) */
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

  /** Scan loaded chunks for building positions in the given area */
  getBuildingPositions(
    minCol: number,
    minRow: number,
    maxCol: number,
    maxRow: number,
  ): {
    government: { x: number; y: number };
    shops: { id: string; x: number; y: number }[];
    factories: { id: string; x: number; y: number }[];
    houses: { id: string; x: number; y: number }[];
  } {
    const positions = {
      government: {
        x: Math.floor((minCol + maxCol) / 2),
        y: Math.floor((minRow + maxRow) / 2),
      },
      shops: [] as { id: string; x: number; y: number }[],
      factories: [] as { id: string; x: number; y: number }[],
      houses: [] as { id: string; x: number; y: number }[],
    };

    const SHOP1_TL = 177;
    const SHOP2_TL = 249;
    const LONG_SHOP_TL = 253;
    const FACTORY_TL = 227;
    const HOUSE_TL = 271;

    let shopIdx = 0;
    let factoryIdx = 0;
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

  destroy() {
    this.loadedChunks.clear();
  }
}
