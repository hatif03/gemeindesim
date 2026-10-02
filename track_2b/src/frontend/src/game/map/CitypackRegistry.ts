/**
 * Citypack tileset tile ID registry.
 * Tileset: citypack.png — 16×16px tiles, 64 columns wide, margin=0, spacing=0
 * Asset path: /assets/maps/citypack.png
 * IDs are 0-indexed (same as CCity). GID = tileIndex + 1 when used in Tiled JSON or putTileAt.
 */

// ─── Roads ───────────────────────────────────────────────────────────────────

export const SEWER = 2433;
export const ROAD_BLANK = 2435;
export const ROAD_DASH_H = 2437; // dashed center line, horizontal (x-axis)
export const ROAD_DASH_V = 2439; // dashed center line, vertical (y-axis)
export const ROAD_CURVE_BR = 2441; // curve: bottom-right corner
export const ROAD_EDGE_RIGHT = 2565; // edge on right side
export const ROAD_EDGE_BOTH = 2567; // edge on both left and right sides
export const ROAD_EDGE_LEFT = 2569; // edge on left side

/**
 * Road tile GIDs (0-indexed ID + 1) — matches values returned by
 * getGroundGrid (Phaser tile.index = GID) and the procedural generator (gid()).
 */
export const ROAD_TILES = new Set([
  ROAD_BLANK + 1,
  ROAD_DASH_H + 1,
  ROAD_DASH_V + 1,
  ROAD_CURVE_BR + 1,
  ROAD_EDGE_RIGHT + 1,
  ROAD_EDGE_BOTH + 1,
  ROAD_EDGE_LEFT + 1,
]);

// ─── Ground ───────────────────────────────────────────────────────────────────

export const GRASS = 3269; // plain green

/**
 * Dirt tiles — 3×3 corner/edge/center set.
 * Can tile any rectangle; repeat interior row/col for larger patches.
 * [row][col] — (0,0) = top-left corner, (2,2) = bottom-right corner.
 */
export const DIRT = [
  [3086, 3088, 3090], // top:    TL corner, top edge,    TR corner
  [3214, 3216, 3218], // middle: left edge, center fill, right edge
  [3342, 3344, 3346], // bottom: BL corner, bot edge,    BR corner
] as const;

export const DIRT_TL = DIRT[0][0];
export const DIRT_T = DIRT[0][1];
export const DIRT_TR = DIRT[0][2];
export const DIRT_L = DIRT[1][0];
export const DIRT_C = DIRT[1][1]; // center fill (use for any interior cell)
export const DIRT_R = DIRT[1][2];
export const DIRT_BL = DIRT[2][0];
export const DIRT_B = DIRT[2][1];
export const DIRT_BR = DIRT[2][2];

// ─── Trees (overlay on grass — second layer) ──────────────────────────────────

/**
 * Trees are 1-wide × 2-tall. Place TRUNK on Objects layer, CANOPY on same col above.
 * Ground layer under both cells should be GRASS.
 */
export const TREE1_CANOPY = 2072; // row 0 (top)
export const TREE1_TRUNK = 2136; // row 1 (bottom)

export const TREE2_CANOPY = 2074;
export const TREE2_TRUNK = 2138;

// ─── Buildings ────────────────────────────────────────────────────────────────

/**
 * Multi-tile buildings. Each is a 2D array [row][col] of tile IDs.
 * Anchor = top-left cell. Width = cols, Height = rows.
 * Place on Objects/Buildings layer above ground.
 */

export const OFFICE1 = [
  [130, 131, 132],
  [194, 195, 196],
  [258, 259, 260],
  [322, 323, 324],
  [386, 387, 388],
  [450, 451, 452],
] as const; // 3 wide × 6 tall

export const OFFICE2 = [
  [135, 136, 137],
  [199, 200, 201],
  [263, 264, 265],
  [327, 328, 329],
  [391, 392, 393],
  [455, 456, 457],
] as const; // 3 wide × 6 tall

export const OFFICE3 = [
  [140, 141, 142],
  [204, 205, 206],
  [268, 269, 270],
  [332, 333, 334],
  [396, 397, 398],
  [460, 461, 462],
] as const; // 3 wide × 6 tall

export const OFFICE4 = [
  [1106, 1107, 1108],
  [1170, 1171, 1172],
  [1234, 1235, 1236],
  [1298, 1299, 1300],
  [1362, 1363, 1364],
  [1426, 1427, 1428],
] as const; // 3 wide × 6 tall

export const SHOP1 = [
  [705, 706, 707, 708],
  [769, 770, 771, 772],
  [833, 834, 835, 836],
] as const; // 4 wide × 3 tall

export const SHOP2 = [
  [711, 712, 713],
  [775, 776, 777],
  [839, 840, 841],
] as const; // 3 wide × 3 tall

export const HOUSE1 = [
  [1095, 1096, 1097],
  [1159, 1160, 1161],
  [1223, 1224, 1225],
] as const; // 3 wide × 3 tall

// ─── Building catalogue (for procedural placement) ───────────────────────────

export type BuildingTemplate = {
  id: string;
  tiles: readonly (readonly number[])[];
  cols: number;
  rows: number;
  zone: "government" | "commercial" | "residential";
};

export const BUILDINGS: BuildingTemplate[] = [
  { id: "office1", tiles: OFFICE1, cols: 3, rows: 6, zone: "government" },
  { id: "office2", tiles: OFFICE2, cols: 3, rows: 6, zone: "government" },
  { id: "office3", tiles: OFFICE3, cols: 3, rows: 6, zone: "government" },
  { id: "office4", tiles: OFFICE4, cols: 3, rows: 6, zone: "government" },
  { id: "shop1", tiles: SHOP1, cols: 4, rows: 3, zone: "commercial" },
  { id: "shop2", tiles: SHOP2, cols: 3, rows: 3, zone: "commercial" },
  { id: "house1", tiles: HOUSE1, cols: 3, rows: 3, zone: "residential" },
];
