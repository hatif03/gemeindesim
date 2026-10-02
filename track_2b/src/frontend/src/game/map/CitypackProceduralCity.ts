/**
 * Procedural city generation for the "citypack" tileset.
 * Mirrors ProceduralCity.ts but uses CitypackRegistry tile IDs.
 *
 * Tileset: citypack.png — 16×16px tiles, 64 columns wide, margin=0, spacing=0
 * IDs are 1-indexed (firstgid=1).
 */

import {
  GRASS,
  ROAD_BLANK,
  ROAD_DASH_H,
  ROAD_DASH_V,
  DIRT_TL,
  DIRT_T,
  DIRT_TR,
  DIRT_L,
  DIRT_C,
  DIRT_R,
  DIRT_BL,
  DIRT_B,
  DIRT_BR,
  TREE1_CANOPY,
  TREE1_TRUNK,
  TREE2_CANOPY,
  TREE2_TRUNK,
  OFFICE1,
  OFFICE2,
  OFFICE3,
  OFFICE4,
  SHOP1,
  SHOP2,
  HOUSE1,
} from "./CitypackRegistry";

// ─── GID helper (same as ProceduralCity.ts) ───
// Citypack is 0-indexed; Phaser putTileAt expects GID = tileIndex + 1
export function gid(tileIndex: number): number {
  return tileIndex + 1;
}

// ─── Road grid pattern ───
// Horizontal road period: 12 rows, roads at offsets 10,11
const ROAD_PERIOD_H = 12;
const HROAD_OFFSET_A = 10;
const HROAD_OFFSET_B = 11;

// Vertical road period: 12 cols, roads at offsets 10,11
const ROAD_PERIOD_V = 12;
const VROAD_OFFSET_A = 10;
const VROAD_OFFSET_B = 11;

