#!/usr/bin/env node
/**
 * Procedural city map generator for GemeindeSim (80x60).
 * Tileset: CCity_mockup.png (640x256, 40 cols x 16 rows, 16x16 tiles)
 *
 * ALL building placements are procedural — no hardcoded positions.
 * The generator:
 *   1. Defines a road grid (H + V roads)
 *   2. Computes rectangular city blocks between roads
 *   3. Assigns a zone to each block based on its position
 *   4. Fills each block procedurally with zone-appropriate buildings
 *   5. Adds rivers with bridges, crossings at intersections, parks
 *
 * Tiled JSON uses GID = tile_index + 1 (firstgid=1). GID 0 = empty.
 */

const fs = require("fs");
const path = require("path");

// ─── Map constants ───
const MAP_COLS = 80;
const MAP_ROWS = 60;
const TILE_SIZE = 16;

function gid(tileIndex) {
  return tileIndex + 1;
}

// ─── Tile IDs (0-indexed) ───

// Ground
const GRASS = 0;
const WATER_FULL = 566;
const RIVER_EDGE_H = 490;
const CONCRETE_FLOOR_L = 290;
const CONCRETE_FLOOR_R = 291;

// Parking
const PARKING_L = 250;
const PARKING_R = 251;

// Roads
const ROAD_X_TOP = 350;
const ROAD_X_BOTTOM = 390;
const ROAD_INTERIOR = 354;
const ROAD_Y_LEFT = 194;
const ROAD_Y_RIGHT = 195;

// Crossings
const CROSSING_X_L = 282;
const CROSSING_X_R = 283;
const CROSSING_Y_RIGHT_TOP = 321;
const CROSSING_Y_RIGHT_BOT = 361;
const CROSSING_Y_LEFT_TOP = 324;
const CROSSING_Y_LEFT_BOT = 364;

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

// ─── Seeded PRNG (deterministic maps) ───
let _seed = 42;
function rand() {
  _seed = (_seed * 16807 + 0) % 2147483647;
  return (_seed - 1) / 2147483646;
}
function randInt(min, max) {
  return Math.floor(rand() * (max - min + 1)) + min;
}
function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = randInt(0, i);
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// ─── Grid helpers ───
function make2D(rows, cols, fill) {
  return Array.from({ length: rows }, () => Array(cols).fill(fill));
}

const ground = make2D(MAP_ROWS, MAP_COLS, gid(GRASS));
const buildings = make2D(MAP_ROWS, MAP_COLS, 0);

// ─── 1. Road grid ───
const H_ROAD_PAIRS = [
  [5, 6],
  [13, 14],
  [21, 22],
  [37, 38],
  [45, 46],
  [53, 54],
];

const V_ROAD_PAIRS = [
  [9, 10],
  [24, 25],
  [39, 40],
  [54, 55],
  [69, 70],
];

const hRoadSet = new Set();
for (const [a, b] of H_ROAD_PAIRS) {
  hRoadSet.add(a);
  hRoadSet.add(b);
}
const vRoadSet = new Set();
for (const [a, b] of V_ROAD_PAIRS) {
  vRoadSet.add(a);
  vRoadSet.add(b);
}

function isHRoadRow(r) {
  return hRoadSet.has(r);
}
function isVRoadCol(c) {
  return vRoadSet.has(c);
}
function isRoad(r, c) {
  return isHRoadRow(r) || isVRoadCol(c);
}

// ─── 2. Rivers ───
const RIVER1_EDGE_TOP = 29;
const RIVER1_WATER_START = 30;
const RIVER1_WATER_END = 32;
const RIVER1_EDGE_BOTTOM = 33;

const RIVER2_EDGE_TOP = 50;
const RIVER2_WATER_START = 51;
const RIVER2_WATER_END = 51;
const RIVER2_EDGE_BOTTOM = 52;

