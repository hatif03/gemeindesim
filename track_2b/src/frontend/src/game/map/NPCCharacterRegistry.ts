/**
 * NPC character sprite data from Kenney RPG Urban Pack.
 * Spritesheet: "city-tiles" (tilemap_packed.png), 27 cols wide, 16×16px tiles
 * ID = row * 27 + col (0-indexed)
 *
 * Per character: 4 columns (west, south, north, east)
 * Per column: 3 rows → row0=idle, row1=walkA, row2=walkB
 */

export type CharacterType =
  | "young_boy"
  | "adult_woman"
  | "old_man"
  | "construction_worker"
  | "adult_man"
  | "young_girl";

export type Direction = "west" | "south" | "north" | "east";

/** Base tile ID for each character (top-left tile = west idle) */
const CHARACTER_BASE: Record<CharacterType, number> = {
  young_boy: 23,
  adult_woman: 104,
  old_man: 185,
  construction_worker: 266,
  adult_man: 347,
  young_girl: 428,
};

const DIR_COL_OFFSET: Record<Direction, number> = {
  west: 0,
  south: 1,
  north: 2,
  east: 3,
};

const TILESET_COLS = 27;

/** Get a single frame tile ID */
function tileId(
  characterType: CharacterType,
  dir: Direction,
  row: 0 | 1 | 2,
): number {
  const base = CHARACTER_BASE[characterType];
  const baseRow = Math.floor(base / TILESET_COLS);
  const baseCol = base % TILESET_COLS;
  return (baseRow + row) * TILESET_COLS + baseCol + DIR_COL_OFFSET[dir];
}

export function getIdleFrame(
  characterType: CharacterType,
  dir: Direction,
): number {
  return tileId(characterType, dir, 0);
}

export function getWalkFrames(
  characterType: CharacterType,
  dir: Direction,
): [number, number] {
  return [tileId(characterType, dir, 1), tileId(characterType, dir, 2)];
}

export function getAnimKey(
  characterType: CharacterType,
  dir: Direction,
): string {
  return `npc_${characterType}_${dir}`;
}

/** Map role string to character type */
export function roleToCharacter(role: string, npcIndex: number): CharacterType {
  switch (role) {
    case "worker":
      return "construction_worker";
    case "farmer":
      return "construction_worker";
    case "retiree":
      return "old_man";
    case "activist":
      return npcIndex % 2 === 0 ? "adult_woman" : "young_girl";
    case "shopkeeper":
      return "adult_woman";
    case "student":
      return npcIndex % 2 === 0 ? "young_boy" : "young_girl";
    case "politician":
      return "old_man";
    case "business_owner":
      return npcIndex % 2 === 0 ? "adult_man" : "adult_woman";
    case "driver":
      return "adult_man";
    default:
      return ALL_CHARACTERS[npcIndex % ALL_CHARACTERS.length];
  }
}

/** All character types, for animation registration */
export const ALL_CHARACTERS: CharacterType[] = [
  "young_boy",
  "adult_woman",
  "old_man",
  "construction_worker",
  "adult_man",
  "young_girl",
];

export const ALL_DIRECTIONS: Direction[] = ["west", "south", "north", "east"];
