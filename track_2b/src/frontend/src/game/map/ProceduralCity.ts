/**
 * Procedural city generation logic — browser-compatible TypeScript port of generate-map.js.
 * Used by ChunkManager for runtime infinite world generation.
 *
 * Tileset: CCity_mockup.png (640x256, 40 cols x 16 rows, 16x16 tiles)
 * Tiled JSON uses GID = tile_index + 1 (firstgid=1). GID 0 = empty.
 */

// ─── Tile IDs (0-indexed) ───
const GRASS = 0;
const WATER_FULL = 566;
const RIVER_EDGE_H = 490;
const CONCRETE_FLOOR_L = 290;
const CONCRETE_FLOOR_R = 291;
const PARKING_L = 250;
const PARKING_R = 251;
const ROAD_X_TOP = 350;
const ROAD_X_BOTTOM = 390;
const ROAD_INTERIOR = 354;
const ROAD_Y_LEFT = 194;
const ROAD_Y_RIGHT = 195;

// Buildings (multi-tile groups, 0-indexed)
const FACTORY = [
  [226, 227, 228, 229],
  [266, 267, 268, 269],
  [306, 307, 308, 309],
];
const SHOP1 = [
  [176, 177],
  [216, 217],
  [256, 257],
  [296, 297],
];
const SHOP2 = [
  [248, 249],
  [288, 289],
];
const LONG_SHOP = [
  [252, 253, 254, 255],
  [292, 293, 294, 295],
];
const HOUSE = [
  [270, 271],
  [310, 311],
];
const HOSPITAL = [
  [178, 179, 180, 181],
  [218, 219, 220, 221],
  [258, 259, 260, 261],
  [298, 299, 300, 301],
];
const CONCRETE_BLDG = [
  [164, 165, 166, 167],
  [204, 205, 206, 207],
  [244, 245, 246, 247],
  [284, 285, 286, 287],
];
const TREE = [
  [356, 357],
  [396, 397],
];
const ROCK = [
  [404, 405],
  [444, 445],
];

// ─── Road grid pattern (repeats every PATTERN_ROWS/COLS) ───
// Horizontal road pairs repeat every 8 rows: roads at offsets 5,6 within each 8-row band
const ROAD_PERIOD_V = 8; // vertical repetition period (rows)
const ROAD_OFFSET_A = 5; // first road lane within period
const ROAD_OFFSET_B = 6; // second road lane within period

// Vertical road pairs repeat every 15 cols: roads at offsets 9,10 within each 15-col band
const ROAD_PERIOD_H = 15; // horizontal repetition period (cols)
const VROAD_OFFSET_A = 9;
const VROAD_OFFSET_B = 10;

// River pattern: every 24 rows, a 5-row river band starting at offset 5 within the band
const RIVER_PERIOD = 24;
const RIVER_START_OFFSET = 5; // edge row within river period
const RIVER_WIDTH = 5; // edge + 3 water + edge

export function gid(tileIndex: number): number {
  return tileIndex + 1;
}

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

/** Check if a world row is a horizontal road lane */
export function isHRoadRow(worldRow: number): boolean {
  const mod = ((worldRow % ROAD_PERIOD_V) + ROAD_PERIOD_V) % ROAD_PERIOD_V;
  return mod === ROAD_OFFSET_A || mod === ROAD_OFFSET_B;
}

/** Check if a world col is a vertical road lane */
export function isVRoadCol(worldCol: number): boolean {
  const mod = ((worldCol % ROAD_PERIOD_H) + ROAD_PERIOD_H) % ROAD_PERIOD_H;
  return mod === VROAD_OFFSET_A || mod === VROAD_OFFSET_B;
}

/** Check if any road at this position */
export function isRoad(worldRow: number, worldCol: number): boolean {
  return isHRoadRow(worldRow) || isVRoadCol(worldCol);
}

/** Check if world row is a river row (edge or water) */
export function isRiverRow(worldRow: number): boolean {
  const mod = ((worldRow % RIVER_PERIOD) + RIVER_PERIOD) % RIVER_PERIOD;
  return mod >= RIVER_START_OFFSET && mod < RIVER_START_OFFSET + RIVER_WIDTH;
}

/** Check if world row is deep water (not edge) */
function isWaterRow(worldRow: number): boolean {
  const mod = ((worldRow % RIVER_PERIOD) + RIVER_PERIOD) % RIVER_PERIOD;
  return mod > RIVER_START_OFFSET && mod < RIVER_START_OFFSET + RIVER_WIDTH - 1;
}

