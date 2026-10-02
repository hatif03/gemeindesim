/**
 * Citypack car tile IDs (0-indexed, GID = id + 1 when in Tiled JSON).
 * All cars use the "citypack" spritesheet loaded as key "citypack".
 *
 * Orientation:
 *   PORTRAIT cars (2 wide × 3 tall) face SOUTH by default.
 *   LANDSCAPE cars (3 wide × 2 tall) face WEST by default.
 *
 * Flip rules (via Container.setScale):
 *   Portrait  moving SOUTH: setScale(1, 1)   — default
 *   Portrait  moving NORTH: setScale(1, -1)  — flip Y
 *   Landscape moving WEST:  setScale(1, 1)   — default
 *   Landscape moving EAST:  setScale(-1, 1)  — flip X
 */

export type CarOrientation = "portrait" | "landscape";

export interface CarTemplate {
  id: string;
  tiles: readonly (readonly number[])[]; // [row][col], 0-indexed tile IDs
  cols: number;
  rows: number;
  orientation: CarOrientation;
}

// Portrait cars (2w × 3h, facing south)
const CAR1_TILES = [
  [1935, 1936],
  [1999, 2000],
  [2063, 2064],
] as const;

const CAR2_TILES = [
  [1939, 1940],
  [2003, 2004],
  [2067, 2068],
] as const;

// Landscape cars (3w × 2h, facing west)
const CAR3_TILES = [
  [1544, 1545, 1546],
  [1608, 1609, 1610],
] as const;

const CAR4_TILES = [
  [1800, 1801, 1802],
  [1864, 1865, 1866],
] as const;

export const CAR_TEMPLATES: CarTemplate[] = [
  { id: "car1", tiles: CAR1_TILES, cols: 2, rows: 3, orientation: "portrait" },
  { id: "car2", tiles: CAR2_TILES, cols: 2, rows: 3, orientation: "portrait" },
  { id: "car3", tiles: CAR3_TILES, cols: 3, rows: 2, orientation: "landscape" },
  { id: "car4", tiles: CAR4_TILES, cols: 3, rows: 2, orientation: "landscape" },
];

/** Pick a random car template */
export function randomCarTemplate(rng: () => number): CarTemplate {
  return CAR_TEMPLATES[Math.floor(rng() * CAR_TEMPLATES.length)];
}
