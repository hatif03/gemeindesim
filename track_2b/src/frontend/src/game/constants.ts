export type MapType = "ccity" | "pico8" | "citypack";

export const TILE_SIZE = 16;
export const MAP_COLS = 80;
export const MAP_ROWS = 60;
export const GAME_WIDTH = MAP_COLS * TILE_SIZE; // 1280
export const GAME_HEIGHT = MAP_ROWS * TILE_SIZE; // 960
export const SCALE_FACTOR = 1; // 1:1 — Phaser Scale.FIT handles display scaling

// Per-map tile/grid constants
export const MAP_CONFIGS = {
  ccity: { tileSize: 16, cols: 80, rows: 60, spacing: 0 },
  pico8: { tileSize: 8, cols: 55, rows: 30, spacing: 0 },
  citypack: { tileSize: 16, cols: 100, rows: 80, spacing: 0 },
} as const;

export let selectedMap: MapType = "citypack";
export function setSelectedMap(m: MapType) {
  selectedMap = m;
}

export let proceduralMap = false;
export function setProceduralMap(v: boolean) {
  proceduralMap = v;
}

export function getMapConfig() {
  return MAP_CONFIGS[selectedMap];
}

// Center bounds for NPC confinement — keeps NPCs within the initial 50x50 visible canvas region
export const CENTER_BOUNDS = {
  minCol: 1,
  maxCol: 50,
  minRow: 1,
  maxRow: 50,
} as const;