/** Check if world row is a river edge (top or bottom) */
function isRiverEdge(worldRow: number): boolean {
  const mod = ((worldRow % RIVER_PERIOD) + RIVER_PERIOD) % RIVER_PERIOD;
  return (
    mod === RIVER_START_OFFSET || mod === RIVER_START_OFFSET + RIVER_WIDTH - 1
  );
}

// ─── Zone assignment for infinite world ───

type Zone =
  | "PARK"
  | "GOVERNMENT"
  | "COMMERCIAL"
  | "RESIDENTIAL"
  | "INDUSTRIAL"
  | "WATERFRONT";

function getZone(worldRow: number, worldCol: number): Zone {
  // Use the row's position within the road period to determine zone
  const rowMod = ((worldRow % ROAD_PERIOD_V) + ROAD_PERIOD_V) % ROAD_PERIOD_V;

  // If it's a river row, waterfront
  if (isRiverRow(worldRow)) return "WATERFRONT";

  // Check proximity to river
  const riverMod = ((worldRow % RIVER_PERIOD) + RIVER_PERIOD) % RIVER_PERIOD;
  if (riverMod >= RIVER_START_OFFSET - 2 && riverMod < RIVER_START_OFFSET)
    return "WATERFRONT";
  if (
    riverMod >= RIVER_START_OFFSET + RIVER_WIDTH &&
    riverMod < RIVER_START_OFFSET + RIVER_WIDTH + 2
  )
    return "WATERFRONT";

  // Use a larger period to create zone variety
  const superRow = ((worldRow % 48) + 48) % 48;
  const superCol = ((worldCol % 60) + 60) % 60;

  // Top band: parks
  if (superRow < 5) return "PARK";
  // Government: center-ish blocks
  if (superRow >= 7 && superRow < 14 && superCol >= 20 && superCol < 40)
    return "GOVERNMENT";
  // Commercial: middle
  if (superRow >= 15 && superRow < 28) return "COMMERCIAL";
  // Industrial: lower-middle
  if (superRow >= 34 && superRow < 44) return "INDUSTRIAL";
  // Default to residential
  return "RESIDENTIAL";
}

// ─── Chunk generation ───

export const CHUNK_SIZE = 20; // tiles per chunk side

export interface ChunkData {
  ground: number[][]; // CHUNK_SIZE x CHUNK_SIZE GID array
  buildings: number[][]; // CHUNK_SIZE x CHUNK_SIZE GID array
}

/**
 * Generate a single chunk at chunk coordinates (cx, cy).
 * World coordinates: worldCol = cx * CHUNK_SIZE + localCol, worldRow = cy * CHUNK_SIZE + localRow
 */