function isRiverRow(r) {
  return (
    (r >= RIVER1_EDGE_TOP && r <= RIVER1_EDGE_BOTTOM) ||
    (r >= RIVER2_EDGE_TOP && r <= RIVER2_EDGE_BOTTOM)
  );
}
function isWaterRow(r) {
  return (
    (r >= RIVER1_WATER_START && r <= RIVER1_WATER_END) ||
    (r >= RIVER2_WATER_START && r <= RIVER2_WATER_END)
  );
}
function isRiverBank(r) {
  return (
    r === RIVER1_EDGE_TOP - 1 ||
    r === RIVER1_EDGE_BOTTOM + 1 ||
    r === RIVER2_EDGE_TOP - 1 ||
    r === RIVER2_EDGE_BOTTOM + 1
  );
}

// ─── 3. Compute city blocks ───
// A block is a rectangular region between roads (and map edges), excluding rivers.

function computeBlocks() {
  // Collect sorted unique horizontal road rows and vertical road cols
  const hRows = [...hRoadSet].sort((a, b) => a - b);
  const vCols = [...vRoadSet].sort((a, b) => a - b);

  // Row ranges: gaps between horizontal roads
  const rowRanges = [];
  let prevR = 0;
  for (const hr of hRows) {
    if (hr > prevR) rowRanges.push([prevR, hr - 1]);
    prevR = hr + 1;
  }
  if (prevR < MAP_ROWS) rowRanges.push([prevR, MAP_ROWS - 1]);

  // Col ranges: gaps between vertical roads
  const colRanges = [];
  let prevC = 0;
  for (const vc of vCols) {
    if (vc > prevC) colRanges.push([prevC, vc - 1]);
    prevC = vc + 1;
  }
  if (prevC < MAP_COLS) colRanges.push([prevC, MAP_COLS - 1]);

  // Cross product: every row range x col range = a block
  const blocks = [];
  for (const [r1, r2] of rowRanges) {
    for (const [c1, c2] of colRanges) {
      // Skip blocks that are entirely inside a river
      let allRiver = true;
      for (let r = r1; r <= r2; r++) {
        if (!isRiverRow(r)) {
          allRiver = false;
          break;
        }
      }
      if (allRiver) continue;

      blocks.push({ r1, c1, r2, c2, zone: null });
    }
  }
  return blocks;
}

// ─── 4. Zone assignment ───
const ZONE = {
  PARK: "PARK",
  GOVERNMENT: "GOVERNMENT",
  COMMERCIAL: "COMMERCIAL",
  RESIDENTIAL: "RESIDENTIAL",
  INDUSTRIAL: "INDUSTRIAL",
  WATERFRONT: "WATERFRONT",
};

function assignZones(blocks) {
  const centerCol = MAP_COLS / 2; // 40

  // Find the largest block in the upper-center area for government
  let bestGovBlock = null;
  let bestGovArea = 0;
  for (const b of blocks) {
    const midC = (b.c1 + b.c2) / 2;
    const midR = (b.r1 + b.r2) / 2;
    if (midR >= 7 && midR <= 12 && Math.abs(midC - centerCol) < 20) {
      const area = (b.r2 - b.r1 + 1) * (b.c2 - b.c1 + 1);
      if (area > bestGovArea) {
        bestGovArea = area;
        bestGovBlock = b;
      }
    }
  }

  for (const b of blocks) {
    const midR = (b.r1 + b.r2) / 2;
    const midC = (b.c1 + b.c2) / 2;

    // Parks: top and bottom rows
    if (b.r2 <= 4) {
      b.zone = ZONE.PARK;
    } else if (b.r1 >= 55) {
      b.zone = ZONE.PARK;
    }
    // Government: the chosen center block
    else if (b === bestGovBlock) {
      b.zone = ZONE.GOVERNMENT;
    }
    // Waterfront: blocks adjacent to rivers
    else if (
      (b.r2 >= RIVER1_EDGE_TOP - 1 && b.r1 <= RIVER1_EDGE_BOTTOM + 1) ||
      (b.r2 >= RIVER2_EDGE_TOP - 1 && b.r1 <= RIVER2_EDGE_BOTTOM + 1)
    ) {
      b.zone = ZONE.WATERFRONT;
    }
    // Industrial: lower-middle area (rows 39-49)
    else if (midR >= 39 && midR <= 49) {
      b.zone = ZONE.INDUSTRIAL;
    }
    // Commercial: middle rows, especially near center columns
    else if (midR >= 15 && midR <= 28 && Math.abs(midC - centerCol) < 30) {
      b.zone = ZONE.COMMERCIAL;
    }
    // Residential: everything else in the upper half with government zone
    else if (midR >= 7 && midR <= 14) {
      b.zone = ZONE.RESIDENTIAL;
    }
    // Default remaining middle blocks
    else if (midR >= 15 && midR <= 36) {
      b.zone = ZONE.COMMERCIAL;
    } else if (midR >= 39 && midR <= 54) {
      b.zone = ZONE.RESIDENTIAL;
    } else {
      b.zone = ZONE.RESIDENTIAL;
    }
  }
}

