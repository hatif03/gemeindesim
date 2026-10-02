import type { BuildingPositions } from "@/types";
import { MAP_COLS, MAP_ROWS } from "../config";
import * as Tiles from "./TileRegistry";

// Each cell in the grid holds a ground tile and optionally an overlay tile
export interface CityGrid {
  ground: number[][]; // MAP_ROWS × MAP_COLS — base layer (grass, road, sidewalk)
  buildings: number[][]; // MAP_ROWS × MAP_COLS — building/object layer (-1 = empty)
  walkable: boolean[][]; // MAP_ROWS × MAP_COLS — can NPCs walk here?
  buildingPositions: BuildingPositions;
}

// ─── Helpers ───

function make2D<T>(rows: number, cols: number, fill: T): T[][] {
  return Array.from({ length: rows }, () => Array(cols).fill(fill) as T[]);
}

function fillRect(
  grid: number[][],
  r1: number,
  c1: number,
  r2: number,
  c2: number,
  tile: number,
) {
  for (let r = r1; r <= r2; r++) {
    for (let c = c1; c <= c2; c++) {
      grid[r][c] = tile;
    }
  }
}

// Horizontal road rows
const H_ROADS = [3, 4, 9, 10, 17, 18, 25, 26];
// Vertical road cols (2-wide each)
const V_ROAD_PAIRS = [
  [5, 6],
  [19, 20],
  [33, 34],
];

function isHRoad(row: number): boolean {
  return H_ROADS.includes(row);
}

function isVRoad(col: number): boolean {
  return V_ROAD_PAIRS.some(([a, b]) => col === a || col === b);
}

function isRoad(row: number, col: number): boolean {
  return isHRoad(row) || isVRoad(col);
}

// ─── City layout ───

function layGroundAndRoads(ground: number[][]) {
  // Fill everything with gray pavement first (matches Sample.png urban style)
  fillRect(ground, 0, 0, MAP_ROWS - 1, MAP_COLS - 1, Tiles.CONCRETE);

  // Lay sidewalks adjacent to roads
  for (let r = 0; r < MAP_ROWS; r++) {
    for (let c = 0; c < MAP_COLS; c++) {
      if (isRoad(r, c)) {
        ground[r][c] = Tiles.ROAD_H; // base road tile
      }
    }
  }

  // Now differentiate road tiles
  for (let r = 0; r < MAP_ROWS; r++) {
    for (let c = 0; c < MAP_COLS; c++) {
      if (!isRoad(r, c)) continue;

      const h = isHRoad(r);
      const v = isVRoad(c);

      if (h && v) {
        ground[r][c] = Tiles.ROAD_CROSS;
      } else if (h) {
        ground[r][c] = Tiles.ROAD_H;
      } else {
        ground[r][c] = Tiles.ROAD_V;
      }
    }
  }

  // Sidewalks along roads
  for (let r = 0; r < MAP_ROWS; r++) {
    for (let c = 0; c < MAP_COLS; c++) {
      if (isRoad(r, c)) continue;
      // Check if adjacent to a road
      const adjRoad =
        (r > 0 && isRoad(r - 1, c)) ||
        (r < MAP_ROWS - 1 && isRoad(r + 1, c)) ||
        (c > 0 && isRoad(r, c - 1)) ||
        (c < MAP_COLS - 1 && isRoad(r, c + 1));
      if (adjRoad) {
        ground[r][c] = Tiles.SIDEWALK;
      }
    }
  }
}

// Place a 3-row-tall house: 2 rows roof + 1 row facade (2 wide × 3 tall)
function placeBuilding2x2(
  buildings: number[][],
  walkable: boolean[][],
  row: number,
  col: number,
  roofTL: number,
  roofTR: number,
  wallL: number,
  wallR: number,
) {
  // Row 0-1: roof
  buildings[row][col] = roofTL;
  buildings[row][col + 1] = roofTR;
  buildings[row + 1][col] = roofTL;
  buildings[row + 1][col + 1] = roofTR;
  // Row 2: facade
  buildings[row + 2][col] = wallL;
  buildings[row + 2][col + 1] = wallR;
  for (let dr = 0; dr < 3; dr++) {
    walkable[row + dr][col] = false;
    walkable[row + dr][col + 1] = false;
  }
}

// Place a 3-row-tall shop/factory: 2 rows roof + 1 row facade (3 wide × 3 tall)
function placeBuilding3x2(
  buildings: number[][],
  walkable: boolean[][],
  row: number,
  col: number,
  roofL: number,
  roofM: number,
  roofR: number,
  wallL: number,
  wallM: number,
  wallR: number,
) {
  // Row 0-1: roof
  buildings[row][col] = roofL;
  buildings[row][col + 1] = roofM;
  buildings[row][col + 2] = roofR;
  buildings[row + 1][col] = roofL;
  buildings[row + 1][col + 1] = roofM;
  buildings[row + 1][col + 2] = roofR;
  // Row 2: facade
  buildings[row + 2][col] = wallL;
  buildings[row + 2][col + 1] = wallM;
  buildings[row + 2][col + 2] = wallR;
  for (let dc = 0; dc < 3; dc++) {
    for (let dr = 0; dr < 3; dr++) {
      walkable[row + dr][col + dc] = false;
    }
  }
}

