// Named tile indices for Kenney RPG Urban Pack (tilemap_packed.png)
// 27 cols × 18 rows, 16×16px tiles, 0-indexed
// Helper: tile index = row * 27 + col
// ALL indices verified by visual inspection of tile_XXXX.png AND Sample.png

const COLS = 27;
const t = (row: number, col: number) => row * COLS + col;

// ─── Ground / Terrain ───
// Sample.png shows gray pavement as the main urban ground, green grass only in parks
export const GRASS = 27; // solid teal-green grass fill, no edges (matches Sample.png park)
export const GRASS_ALT = 28; // solid teal-green grass variant
export const CONCRETE = 81; // gray/purple pavement — main city ground (matches Sample.png)
export const CONCRETE_ALT = 82; // gray pavement with edge
export const DIRT = 180; // brown/tan solid ground
export const DIRT_ALT = 181; // brown variant

// ─── Roads (row 15-16 in tilemap, verified against Sample.png) ───
export const ROAD_H = 432; // medium gray road with white dashed horizontal center line
export const ROAD_V = 414; // medium gray road with white dashed vertical center line
export const ROAD_CROSS = 433; // solid medium gray — plain intersection fill
export const ROAD_T_DOWN = 433; // plain gray for T-junctions
export const ROAD_T_UP = 433;
export const ROAD_T_LEFT = 433;
export const ROAD_T_RIGHT = 433;
export const ROAD_CORNER_TL = 433;
export const ROAD_CORNER_TR = 433;
export const ROAD_CORNER_BL = 433;
export const ROAD_CORNER_BR = 433;
export const SIDEWALK = 81; // gray pavement with dotted texture (matches Sample.png sidewalks)

// ─── Water ───
export const WATER = 197;
export const WATER_EDGE_T = 198;
export const WATER_EDGE_B = 199;
export const WATER_EDGE_L = 200;
export const WATER_EDGE_R = 201;

// ─── Buildings — Roofs (verified against Sample.png) ───
// Residential: warm orange-brown flat rooftop (125-129)
export const ROOF_RED_TL = 125; // solid orange-brown roof fill
export const ROOF_RED_T = 125; // solid orange-brown roof fill
export const ROOF_RED_TR = 125; // solid orange-brown roof fill
export const ROOF_RED_BL = 125; // solid orange-brown roof fill
export const ROOF_RED_B = 125; // solid orange-brown roof fill
export const ROOF_RED_BR = 125; // solid orange-brown roof fill

// Commercial: darker brown roof with shingle lines (124, 126-128)
export const ROOF_GRAY_TL = 124; // brown roof with horizontal shingle lines
export const ROOF_GRAY_T = 124; // brown roof with shingle lines
export const ROOF_GRAY_TR = 124; // brown roof with shingle lines
export const ROOF_GRAY_BL = 124; // brown roof with shingle lines
export const ROOF_GRAY_B = 124; // brown roof with shingle lines
export const ROOF_GRAY_BR = 124; // brown roof with shingle lines

// Industrial: lighter beige/tan roof (108-110)
export const ROOF_GREEN_TL = 108; // beige/tan grid roof
export const ROOF_GREEN_T = 109; // beige/tan roof center
export const ROOF_GREEN_TR = 108; // beige/tan grid roof
export const ROOF_GREEN_BL = 108; // beige/tan grid roof
export const ROOF_GREEN_B = 109; // beige/tan roof center
export const ROOF_GREEN_BR = 108; // beige/tan grid roof

// ─── Building Walls / Facades ───
// Facade tiles: brick base with colored awning strip at top (matches Sample.png)
export const WALL_GRAY = 151; // solid orange brick wall
export const WALL_WINDOW = 152; // brick wall + blue awning strip (facade with window)
export const WALL_DOOR = 153; // brick wall + gray awning strip (facade with door)
export const WALL_BRICK = 178; // solid orange-brown brick
export const WALL_BRICK_WINDOW = 154; // brick + blue awning variant
export const WALL_SHOP_FRONT = 155; // facade with awning (shop)
export const WALL_SHOP_WINDOW = 156; // facade with awning variant
export const WALL_SHOP_DOOR = 157; // facade with awning + door