// ─── 5. Building placement helpers ───

function placeGroup(layer, group, topRow, leftCol) {
  for (let dr = 0; dr < group.length; dr++) {
    for (let dc = 0; dc < group[dr].length; dc++) {
      const r = topRow + dr;
      const c = leftCol + dc;
      if (r >= 0 && r < MAP_ROWS && c >= 0 && c < MAP_COLS) {
        layer[r][c] = gid(group[dr][dc]);
      }
    }
  }
}

function areaFree(topRow, leftCol, height, width) {
  for (let dr = 0; dr < height; dr++) {
    for (let dc = 0; dc < width; dc++) {
      const r = topRow + dr;
      const c = leftCol + dc;
      if (r < 0 || r >= MAP_ROWS || c < 0 || c >= MAP_COLS) return false;
      if (buildings[r][c] !== 0) return false;
      if (isRoad(r, c)) return false;
      if (isRiverRow(r)) return false;
    }
  }
  return true;
}

// Fill concrete floor (ground layer) in a 1x2 pair pattern
function fillConcreteGround(r, c) {
  if (c + 1 < MAP_COLS) {
    ground[r][c] = gid(CONCRETE_FLOOR_L);
    ground[r][c + 1] = gid(CONCRETE_FLOOR_R);
  }
}

// Place parking (1x2 pair) on buildings layer
function placeParking(r, c) {
  if (c + 1 < MAP_COLS && buildings[r][c] === 0 && buildings[r][c + 1] === 0) {
    buildings[r][c] = gid(PARKING_L);
    buildings[r][c + 1] = gid(PARKING_R);
    fillConcreteGround(r, c);
    return true;
  }
  return false;
}

// ─── 6. Procedural block filling ───

// Building palettes per zone
const ZONE_PALETTES = {
  [ZONE.GOVERNMENT]: [HOSPITAL, CONCRETE_BLDG, SHOP1, SHOP2],
  [ZONE.COMMERCIAL]: [CONCRETE_BLDG, LONG_SHOP, SHOP1, SHOP2, HOUSE],
  [ZONE.RESIDENTIAL]: [HOUSE, SHOP2, HOUSE, HOUSE], // weighted toward houses
  [ZONE.INDUSTRIAL]: [FACTORY, FACTORY, LONG_SHOP, HOUSE],
  [ZONE.WATERFRONT]: [SHOP2, HOUSE, LONG_SHOP],
};

function fillBlock(block) {
  const { r1, c1, r2, c2, zone } = block;
  const blockH = r2 - r1 + 1;
  const blockW = c2 - c1 + 1;

  if (zone === ZONE.PARK) {
    fillPark(r1, c1, r2, c2);
    return;
  }

  if (zone === ZONE.WATERFRONT) {
    fillWaterfront(r1, c1, r2, c2);
    return;
  }

  const palette = ZONE_PALETTES[zone];
  if (!palette) return;

  // 1-tile sidewalk border (leave as grass — it reads as a sidewalk gap)
  const innerR1 = r1 + 1;
  const innerC1 = c1 + 1;
  const innerR2 = r2 - 1;
  const innerC2 = c2 - 1;

  if (innerR2 < innerR1 || innerC2 < innerC1) return;

  // For government zone, place hospitals first
  if (zone === ZONE.GOVERNMENT) {
    fillGovernment(innerR1, innerC1, innerR2, innerC2);
    return;
  }

  // Pack buildings left-to-right, top-to-bottom
  packBuildings(innerR1, innerC1, innerR2, innerC2, palette, zone);
}

