/**
 * Generates citypack-city.json — a hand-crafted Tiled JSON city map for GemeindeSim.
 * Run: node scripts/generate-citypack-map.js
 *
 * Map: 100 cols x 80 rows, 16x16 tiles
 * Tileset: citypack.png (64 cols, 4096 tiles, firstgid=1)
 *
 * Tile IDs are 1-indexed GIDs matching CitypackRegistry.ts
 */
const fs = require("fs");
const path = require("path");

const W = 100;
const H = 80;

// ─── Tile GIDs (from CitypackRegistry.ts) ───────────────────────────────────

const GRASS = 3270;
const ROAD_BLANK = 2436; // intersection / plain road
const ROAD_DASH_H = 2438; // horizontal dashed center line
const ROAD_DASH_V = 2440; // vertical dashed center line

// Dirt 3x3 patch tiles
const DIRT_TL = 3087;
const DIRT_T = 3089;
const DIRT_TR = 3091;
const DIRT_L = 3215;
const DIRT_C = 3217;
const DIRT_R = 3219;
const DIRT_BL = 3343;
const DIRT_B = 3345;
const DIRT_BR = 3347;

// Trees (1w x 2h, canopy on top, trunk on bottom)
const TREE1_CANOPY = 2073;
const TREE1_TRUNK = 2137;
const TREE2_CANOPY = 2075;
const TREE2_TRUNK = 2139;

// Buildings (GIDs from registry — each is [row][col])
const OFFICE1 = [
  [131, 132, 133],
  [195, 196, 197],
  [259, 260, 261],
  [323, 324, 325],
  [387, 388, 389],
  [451, 452, 453],
]; // 3w x 6h

const OFFICE2 = [
  [136, 137, 138],
  [200, 201, 202],
  [264, 265, 266],
  [328, 329, 330],
  [392, 393, 394],
  [456, 457, 458],
]; // 3w x 6h

const OFFICE3 = [
  [141, 142, 143],
  [205, 206, 207],
  [269, 270, 271],
  [333, 334, 335],
  [397, 398, 399],
  [461, 462, 463],
]; // 3w x 6h

const OFFICE4 = [
  [1107, 1108, 1109],
  [1171, 1172, 1173],
  [1235, 1236, 1237],
  [1299, 1300, 1301],
  [1363, 1364, 1365],
  [1427, 1428, 1429],
]; // 3w x 6h

const SHOP1 = [
  [706, 707, 708, 709],
  [770, 771, 772, 773],
  [834, 835, 836, 837],
]; // 4w x 3h

const SHOP2 = [
  [712, 713, 714],
  [776, 777, 778],
  [840, 841, 842],
]; // 3w x 3h

const HOUSE1 = [
  [1096, 1097, 1098],
  [1160, 1161, 1162],
  [1224, 1225, 1226],
]; // 3w x 3h

// ─── Seeded RNG (deterministic) ─────────────────────────────────────────────