// ─── Government / Large building ───
export const GOV_ROOF = 113; // light beige/cream roof (stone government)
export const GOV_WALL = 178; // orange-brown brick wall
export const GOV_DOOR = 155; // facade with awning — government entrance
export const GOV_WINDOW = 151; // orange brick with window pattern
export const GOV_PILLAR = 408; // stone arch/column

// ─── Industrial ───
export const FACTORY_WALL = 178; // orange-brown brick wall
export const FACTORY_WINDOW = 151; // brick with window pattern
export const FACTORY_DOOR = 156; // facade with awning variant
export const FACTORY_CHIMNEY = 92; // tan/brown with dark border — chimney element

// ─── Trees / Nature ───
// Sample.png: bright green round tree canopies with visible brown trunks
export const TREE_GREEN_TOP = 259; // green tree with brown trunk (matches Sample.png)
export const TREE_GREEN_TRUNK = 260; // tree variant with trunk
export const TREE_ROUND = 237; // round solid green bush/shrub
export const TREE_SMALL = 235; // wide green hedge
export const BUSH = 237; // round green bush
export const FLOWER = 238; // small green bush variant
export const BENCH_H = 245; // horizontal bench
export const BENCH_V = 246; // vertical bench/seat

// ─── Furniture / Props ───
export const LAMP_POST = 190; // street lamp
export const TRASH_CAN = 272; // gray trash can/barrel
export const SIGN_POST = 162; // sign on pole
export const FIRE_HYDRANT = 307; // small object
export const MAILBOX = 279; // purple/gray mailbox
export const FENCE_H = 247; // horizontal fence/railing
export const FENCE_V = 244; // vertical fence/railing

// ─── Vehicles ───
export const CAR_RED_L = 396; // vehicle left
export const CAR_RED_R = 397; // vehicle right
export const CAR_BLUE_L = 400; // vehicle left (dark)
export const CAR_BLUE_R = 395; // vehicle right
export const TRUCK_L = 398; // truck left
export const TRUCK_R = 399; // truck right

// ─── NPC sprites (cols 23-26, rows 14-17) ───
// 16 unique static character tiles, no directional animation frames.
// Layout: 4 columns × 4 rows = 16 characters.
// Tiles: 401-404, 428-431, 455-458, 482-485
export const NPC_BASE_COL = 23;
export const NPC_BASE_ROW = 14;
export const NPC_COLS = 4; // cols 23-26
export const NPC_TOTAL = 16; // 4 cols × 4 rows

// Get NPC tile index by character index (0-15). Each NPC is a single static tile.
export function getNPCTile(charIndex: number): number {
  const col = NPC_BASE_COL + (charIndex % NPC_COLS);
  const row = NPC_BASE_ROW + Math.floor(charIndex / NPC_COLS);
  return t(row, col);
}

// Collision tile set — tiles that block NPC movement
export const COLLISION_TILES = new Set([
  WALL_GRAY,
  WALL_WINDOW,
  WALL_DOOR,
  WALL_BRICK,
  WALL_BRICK_WINDOW,
  WALL_SHOP_FRONT,
  WALL_SHOP_WINDOW,
  WALL_SHOP_DOOR,
  GOV_ROOF,
  GOV_WALL,
  GOV_DOOR,
  GOV_WINDOW,
  GOV_PILLAR,
  FACTORY_WALL,
  FACTORY_WINDOW,
  FACTORY_DOOR,
  FACTORY_CHIMNEY,
  TREE_GREEN_TOP,
  TREE_GREEN_TRUNK,
  TREE_ROUND,
  WATER,
  WATER_EDGE_T,
  WATER_EDGE_B,
  WATER_EDGE_L,
  WATER_EDGE_R,
  FENCE_H,
  FENCE_V,
  ROOF_RED_TL,
  ROOF_RED_T,
  ROOF_RED_TR,
  ROOF_RED_BL,
  ROOF_RED_B,
  ROOF_RED_BR,
  ROOF_GRAY_TL,
  ROOF_GRAY_T,
  ROOF_GRAY_TR,
  ROOF_GRAY_BL,
  ROOF_GRAY_B,
  ROOF_GRAY_BR,
  ROOF_GREEN_TL,
  ROOF_GREEN_T,
  ROOF_GREEN_TR,
  ROOF_GREEN_BL,
  ROOF_GREEN_B,
  ROOF_GREEN_BR,
]);