function fillGovernment(r1, c1, r2, c2) {
  const midC = Math.floor((c1 + c2) / 2);

  // Place 1-2 hospitals in the center
  let hospitalsPlaced = 0;
  for (
    let startC = midC - 6;
    startC <= midC + 2 && hospitalsPlaced < 2;
    startC += 5
  ) {
    if (areaFree(r1, startC, 4, 4)) {
      placeGroup(buildings, HOSPITAL, r1, startC);
      hospitalsPlaced++;
    }
  }

  // Place concrete buildings as office towers flanking hospitals
  for (let c = c1; c <= c2 - 3; c += 5) {
    if (areaFree(r1, c, 4, 4)) {
      placeGroup(buildings, CONCRETE_BLDG, r1, c);
    }
  }

  // Fill remaining space with Shop1 (tall government buildings)
  packBuildings(r1, c1, r2, c2, [SHOP1, SHOP2, HOUSE], ZONE.GOVERNMENT);
}

function fillPark(r1, c1, r2, c2) {
  // Re-seed PRNG per block so each park is unique
  _seed = (r1 * 1000 + c1 * 37 + 42) % 2147483647;
  // Scatter trees and rocks with minimum 1-tile spacing
  for (let r = r1; r <= r2 - 1; r += 2) {
    for (let c = c1; c <= c2 - 1; c += 2) {
      if (isRoad(r, c) || isRiverRow(r)) continue;
      if (!areaFree(r, c, 2, 2)) continue;

      const roll = rand();
      if (roll < 0.45) {
        placeGroup(buildings, TREE, r, c);
      } else if (roll < 0.6) {
        placeGroup(buildings, ROCK, r, c);
      }
      // else: leave as open grass
    }
  }

  // Scatter a few concrete plazas (2-wide concrete floor on ground)
  const plazaCount = Math.floor((c2 - c1) / 12);
  for (let i = 0; i < plazaCount; i++) {
    const pr = randInt(r1, r2);
    const pc = randInt(c1, Math.max(c1, c2 - 3));
    if (!isRoad(pr, pc) && !isRiverRow(pr) && pc + 1 <= c2) {
      fillConcreteGround(pr, pc);
      if (pc + 2 <= c2) fillConcreteGround(pr, pc + 2);
    }
  }
}

function fillWaterfront(r1, c1, r2, c2) {
  const innerR1 = r1 + 1;
  const innerC1 = c1;
  const innerR2 = r2 - 1;
  const innerC2 = c2;

  if (innerR2 < innerR1 || innerC2 < innerC1) return;

  // Concrete floor strip along the riverbank
  for (let r = innerR1; r <= innerR2; r++) {
    if (isRiverRow(r) || isRoad(r, 0)) continue;
    for (let c = innerC1; c <= innerC2 - 1; c += 2) {
      if (isVRoadCol(c) || isVRoadCol(c + 1)) continue;
      fillConcreteGround(r, c);
    }
  }

  // Place parking lots and small shops
  for (let r = innerR1; r <= innerR2 - 1; r += 2) {
    for (let c = innerC1; c <= innerC2 - 1; c += 2) {
      if (isRoad(r, c) || isRiverRow(r)) continue;
      if (!areaFree(r, c, 2, 2)) continue;

      const roll = rand();
      if (roll < 0.35) {
        placeParking(r, c);
        if (r + 1 <= innerR2) placeParking(r + 1, c);
      } else if (roll < 0.55) {
        placeGroup(buildings, SHOP2, r, c);
      } else if (roll < 0.7) {
        placeGroup(buildings, HOUSE, r, c);
      }
      // else: leave as concrete plaza
    }
  }
}

