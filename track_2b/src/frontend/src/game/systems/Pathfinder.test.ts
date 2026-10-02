import { describe, expect, it } from "vitest";
import { findPath } from "./Pathfinder";

/** Helper: create a walkability checker from a string grid.
 *  '.' = walkable, '#' = wall.  Row 0 is top. */
function makeGrid(rows: string[]): (col: number, row: number) => boolean {
  const height = rows.length;
  const width = rows[0].length;
  return (col, row) => {
    if (col < 0 || row < 0 || col >= width || row >= height) return false;
    return rows[row][col] === ".";
  };
}

describe("Pathfinder (A*)", () => {
  it("returns empty array when start === goal", () => {
    const isWalkable = makeGrid(["..."]);
    const path = findPath({ col: 1, row: 0 }, { col: 1, row: 0 }, isWalkable);
    expect(path).toEqual([]);
  });

  it("finds a straight-line path on open ground", () => {
    const isWalkable = makeGrid([".....", ".....", "....."]);
    const path = findPath({ col: 0, row: 1 }, { col: 4, row: 1 }, isWalkable);
    expect(path).not.toBeNull();
    expect(path!.length).toBe(4);
    // First step moves right from (0,1)
    expect(path![0]).toEqual({ col: 1, row: 1 });
    // Last step is the goal
    expect(path![path!.length - 1]).toEqual({ col: 4, row: 1 });
  });

  it("routes around a wall", () => {
    // Map:
    //  . . . . .
    //  . # # # .
    //  . . . . .
    const isWalkable = makeGrid([".....", ".###.", "....."]);
    const path = findPath({ col: 0, row: 1 }, { col: 4, row: 1 }, isWalkable);
    expect(path).not.toBeNull();
    // Path must go around the wall — cannot pass through row 1 cols 1-3
    for (const node of path!) {
      const isWall = node.row === 1 && node.col >= 1 && node.col <= 3;
      expect(isWall).toBe(false);
    }
    // Goal reached
    expect(path![path!.length - 1]).toEqual({ col: 4, row: 1 });
  });

  it("returns null when goal is unreachable (walled off)", () => {
    // Map:
    //  . # .
    //  . # .
    //  . # .
    const isWalkable = makeGrid([".#.", ".#.", ".#."]);
    const path = findPath({ col: 0, row: 0 }, { col: 2, row: 0 }, isWalkable);
    expect(path).toBeNull();
  });

  it("returns null when goal is inside a wall", () => {
    const isWalkable = makeGrid(["..#", "..#", "..."]);
    const path = findPath({ col: 0, row: 0 }, { col: 2, row: 0 }, isWalkable);
    expect(path).toBeNull();
  });

  it("finds shortest path through a narrow corridor", () => {
    // Map:
    //  # . #
    //  # . #
    //  # . #
    const isWalkable = makeGrid(["#.#", "#.#", "#.#"]);
    const path = findPath({ col: 1, row: 0 }, { col: 1, row: 2 }, isWalkable);
    expect(path).not.toBeNull();
    expect(path!.length).toBe(2);
    expect(path).toEqual([
      { col: 1, row: 1 },
      { col: 1, row: 2 },
    ]);
  });

  it("path excludes start, includes goal", () => {
    const isWalkable = makeGrid(["....."]);
    const path = findPath({ col: 0, row: 0 }, { col: 3, row: 0 }, isWalkable);
    expect(path).not.toBeNull();
    // Should not include start (0,0)
    expect(path!.find((n) => n.col === 0 && n.row === 0)).toBeUndefined();
    // Should include goal (3,0)
    expect(path![path!.length - 1]).toEqual({ col: 3, row: 0 });
  });

  it("respects maxNodes limit and returns null for long paths", () => {
    // 50-tile corridor — with maxNodes=10 it should give up
    const row = ".".repeat(50);
    const isWalkable = makeGrid([row]);
    const path = findPath(
      { col: 0, row: 0 },
      { col: 49, row: 0 },
      isWalkable,
      10,
    );
    expect(path).toBeNull();
  });

  it("handles L-shaped path correctly", () => {
    // Map:
    //  . . .
    //  # # .
    //  . . .
    const isWalkable = makeGrid(["...", "##.", "..."]);
    const path = findPath({ col: 0, row: 0 }, { col: 0, row: 2 }, isWalkable);
    expect(path).not.toBeNull();
    // Must go right, then down, then left — around the wall
    expect(path![path!.length - 1]).toEqual({ col: 0, row: 2 });
    // No path node should be on a wall
    for (const node of path!) {
      expect(isWalkable(node.col, node.row)).toBe(true);
    }
  });

  it("uses only cardinal directions (no diagonals)", () => {
    const isWalkable = makeGrid(["...", "...", "..."]);
    const path = findPath({ col: 0, row: 0 }, { col: 2, row: 2 }, isWalkable);
    expect(path).not.toBeNull();
    // Each step should differ by exactly 1 in either col or row, not both
    let prev = { col: 0, row: 0 };
    for (const node of path!) {
      const dc = Math.abs(node.col - prev.col);
      const dr = Math.abs(node.row - prev.row);
      expect(dc + dr).toBe(1);
      prev = node;
    }
  });

  it("finds optimal path length (Manhattan distance on open grid)", () => {
    const isWalkable = makeGrid([".....", ".....", ".....", ".....", "....."]);
    const path = findPath({ col: 0, row: 0 }, { col: 4, row: 4 }, isWalkable);
    expect(path).not.toBeNull();
    // Manhattan distance = 4 + 4 = 8
    expect(path!.length).toBe(8);
  });

  it("adjacent start and goal returns single-step path", () => {
    const isWalkable = makeGrid(["..."]);
    const path = findPath({ col: 0, row: 0 }, { col: 1, row: 0 }, isWalkable);
    expect(path).not.toBeNull();
    expect(path!.length).toBe(1);
    expect(path![0]).toEqual({ col: 1, row: 0 });
  });
});
