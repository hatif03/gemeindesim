import { beforeEach, describe, expect, it } from "vitest";
import { OccupancyGrid } from "./OccupancyGrid";

describe("OccupancyGrid", () => {
  let grid: OccupancyGrid;

  beforeEach(() => {
    grid = new OccupancyGrid();
  });

  it("starts empty — no tile is occupied", () => {
    expect(grid.isOccupied(5, 5)).toBe(false);
    expect(grid.isOccupiedByOther("npc-1", 5, 5)).toBe(false);
  });

  it("marks a tile as occupied after occupy()", () => {
    grid.occupy("npc-1", 3, 4);
    expect(grid.isOccupied(3, 4)).toBe(true);
  });

  it("isOccupiedByOther returns false for the occupying NPC", () => {
    grid.occupy("npc-1", 3, 4);
    expect(grid.isOccupiedByOther("npc-1", 3, 4)).toBe(false);
  });

  it("isOccupiedByOther returns true for a different NPC", () => {
    grid.occupy("npc-1", 3, 4);
    expect(grid.isOccupiedByOther("npc-2", 3, 4)).toBe(true);
  });

  it("auto-releases old position when occupy() is called again", () => {
    grid.occupy("npc-1", 3, 4);
    grid.occupy("npc-1", 5, 6);
    expect(grid.isOccupied(3, 4)).toBe(false);
    expect(grid.isOccupied(5, 6)).toBe(true);
  });

  it("release() frees the tile", () => {
    grid.occupy("npc-1", 3, 4);
    grid.release("npc-1");
    expect(grid.isOccupied(3, 4)).toBe(false);
  });

  it("release() on unknown NPC is a no-op", () => {
    grid.release("nonexistent");
    expect(grid.isOccupied(0, 0)).toBe(false);
  });

  it("multiple NPCs can occupy different tiles", () => {
    grid.occupy("npc-1", 0, 0);
    grid.occupy("npc-2", 1, 1);
    grid.occupy("npc-3", 2, 2);
    expect(grid.isOccupied(0, 0)).toBe(true);
    expect(grid.isOccupied(1, 1)).toBe(true);
    expect(grid.isOccupied(2, 2)).toBe(true);
    expect(grid.isOccupied(3, 3)).toBe(false);
  });

  it("two NPCs cannot silently share a tile — second overwrites", () => {
    grid.occupy("npc-1", 5, 5);
    grid.occupy("npc-2", 5, 5);
    // npc-2 now owns the tile; npc-1's old position was auto-released
    expect(grid.isOccupiedByOther("npc-1", 5, 5)).toBe(true);
    expect(grid.isOccupiedByOther("npc-2", 5, 5)).toBe(false);
  });

  it("clear() removes all entries", () => {
    grid.occupy("npc-1", 0, 0);
    grid.occupy("npc-2", 1, 1);
    grid.clear();
    expect(grid.isOccupied(0, 0)).toBe(false);
    expect(grid.isOccupied(1, 1)).toBe(false);
  });
});