function packBuildings(r1, c1, r2, c2, palette, zone) {
  // Re-seed PRNG per block so each block gets unique buildings
  _seed = (r1 * 1000 + c1 * 37 + 42) % 2147483647;
  // Shuffle palette for variety per block
  const localPalette = shuffle([...palette]);

  let r = r1;
  while (r <= r2) {
    let c = c1;
    let rowAdvance = 1;
    while (c <= c2) {
      if (isRoad(r, c) || isRiverRow(r)) {
        c++;
        continue;
      }

      let placed = false;
      // Try each building in the palette
      for (const bldg of localPalette) {
        const bH = bldg.length;
        const bW = bldg[0].length;
        if (r + bH - 1 <= r2 && c + bW - 1 <= c2 && areaFree(r, c, bH, bW)) {
          placeGroup(buildings, bldg, r, c);
          c += bW;
          rowAdvance = Math.max(rowAdvance, bH);
          placed = true;
          break;
        }
      }

      if (!placed) {
        // Try filling small gaps with parking or concrete
        if (c + 1 <= c2 && areaFree(r, c, 1, 2)) {
          if (zone === ZONE.COMMERCIAL || zone === ZONE.INDUSTRIAL) {
            placeParking(r, c);
            c += 2;
          } else {
            c++;
          }
        } else {
          c++;
        }
      }
    }
    r += rowAdvance;
  }
}

// ─── GENERATE ───

// Step 1: Lay roads on ground layer
for (let r = 0; r < MAP_ROWS; r++) {
  for (let c = 0; c < MAP_COLS; c++) {
    if (isRiverRow(r)) continue;

    const hRoad = isHRoadRow(r);
    const vRoad = isVRoadCol(c);

    if (hRoad && vRoad) {
      // Intersection: use interior road tile
      ground[r][c] = gid(ROAD_INTERIOR);
    } else if (hRoad) {
      const isTopLane = H_ROAD_PAIRS.some(([a]) => r === a);
      ground[r][c] = isTopLane ? gid(ROAD_X_TOP) : gid(ROAD_X_BOTTOM);
    } else if (vRoad) {
      const isLeftLane = V_ROAD_PAIRS.some(([a]) => c === a);
      ground[r][c] = isLeftLane ? gid(ROAD_Y_LEFT) : gid(ROAD_Y_RIGHT);
    }
  }
}

// Step 2: Rivers (crossings removed — clean roads look better)
function layRiverRow(r, tileId) {
  for (let c = 0; c < MAP_COLS; c++) {
    if (isVRoadCol(c)) {
      // Bridge
      const isLeftLane = V_ROAD_PAIRS.some(([a]) => c === a);
      ground[r][c] = isLeftLane ? gid(ROAD_Y_LEFT) : gid(ROAD_Y_RIGHT);
    } else {
      ground[r][c] = gid(tileId);
    }
  }
}

layRiverRow(RIVER1_EDGE_TOP, RIVER_EDGE_H);
for (let r = RIVER1_WATER_START; r <= RIVER1_WATER_END; r++) {
  layRiverRow(r, WATER_FULL);
}
layRiverRow(RIVER1_EDGE_BOTTOM, RIVER_EDGE_H);

layRiverRow(RIVER2_EDGE_TOP, RIVER_EDGE_H);
layRiverRow(RIVER2_WATER_START, WATER_FULL);
layRiverRow(RIVER2_EDGE_BOTTOM, RIVER_EDGE_H);

// Step 4: Compute blocks, assign zones, fill
const blocks = computeBlocks();
assignZones(blocks);

for (const block of blocks) {
  fillBlock(block);
}

// Step 5: Riverbank decoration — trees along banks where buildings layer is empty
function decorateRiverbank(bankRow) {
  for (let c = 0; c < MAP_COLS - 1; c += 3) {
    if (isVRoadCol(c) || isVRoadCol(c + 1)) continue;
    if (
      buildings[bankRow][c] === 0 &&
      buildings[bankRow][c + 1] === 0 &&
      !isRoad(bankRow, c) &&
      !isRiverRow(bankRow)
    ) {
      if (rand() < 0.5) {
        buildings[bankRow][c] = gid(TREE[0][0]);
        buildings[bankRow][c + 1] = gid(TREE[0][1]);
      }
    }
  }
}

decorateRiverbank(RIVER1_EDGE_TOP - 1);
decorateRiverbank(RIVER1_EDGE_BOTTOM + 1);
decorateRiverbank(RIVER2_EDGE_TOP - 1);
decorateRiverbank(RIVER2_EDGE_BOTTOM + 1);