function mulberry32(seed) {
  let s = seed | 0;
  return function () {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rng = mulberry32(42);

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// ─── Layer arrays ───────────────────────────────────────────────────────────

const terrain = new Array(W * H).fill(0);
const objects = new Array(W * H).fill(0);

function setTerrain(col, row, gid) {
  if (col >= 0 && col < W && row >= 0 && row < H) {
    terrain[row * W + col] = gid;
  }
}

function setObject(col, row, gid) {
  if (col >= 0 && col < W && row >= 0 && row < H) {
    objects[row * W + col] = gid;
  }
}

function getObject(col, row) {
  if (col >= 0 && col < W && row >= 0 && row < H) {
    return objects[row * W + col];
  }
  return -1;
}

function getTerrain(col, row) {
  if (col >= 0 && col < W && row >= 0 && row < H) {
    return terrain[row * W + col];
  }
  return -1;
}

// ─── Road layout ────────────────────────────────────────────────────────────

// 2-tile wide roads
const H_ROAD_PAIRS = [
  [10, 11],
  [24, 25],
  [38, 39],
  [52, 53],
  [66, 67],
];
const V_ROAD_PAIRS = [
  [12, 13],
  [26, 27],
  [40, 41],
  [54, 55],
  [68, 69],
];

const hRoadRows = new Set();
const vRoadCols = new Set();

for (const [r1, r2] of H_ROAD_PAIRS) {
  hRoadRows.add(r1);
  hRoadRows.add(r2);
}
for (const [c1, c2] of V_ROAD_PAIRS) {
  vRoadCols.add(c1);
  vRoadCols.add(c2);
}

function isRoadRow(r) {
  return hRoadRows.has(r);
}
function isRoadCol(c) {
  return vRoadCols.has(c);
}
function isRoad(col, row) {
  return isRoadRow(row) || isRoadCol(col);
}

// ─── Step 1: Fill entire terrain with grass ─────────────────────────────────

for (let r = 0; r < H; r++) {
  for (let c = 0; c < W; c++) {
    setTerrain(c, r, GRASS);
  }
}

// ─── Step 2: Place roads on terrain layer ───────────────────────────────────

for (let r = 0; r < H; r++) {
  for (let c = 0; c < W; c++) {
    const onHRoad = isRoadRow(r);
    const onVRoad = isRoadCol(c);

    if (onHRoad && onVRoad) {
      // Intersection
      setTerrain(c, r, ROAD_BLANK);
    } else if (onHRoad) {
      // Horizontal road segment
      setTerrain(c, r, ROAD_DASH_H);
    } else if (onVRoad) {
      // Vertical road segment
      setTerrain(c, r, ROAD_DASH_V);
    }
  }
}

// ─── Step 3: Define blocks and zones ────────────────────────────────────────

// Block boundaries (col ranges and row ranges between roads)
// Col blocks: 0=cols 0-11, 1=cols 14-25, 2=cols 28-39, 3=cols 42-53, 4=cols 56-67, 5=cols 70-99
const colBlocks = [
  { start: 0, end: 11 },
  { start: 14, end: 25 },
  { start: 28, end: 39 },
  { start: 42, end: 53 },
  { start: 56, end: 67 },
  { start: 70, end: 99 },
];

// Row blocks: 0=rows 0-9, 1=rows 12-23, 2=rows 26-37, 3=rows 40-51, 4=rows 54-65, 5=rows 68-79
const rowBlocks = [
  { start: 0, end: 9 },
  { start: 12, end: 23 },
  { start: 26, end: 37 },
  { start: 40, end: 51 },
  { start: 54, end: 65 },
  { start: 68, end: 79 },
];

// Zone assignments [rowBlock][colBlock]
const ZONE_MAP = [
  ["PARK", "PARK", "RESIDENTIAL", "RESIDENTIAL", "COMMERCIAL", "RESIDENTIAL"],
  ["PARK", "COMMERCIAL", "GOVT", "GOVT", "RESIDENTIAL", "RESIDENTIAL"],
  ["RESIDENTIAL", "COMMERCIAL", "GOVT", "GOVT", "COMMERCIAL", "RESIDENTIAL"],
  [
    "RESIDENTIAL",
    "RESIDENTIAL",
    "GOVT",
    "COMMERCIAL",
    "RESIDENTIAL",
    "RESIDENTIAL",
  ],
  [
    "COMMERCIAL",
    "RESIDENTIAL",
    "RESIDENTIAL",
    "RESIDENTIAL",
    "RESIDENTIAL",
    "COMMERCIAL",
  ],
  [
    "RESIDENTIAL",
    "RESIDENTIAL",
    "COMMERCIAL",
    "COMMERCIAL",
    "RESIDENTIAL",
    "RESIDENTIAL",
  ],
];

// ─── Step 4: Place buildings in each block ──────────────────────────────────

// Building palettes per zone
const GOVT_PALETTE = [OFFICE1, OFFICE2, OFFICE3, OFFICE4];
const COMMERCIAL_PALETTE = [SHOP1, SHOP2, SHOP1, HOUSE1];
const RESIDENTIAL_PALETTE = [HOUSE1, HOUSE1, SHOP2];

function getBuildingPalette(zone) {
  switch (zone) {
    case "GOVT":
      return GOVT_PALETTE;
    case "COMMERCIAL":
      return COMMERCIAL_PALETTE;
    case "RESIDENTIAL":
      return RESIDENTIAL_PALETTE;
    default:
      return [];
  }
}

function buildingWidth(b) {
  return b[0].length;
}
function buildingHeight(b) {
  return b.length;
}

/**
 * Place a building at (col, row) on the objects layer.
 * Returns true if placed successfully (no overlap with existing objects or roads).
 */
function placeBuilding(building, col, row) {
  const bw = buildingWidth(building);
  const bh = buildingHeight(building);

  // Check bounds and overlap
  for (let dr = 0; dr < bh; dr++) {
    for (let dc = 0; dc < bw; dc++) {
      const c = col + dc;
      const r = row + dr;
      if (c >= W || r >= H) return false;
      if (isRoad(c, r)) return false;
      if (getObject(c, r) !== 0) return false;
    }
  }

  // Place tiles
  for (let dr = 0; dr < bh; dr++) {
    for (let dc = 0; dc < bw; dc++) {
      setObject(col + dc, row + dr, building[dr][dc]);
    }
  }
  return true;
}

/**
 * Pack buildings into a block, left-to-right, top-to-bottom.
 * Margin: 1 tile from edges that border a road.
 */
function fillBlock(colBlock, rowBlock, zone) {
  const cb = colBlocks[colBlock];
  const rb = rowBlocks[rowBlock];

  // Determine margins (1 tile from road-adjacent edges)
  const marginTop = rowBlock > 0 ? 1 : 0; // road above if not first row block
  const marginBottom = rowBlock < rowBlocks.length - 1 ? 1 : 0;
  const marginLeft = colBlock > 0 ? 1 : 0;
  const marginRight = colBlock < colBlocks.length - 1 ? 1 : 0;

  const startCol = cb.start + marginLeft;
  const endCol = cb.end - marginRight;
  const startRow = rb.start + marginTop;
  const endRow = rb.end - marginBottom;

  if (zone === "PARK") {
    fillPark(startCol, endCol, startRow, endRow);
    return;
  }

  const palette = getBuildingPalette(zone);
  if (palette.length === 0) return;

  // Create a shuffled/cycled palette for this block
  const blockSeed = colBlock * 7 + rowBlock * 13;
  let paletteIndex = blockSeed % palette.length;

  // Pack buildings row by row
  let curRow = startRow;
  while (curRow <= endRow) {
    let curCol = startCol;
    let rowMaxHeight = 0;
    let placedAny = false;

    while (curCol <= endCol) {
      const building = palette[paletteIndex % palette.length];
      paletteIndex++;

      const bw = buildingWidth(building);
      const bh = buildingHeight(building);

      // Check if building fits
      if (curCol + bw - 1 > endCol || curRow + bh - 1 > endRow) {
        // Try a smaller building
        let placed = false;
        for (const alt of palette) {
          const aw = buildingWidth(alt);
          const ah = buildingHeight(alt);
          if (curCol + aw - 1 <= endCol && curRow + ah - 1 <= endRow) {
            if (placeBuilding(alt, curCol, curRow)) {
              curCol += aw + 1; // 1-tile gap
              rowMaxHeight = Math.max(rowMaxHeight, ah);
              placed = true;
              placedAny = true;
              break;
            }
          }
        }
        if (!placed) {
          curCol++; // skip and try next position
        }
      } else {
        if (placeBuilding(building, curCol, curRow)) {
          curCol += bw + 1; // 1-tile gap
          rowMaxHeight = Math.max(rowMaxHeight, bh);
          placedAny = true;
        } else {
          curCol++;
        }
      }
    }

    if (placedAny && rowMaxHeight > 0) {
      curRow += rowMaxHeight + 1; // 1-tile gap between rows
    } else {
      curRow++;
    }
  }
}

// ─── Step 5: Park filling (trees) ───────────────────────────────────────────

function fillPark(startCol, endCol, startRow, endRow) {
  // Place trees in a grid pattern: every 2 cols, every 3 rows (2-tile tall trees)
  let treeToggle = false;
  for (let r = startRow; r <= endRow - 1; r += 3) {
    for (let c = startCol; c <= endCol; c += 2) {
      if (isRoad(c, r) || isRoad(c, r + 1)) continue;
      if (getObject(c, r) !== 0 || getObject(c, r + 1) !== 0) continue;

      const canopy = treeToggle ? TREE2_CANOPY : TREE1_CANOPY;
      const trunk = treeToggle ? TREE2_TRUNK : TREE1_TRUNK;

      setObject(c, r, canopy);
      setObject(c, r + 1, trunk);
      treeToggle = !treeToggle;
    }
    treeToggle = !treeToggle; // offset checkerboard per row
  }
}

// ─── Step 6: Dirt patches in residential zones ──────────────────────────────

function placeDirtPatch(col, row, pw, ph) {
  // Check all cells are free on terrain (still grass) and no road/object
  for (let dr = 0; dr < ph; dr++) {
    for (let dc = 0; dc < pw; dc++) {
      const c = col + dc;
      const r = row + dr;
      if (c >= W || r >= H) return false;
      if (isRoad(c, r)) return false;
      if (getObject(c, r) !== 0) return false;
      if (getTerrain(c, r) !== GRASS) return false;
    }
  }

  // Place the dirt patch on terrain layer
  for (let dr = 0; dr < ph; dr++) {
    for (let dc = 0; dc < pw; dc++) {
      const c = col + dc;
      const r = row + dr;
      let tile;

      // Determine which dirt tile based on position
      const isTop = dr === 0;
      const isBottom = dr === ph - 1;
      const isLeft = dc === 0;
      const isRight = dc === pw - 1;

      if (isTop && isLeft) tile = DIRT_TL;
      else if (isTop && isRight) tile = DIRT_TR;
      else if (isTop) tile = DIRT_T;
      else if (isBottom && isLeft) tile = DIRT_BL;
      else if (isBottom && isRight) tile = DIRT_BR;
      else if (isBottom) tile = DIRT_B;
      else if (isLeft) tile = DIRT_L;
      else if (isRight) tile = DIRT_R;
      else tile = DIRT_C;

      setTerrain(c, r, tile);
    }
  }
  return true;
}

function scatterDirt(colBlock, rowBlock) {
  const cb = colBlocks[colBlock];
  const rb = rowBlocks[rowBlock];

  // Place 2-3 dirt patches per residential block
  const numPatches = 2 + ((colBlock * 3 + rowBlock * 5) % 2 === 0 ? 1 : 0);

  for (let p = 0; p < numPatches; p++) {
    // Deterministic positions within block
    const offsetCol = Math.floor(
      (cb.end - cb.start) * (0.2 + 0.3 * p) + ((colBlock * 7 + p * 11) % 3),
    );
    const offsetRow = Math.floor(
      (rb.end - rb.start) * (0.3 + 0.2 * p) + ((rowBlock * 5 + p * 7) % 3),
    );

    const patchCol = cb.start + (offsetCol % (cb.end - cb.start - 2));
    const patchRow = rb.start + (offsetRow % (rb.end - rb.start - 2));

    // Alternate 3x3 and 4x3 patches
    const pw = p % 2 === 0 ? 3 : 4;
    const ph = 3;

    placeDirtPatch(patchCol, patchRow, pw, ph);
  }
}

// ─── Execute generation ─────────────────────────────────────────────────────

// Fill all blocks with buildings/parks
for (let rb = 0; rb < rowBlocks.length; rb++) {
  for (let cb = 0; cb < colBlocks.length; cb++) {
    const zone = ZONE_MAP[rb][cb];
    fillBlock(cb, rb, zone);
  }
}

// Scatter dirt in residential blocks
for (let rb = 0; rb < rowBlocks.length; rb++) {
  for (let cb = 0; cb < colBlocks.length; cb++) {
    if (ZONE_MAP[rb][cb] === "RESIDENTIAL") {
      scatterDirt(cb, rb);
    }
  }
}

// ─── Build Tiled JSON ───────────────────────────────────────────────────────

const map = {
  compressionlevel: -1,
  height: H,
  width: W,
  infinite: false,
  tileheight: 16,
  tilewidth: 16,
  orientation: "orthogonal",
  renderorder: "right-down",
  type: "map",
  version: "1.10",
  tiledversion: "1.12.1",
  nextlayerid: 3,
  nextobjectid: 1,
  layers: [
    {
      id: 1,
      name: "Terrain",
      type: "tilelayer",
      width: W,
      height: H,
      x: 0,
      y: 0,
      opacity: 1,
      visible: true,
      data: terrain,
    },
    {
      id: 2,
      name: "Objects",
      type: "tilelayer",
      width: W,
      height: H,
      x: 0,
      y: 0,
      opacity: 1,
      visible: true,
      data: objects,
    },
  ],
  tilesets: [
    {
      columns: 64,
      firstgid: 1,
      image: "citypack.png",
      imageheight: 1024,
      imagewidth: 1024,
      margin: 0,
      name: "citypack",
      spacing: 0,
      tilecount: 4096,
      tileheight: 16,
      tilewidth: 16,
    },
  ],
};

const outPath = path.join(
  __dirname,
  "../public/assets/maps/citypack-city.json",
);
fs.writeFileSync(outPath, JSON.stringify(map));

const stats = fs.statSync(outPath);
const sizeKB = (stats.size / 1024).toFixed(1);
console.log(`Generated citypack-city.json (${sizeKB} KB)`);

// ─── Stats ──────────────────────────────────────────────────────────────────

let roadCount = 0;
let grassCount = 0;
let dirtCount = 0;
let objectCount = 0;

for (let i = 0; i < W * H; i++) {
  const t = terrain[i];
  if (t === ROAD_BLANK || t === ROAD_DASH_H || t === ROAD_DASH_V) roadCount++;
  else if (t === GRASS) grassCount++;
  else dirtCount++;
  if (objects[i] !== 0) objectCount++;
}

console.log(
  `Terrain: ${roadCount} road, ${grassCount} grass, ${dirtCount} dirt tiles`,
);
console.log(`Objects: ${objectCount} building/tree tiles`);