export function generateCity(): CityGrid {
  const ground = make2D(MAP_ROWS, MAP_COLS, Tiles.CONCRETE);
  const buildings = make2D(MAP_ROWS, MAP_COLS, -1);
  const walkable = make2D(MAP_ROWS, MAP_COLS, true);

  const positions: BuildingPositions = {
    government: { x: 0, y: 0 },
    shops: [],
    factories: [],
    houses: [],
  };

  // 1. Ground + roads
  layGroundAndRoads(ground);

  // 2. Mark roads as walkable (NPCs walk on roads and sidewalks)
  for (let r = 0; r < MAP_ROWS; r++) {
    for (let c = 0; c < MAP_COLS; c++) {
      // Everything starts walkable; we mark buildings as not walkable
    }
  }

  // 3. Parks (rows 0-2 and 27-29) — add trees
  const parkRows = [
    [0, 2],
    [27, 29],
  ];
  for (const [r1, r2] of parkRows) {
    for (let r = r1; r <= r2; r++) {
      for (let c = 0; c < MAP_COLS; c++) {
        if (isRoad(r, c) || ground[r][c] === Tiles.SIDEWALK) continue;
        // Park ground is green grass
        ground[r][c] = Tiles.GRASS;
        // Scatter trees and bushes
        if ((c + r) % 4 === 0) {
          buildings[r][c] = Tiles.TREE_GREEN_TOP;
          walkable[r][c] = false;
        } else if ((c + r) % 7 === 0) {
          buildings[r][c] = Tiles.BUSH;
          walkable[r][c] = false;
        }
      }
    }
  }

  // 4. Government building (rows 5-8, centered between roads)
  // Place between vertical roads at cols 7-18 area, rows 5-8
  const govRow = 5;
  const govCol = 8;
  positions.government = { x: govCol, y: govRow };

  // Government: 4 wide × 2 tall using gray roof + gov walls
  for (let dc = 0; dc < 4; dc++) {
    buildings[govRow][govCol + dc] = Tiles.GOV_ROOF;
    buildings[govRow + 1][govCol + dc] =
      dc === 1 ? Tiles.GOV_DOOR : Tiles.GOV_WALL;
    walkable[govRow][govCol + dc] = false;
    walkable[govRow + 1][govCol + dc] = false;
  }
  // Pillars on sides
  buildings[govRow + 1][govCol] = Tiles.GOV_PILLAR;
  buildings[govRow + 1][govCol + 3] = Tiles.GOV_PILLAR;
  // Second floor
  for (let dc = 0; dc < 4; dc++) {
    buildings[govRow + 2][govCol + dc] = Tiles.GOV_WINDOW;
    walkable[govRow + 2][govCol + dc] = false;
  }

  // Residential on sides of government (rows 5-8)
  // Buildings are now 3 rows tall (2 roof + 1 facade), so avoid road overflow
  const houseConfigs = [
    { row: 5, col: 1, id: "house-1" },
    { row: 5, col: 3, id: "house-2" },
    { row: 6, col: 1, id: "house-3" },
    { row: 6, col: 3, id: "house-4" },
    { row: 5, col: 14, id: "house-5" },
    { row: 5, col: 16, id: "house-6" },
    { row: 6, col: 14, id: "house-7" },
    { row: 6, col: 16, id: "house-8" },
  ];

  for (const h of houseConfigs) {
    if (isRoad(h.row, h.col) || isRoad(h.row + 2, h.col)) continue;
    if (ground[h.row][h.col] === Tiles.SIDEWALK) continue;
    placeBuilding2x2(
      buildings,
      walkable,
      h.row,
      h.col,
      Tiles.ROOF_RED_TL,
      Tiles.ROOF_RED_TR,
      Tiles.WALL_WINDOW,
      Tiles.WALL_DOOR,
    );
    positions.houses.push({ id: h.id, x: h.col, y: h.row });
  }

  // 5. Commercial district (rows 11-16)
  const shopConfigs = [
    { row: 11, col: 7, id: "shop-grocery" },
    { row: 11, col: 10, id: "shop-bakery" },
    { row: 11, col: 13, id: "shop-hardware" },
    { row: 11, col: 16, id: "shop-clothing" },
    { row: 14, col: 7, id: "shop-restaurant" },
    { row: 14, col: 10, id: "shop-pharmacy" },
    { row: 14, col: 13, id: "shop-electronics" },
    { row: 14, col: 16, id: "shop-bank" },
    // Right side of map
    { row: 11, col: 22, id: "shop-cafe" },
    { row: 11, col: 25, id: "shop-bookstore" },
    { row: 14, col: 22, id: "shop-barber" },
    { row: 14, col: 25, id: "shop-market" },
  ];

  for (const s of shopConfigs) {
    if (isRoad(s.row, s.col) || isRoad(s.row + 2, s.col)) continue;
    placeBuilding3x2(
      buildings,
      walkable,
      s.row,
      s.col,
      Tiles.ROOF_GRAY_TL,
      Tiles.ROOF_GRAY_T,
      Tiles.ROOF_GRAY_TR,
      Tiles.WALL_SHOP_FRONT,
      Tiles.WALL_SHOP_DOOR,
      Tiles.WALL_SHOP_WINDOW,
    );
    positions.shops.push({ id: s.id, x: s.col, y: s.row });
  }

  // More houses in commercial zone sides
  const moreHouses = [
    { row: 11, col: 1, id: "house-9" },
    { row: 11, col: 3, id: "house-10" },
    { row: 14, col: 1, id: "house-11" },
    { row: 14, col: 3, id: "house-12" },
    { row: 11, col: 28, id: "house-13" },
    { row: 11, col: 30, id: "house-14" },
    { row: 14, col: 28, id: "house-15" },
    { row: 14, col: 30, id: "house-16" },
  ];

  for (const h of moreHouses) {
    if (h.col >= MAP_COLS - 1) continue;
    if (isRoad(h.row, h.col) || isRoad(h.row + 2, h.col)) continue;
    placeBuilding2x2(
      buildings,
      walkable,
      h.row,
      h.col,
      Tiles.ROOF_RED_TL,
      Tiles.ROOF_RED_TR,
      Tiles.WALL_WINDOW,
      Tiles.WALL_DOOR,
    );
    positions.houses.push({ id: h.id, x: h.col, y: h.row });
  }

  // 6. Industrial zone (rows 19-24)
  const factoryConfigs = [
    { row: 19, col: 7, id: "factory-steel" },
    { row: 19, col: 11, id: "factory-textile" },
    { row: 22, col: 7, id: "factory-auto" },
    { row: 22, col: 11, id: "factory-food" },
    { row: 19, col: 22, id: "factory-tech" },
    { row: 22, col: 22, id: "factory-chemical" },
  ];

  for (const f of factoryConfigs) {
    if (isRoad(f.row, f.col) || isRoad(f.row + 2, f.col)) continue;
    placeBuilding3x2(
      buildings,
      walkable,
      f.row,
      f.col,
      Tiles.ROOF_GRAY_TL,
      Tiles.ROOF_GRAY_T,
      Tiles.ROOF_GRAY_TR,
      Tiles.FACTORY_WALL,
      Tiles.FACTORY_DOOR,
      Tiles.FACTORY_CHIMNEY,
    );
    positions.factories.push({ id: f.id, x: f.col, y: f.row });
  }

  // More houses in industrial area
  const indHouses = [
    { row: 19, col: 1, id: "house-17" },
    { row: 19, col: 3, id: "house-18" },
    { row: 22, col: 1, id: "house-19" },
    { row: 22, col: 3, id: "house-20" },
    { row: 19, col: 28, id: "house-21" },
    { row: 22, col: 28, id: "house-22" },
    { row: 19, col: 36, id: "house-23" },
    { row: 22, col: 36, id: "house-24" },
  ];

  for (const h of indHouses) {
    if (h.col + 1 >= MAP_COLS) continue;
    if (isRoad(h.row, h.col) || isRoad(h.row + 2, h.col)) continue;
    placeBuilding2x2(
      buildings,
      walkable,
      h.row,
      h.col,
      Tiles.ROOF_GREEN_TL,
      Tiles.ROOF_GREEN_TR,
      Tiles.WALL_BRICK_WINDOW,
      Tiles.WALL_DOOR,
    );
    positions.houses.push({ id: h.id, x: h.col, y: h.row });
  }

  // 7. Add lamp posts and props along sidewalks
  for (let r = 0; r < MAP_ROWS; r++) {
    for (let c = 0; c < MAP_COLS; c++) {
      if (ground[r][c] !== Tiles.SIDEWALK) continue;
      if (buildings[r][c] !== -1) continue;
      // Place lamp posts every ~8 tiles on sidewalks
      if (c % 8 === 0 && r % 6 === 2) {
        buildings[r][c] = Tiles.LAMP_POST;
        walkable[r][c] = false;
      }
      // Occasional benches
      if (c % 12 === 4 && r % 8 === 5) {
        buildings[r][c] = Tiles.BENCH_H;
        walkable[r][c] = false;
      }
    }
  }

  return { ground, buildings, walkable, buildingPositions: positions };
}