// ─── Flatten to row-major 1D arrays ───
const groundData = [];
const buildingsData = [];

for (let r = 0; r < MAP_ROWS; r++) {
  for (let c = 0; c < MAP_COLS; c++) {
    groundData.push(ground[r][c]);
    buildingsData.push(buildings[r][c]);
  }
}

// ─── Build Tiled JSON ───
const tiledMap = {
  compressionlevel: -1,
  width: MAP_COLS,
  height: MAP_ROWS,
  tilewidth: TILE_SIZE,
  tileheight: TILE_SIZE,
  orientation: "orthogonal",
  renderorder: "right-down",
  type: "map",
  version: "1.10",
  tiledversion: "1.10.2",
  infinite: false,
  nextlayerid: 3,
  nextobjectid: 1,
  layers: [
    {
      id: 1,
      name: "ground",
      type: "tilelayer",
      width: MAP_COLS,
      height: MAP_ROWS,
      x: 0,
      y: 0,
      opacity: 1,
      visible: true,
      data: groundData,
    },
    {
      id: 2,
      name: "buildings",
      type: "tilelayer",
      width: MAP_COLS,
      height: MAP_ROWS,
      x: 0,
      y: 0,
      opacity: 1,
      visible: true,
      data: buildingsData,
    },
  ],
  tilesets: [
    {
      columns: 40,
      firstgid: 1,
      image: "../citymap_tilesets/CCity_mockup.png",
      imageheight: 256,
      imagewidth: 640,
      margin: 0,
      name: "urban",
      spacing: 0,
      tilecount: 640,
      tileheight: 16,
      tilewidth: 16,
    },
  ],
};

// ─── Write output ───
const outDir = path.join(__dirname, "..", "public", "assets", "maps");
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const outPath = path.join(outDir, "city.json");
fs.writeFileSync(outPath, JSON.stringify(tiledMap, null, 2));

// ─── Validation ───
console.log(`Map generated: ${outPath}`);
console.log(`Size: ${MAP_COLS}x${MAP_ROWS} = ${MAP_COLS * MAP_ROWS} tiles`);
console.log(`Ground layer: ${groundData.length} tiles`);
console.log(`Buildings layer: ${buildingsData.length} tiles`);

const nonEmptyBuildings = buildingsData.filter((g) => g !== 0).length;
console.log(`Non-empty building tiles: ${nonEmptyBuildings}`);

// Validate GID range [0, 640]
const allGids = [...groundData, ...buildingsData];
const invalidGids = allGids.filter((g) => g < 0 || g > 640);
if (invalidGids.length > 0) {
  console.error(`ERROR: Found ${invalidGids.length} invalid GIDs:`, [
    ...new Set(invalidGids),
  ]);
  process.exit(1);
} else {
  console.log("All GIDs valid (0-640 range).");
}

if (
  groundData.length !== MAP_COLS * MAP_ROWS ||
  buildingsData.length !== MAP_COLS * MAP_ROWS
) {
  console.error("ERROR: Data array length mismatch!");
  process.exit(1);
}

// Zone stats
const zoneCounts = {};
for (const b of blocks) {
  const area = (b.r2 - b.r1 + 1) * (b.c2 - b.c1 + 1);
  zoneCounts[b.zone] = (zoneCounts[b.zone] || 0) + area;
}
console.log("Zone distribution (tiles):", zoneCounts);

const waterTiles = groundData.filter((g) => g === gid(WATER_FULL)).length;
const edgeTiles = groundData.filter((g) => g === gid(RIVER_EDGE_H)).length;
console.log(`River: ${waterTiles} water, ${edgeTiles} edge tiles`);

const crossingTiles = groundData.filter(
  (g) =>
    g === gid(CROSSING_X_L) ||
    g === gid(CROSSING_X_R) ||
    g === gid(CROSSING_Y_RIGHT_TOP) ||
    g === gid(CROSSING_Y_RIGHT_BOT) ||
    g === gid(CROSSING_Y_LEFT_TOP) ||
    g === gid(CROSSING_Y_LEFT_BOT),
).length;
console.log(`Crossing tiles: ${crossingTiles}`);

console.log("Validation passed.");