// ─── Seeded PRNG ───
export class SeededRNG {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed % 2147483647;
    if (this.seed <= 0) this.seed += 2147483646;
  }

  next(): number {
    this.seed = (this.seed * 16807 + 0) % 2147483647;
    return (this.seed - 1) / 2147483646;
  }

  nextInt(min: number, max: number): number {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  shuffle<T>(arr: T[]): T[] {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = this.nextInt(0, i);
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
}

// ─── Infinite coordinate helpers ───

export function isHRoadRow(worldRow: number): boolean {
  const mod = ((worldRow % ROAD_PERIOD_H) + ROAD_PERIOD_H) % ROAD_PERIOD_H;
  return mod === HROAD_OFFSET_A || mod === HROAD_OFFSET_B;
}

export function isVRoadCol(worldCol: number): boolean {
  const mod = ((worldCol % ROAD_PERIOD_V) + ROAD_PERIOD_V) % ROAD_PERIOD_V;
  return mod === VROAD_OFFSET_A || mod === VROAD_OFFSET_B;
}

export function isRoad(worldRow: number, worldCol: number): boolean {
  return isHRoadRow(worldRow) || isVRoadCol(worldCol);
}

// ─── Zone assignment ───

type Zone = "PARK" | "GOVERNMENT" | "COMMERCIAL" | "RESIDENTIAL";

function getZone(worldRow: number, worldCol: number): Zone {
  const superRow = ((worldRow % 48) + 48) % 48;
  const superCol = ((worldCol % 60) + 60) % 60;

  if (superRow < 4) return "PARK";
  if (superRow >= 6 && superRow <= 17 && superCol >= 20 && superCol <= 40)
    return "GOVERNMENT";
  if (superRow >= 18 && superRow <= 30) return "COMMERCIAL";
  if (superRow >= 31 && superRow <= 44) return "RESIDENTIAL";
  return "PARK";
}

// ─── Chunk generation ───

export const CHUNK_SIZE = 20;

export interface ChunkData {
  ground: number[][];
  buildings: number[][];
}

export function generateCitypackChunk(cx: number, cy: number): ChunkData {
  const rng = new SeededRNG(cx * 10007 + cy * 31337 + 7919);

  const ground: number[][] = [];
  const buildings: number[][] = [];

  for (let lr = 0; lr < CHUNK_SIZE; lr++) {
    ground[lr] = [];
    buildings[lr] = [];
    for (let lc = 0; lc < CHUNK_SIZE; lc++) {
      ground[lr][lc] = gid(GRASS);
      buildings[lr][lc] = 0;
    }
  }

  // Pass 1: Roads on ground layer
  for (let lr = 0; lr < CHUNK_SIZE; lr++) {
    const wr = cy * CHUNK_SIZE + lr;
    for (let lc = 0; lc < CHUNK_SIZE; lc++) {
      const wc = cx * CHUNK_SIZE + lc;

      const hRoad = isHRoadRow(wr);
      const vRoad = isVRoadCol(wc);

      if (hRoad && vRoad) {
        ground[lr][lc] = gid(ROAD_BLANK);
      } else if (hRoad) {
        ground[lr][lc] = gid(ROAD_DASH_H);
      } else if (vRoad) {
        ground[lr][lc] = gid(ROAD_DASH_V);
      }
    }
  }

  // Pass 1b: Dirt patches (ground layer only, skip road cells)
  const numPatches = rng.nextInt(2, 4);
  for (let p = 0; p < numPatches; p++) {
    const patchW = rng.nextInt(3, 4);
    const patchH = rng.nextInt(3, 4);
    const startRow = rng.nextInt(0, CHUNK_SIZE - patchH);
    const startCol = rng.nextInt(0, CHUNK_SIZE - patchW);

    // Check that no cell in the patch lands on a road
    let blocked = false;
    for (let dr = 0; dr < patchH && !blocked; dr++) {
      for (let dc = 0; dc < patchW && !blocked; dc++) {
        const wr = cy * CHUNK_SIZE + startRow + dr;
        const wc = cx * CHUNK_SIZE + startCol + dc;
        if (isRoad(wr, wc)) blocked = true;
      }
    }
    if (blocked) continue;

    for (let dr = 0; dr < patchH; dr++) {
      for (let dc = 0; dc < patchW; dc++) {
        const lr = startRow + dr;
        const lc = startCol + dc;
        const isTop = dr === 0;
        const isBottom = dr === patchH - 1;
        const isLeft = dc === 0;
        const isRight = dc === patchW - 1;

        let tile: number;
        if (isTop && isLeft) tile = DIRT_TL;
        else if (isTop && isRight) tile = DIRT_TR;
        else if (isBottom && isLeft) tile = DIRT_BL;
        else if (isBottom && isRight) tile = DIRT_BR;
        else if (isTop) tile = DIRT_T;
        else if (isBottom) tile = DIRT_B;
        else if (isLeft) tile = DIRT_L;
        else if (isRight) tile = DIRT_R;
        else tile = DIRT_C;

        ground[lr][lc] = gid(tile);
      }
    }
  }

  // Pass 2: Determine zone from chunk center
  const centerWR = cy * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2);
  const centerWC = cx * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2);
  const zone = getZone(centerWR, centerWC);

  const placed = new Set<string>();

  function isLocalFree(lr: number, lc: number, h: number, w: number): boolean {
    for (let dr = 0; dr < h; dr++) {
      for (let dc = 0; dc < w; dc++) {
        const r = lr + dr;
        const c = lc + dc;
        if (r >= CHUNK_SIZE || c >= CHUNK_SIZE) return false;
        const wr = cy * CHUNK_SIZE + r;
        const wc = cx * CHUNK_SIZE + c;
        if (isRoad(wr, wc)) return false;
        if (buildings[r][c] !== 0) return false;
        if (placed.has(`${r},${c}`)) return false;
      }
    }
    return true;
  }

  function placeLocal(
    group: ReadonlyArray<ReadonlyArray<number>>,
    lr: number,
    lc: number,
  ): boolean {
    const h = group.length;
    const w = group[0].length;
    if (!isLocalFree(lr, lc, h, w)) return false;
    for (let dr = 0; dr < h; dr++) {
      for (let dc = 0; dc < w; dc++) {
        buildings[lr + dr][lc + dc] = gid(group[dr][dc]);
        placed.add(`${lr + dr},${lc + dc}`);
      }
    }
    return true;
  }

  if (zone === "PARK") {
    // Scatter trees every 2 tiles
    for (let lr = 0; lr < CHUNK_SIZE - 1; lr += 2) {
      for (let lc = 0; lc < CHUNK_SIZE - 1; lc += 2) {
        const wr = cy * CHUNK_SIZE + lr;
        const wc = cx * CHUNK_SIZE + lc;
        const wrBelow = cy * CHUNK_SIZE + lr + 1;
        if (isRoad(wr, wc) || isRoad(wrBelow, wc)) continue;

        const roll = rng.next();
        if (roll < 0.5) {
          // 50% chance TREE2 vs TREE1
          const useTree2 = rng.next() < 0.5;
          const canopy = useTree2 ? TREE2_CANOPY : TREE1_CANOPY;
          const trunk = useTree2 ? TREE2_TRUNK : TREE1_TRUNK;
          buildings[lr][lc] = gid(canopy);
          buildings[lr + 1][lc] = gid(trunk);
          placed.add(`${lr},${lc}`);
          placed.add(`${lr + 1},${lc}`);
        }
      }
    }
  } else {
    const palettes: Record<
      Exclude<Zone, "PARK">,
      ReadonlyArray<ReadonlyArray<ReadonlyArray<number>>>
    > = {
      GOVERNMENT: [OFFICE1, OFFICE2, OFFICE3, OFFICE4],
      COMMERCIAL: [SHOP1, SHOP2, SHOP1, HOUSE1],
      RESIDENTIAL: [HOUSE1, SHOP2, HOUSE1, HOUSE1],
    };

    const palette = palettes[zone];
    const shuffled = rng.shuffle([...palette] as ReadonlyArray<
      ReadonlyArray<number>
    >[]);

    let lr = 1;
    while (lr < CHUNK_SIZE - 1) {
      let lc = 1;
      let rowAdvance = 1;
      while (lc < CHUNK_SIZE - 1) {
        const wr = cy * CHUNK_SIZE + lr;
        const wc = cx * CHUNK_SIZE + lc;
        if (isRoad(wr, wc)) {
          lc++;
          continue;
        }

        let didPlace = false;
        for (const bldg of shuffled) {
          const bW = bldg[0].length;
          const bH = bldg.length;
          if (placeLocal(bldg, lr, lc)) {
            lc += bW;
            rowAdvance = Math.max(rowAdvance, bH);
            didPlace = true;
            break;
          }
        }
        if (!didPlace) {
          lc++;
        }
      }
      lr += rowAdvance;
    }
  }

  return { ground, buildings };
}