export function generateChunk(cx: number, cy: number): ChunkData {
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

  // Pass 1: Lay ground (roads, rivers, grass)
  for (let lr = 0; lr < CHUNK_SIZE; lr++) {
    const wr = cy * CHUNK_SIZE + lr;
    for (let lc = 0; lc < CHUNK_SIZE; lc++) {
      const wc = cx * CHUNK_SIZE + lc;

      if (isRiverRow(wr)) {
        if (isVRoadCol(wc)) {
          // Bridge over river
          const colMod = ((wc % ROAD_PERIOD_H) + ROAD_PERIOD_H) % ROAD_PERIOD_H;
          ground[lr][lc] =
            colMod === VROAD_OFFSET_A ? gid(ROAD_Y_LEFT) : gid(ROAD_Y_RIGHT);
        } else if (isWaterRow(wr)) {
          ground[lr][lc] = gid(WATER_FULL);
        } else {
          ground[lr][lc] = gid(RIVER_EDGE_H);
        }
        continue;
      }

      const hRoad = isHRoadRow(wr);
      const vRoad = isVRoadCol(wc);

      if (hRoad && vRoad) {
        ground[lr][lc] = gid(ROAD_INTERIOR);
      } else if (hRoad) {
        const rowMod = ((wr % ROAD_PERIOD_V) + ROAD_PERIOD_V) % ROAD_PERIOD_V;
        ground[lr][lc] =
          rowMod === ROAD_OFFSET_A ? gid(ROAD_X_TOP) : gid(ROAD_X_BOTTOM);
      } else if (vRoad) {
        const colMod = ((wc % ROAD_PERIOD_H) + ROAD_PERIOD_H) % ROAD_PERIOD_H;
        ground[lr][lc] =
          colMod === VROAD_OFFSET_A ? gid(ROAD_Y_LEFT) : gid(ROAD_Y_RIGHT);
      }
    }
  }

  // Pass 2: Place buildings in non-road, non-river areas
  // We process local cells and try to fit buildings
  const placed = new Set<string>();

  function isLocalFree(lr: number, lc: number, h: number, w: number): boolean {
    for (let dr = 0; dr < h; dr++) {
      for (let dc = 0; dc < w; dc++) {
        const r = lr + dr;
        const c = lc + dc;
        if (r >= CHUNK_SIZE || c >= CHUNK_SIZE) return false;
        const wr = cy * CHUNK_SIZE + r;
        const wc = cx * CHUNK_SIZE + c;
        if (isRoad(wr, wc) || isRiverRow(wr)) return false;
        if (buildings[r][c] !== 0) return false;
        if (placed.has(`${r},${c}`)) return false;
      }
    }
    return true;
  }

  function placeLocal(group: number[][], lr: number, lc: number): boolean {
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

  // Determine predominant zone for this chunk
  const centerWR = cy * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2);
  const centerWC = cx * CHUNK_SIZE + Math.floor(CHUNK_SIZE / 2);
  const zone = getZone(centerWR, centerWC);

  const palettes: Record<Zone, number[][][]> = {
    PARK: [],
    GOVERNMENT: [HOSPITAL, CONCRETE_BLDG, SHOP1, SHOP2],
    COMMERCIAL: [CONCRETE_BLDG, LONG_SHOP, SHOP1, SHOP2, HOUSE],
    RESIDENTIAL: [HOUSE, SHOP2, HOUSE, HOUSE],
    INDUSTRIAL: [FACTORY, FACTORY, LONG_SHOP, HOUSE],
    WATERFRONT: [SHOP2, HOUSE, LONG_SHOP],
  };

  if (zone === "PARK") {
    // Scatter trees and rocks
    for (let lr = 0; lr < CHUNK_SIZE - 1; lr += 2) {
      for (let lc = 0; lc < CHUNK_SIZE - 1; lc += 2) {
        const wr = cy * CHUNK_SIZE + lr;
        const wc = cx * CHUNK_SIZE + lc;
        if (isRoad(wr, wc) || isRiverRow(wr)) continue;
        if (!isLocalFree(lr, lc, 2, 2)) continue;

        const roll = rng.next();
        if (roll < 0.45) {
          placeLocal(TREE, lr, lc);
        } else if (roll < 0.6) {
          placeLocal(ROCK, lr, lc);
        }
      }
    }
  } else {
    const palette = palettes[zone];
    if (palette.length > 0) {
      const shuffled = rng.shuffle(palette);

      // Pack buildings with 1-tile sidewalk margin from chunk edges
      let lr = 1;
      while (lr < CHUNK_SIZE - 1) {
        let lc = 1;
        let rowAdvance = 1;
        while (lc < CHUNK_SIZE - 1) {
          const wr = cy * CHUNK_SIZE + lr;
          const wc = cx * CHUNK_SIZE + lc;
          if (isRoad(wr, wc) || isRiverRow(wr)) {
            lc++;
            continue;
          }

          let didPlace = false;
          for (const bldg of shuffled) {
            const bH = bldg.length;
            const bW = bldg[0].length;
            if (placeLocal(bldg, lr, lc)) {
              lc += bW;
              rowAdvance = Math.max(rowAdvance, bH);
              didPlace = true;
              break;
            }
          }
          if (!didPlace) {
            // Try parking in commercial/industrial zones
            if (
              (zone === "COMMERCIAL" || zone === "INDUSTRIAL") &&
              lc + 1 < CHUNK_SIZE &&
              isLocalFree(lr, lc, 1, 2)
            ) {
              buildings[lr][lc] = gid(PARKING_L);
              buildings[lr][lc + 1] = gid(PARKING_R);
              ground[lr][lc] = gid(CONCRETE_FLOOR_L);
              ground[lr][lc + 1] = gid(CONCRETE_FLOOR_R);
              placed.add(`${lr},${lc}`);
              placed.add(`${lr},${lc + 1}`);
              lc += 2;
            } else {
              lc++;
            }
          }
        }
        lr += rowAdvance;
      }
    }
  }

  return { ground, buildings };
}
