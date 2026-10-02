export interface PathNode {
  col: number;
  row: number;
}

interface AStarNode {
  col: number;
  row: number;
  g: number;
  h: number;
  f: number;
  parent: AStarNode | null;
}

const NEIGHBORS: [number, number][] = [
  [0, -1],
  [0, 1],
  [-1, 0],
  [1, 0],
];

function heuristic(a: PathNode, b: PathNode): number {
  return Math.abs(a.col - b.col) + Math.abs(a.row - b.row);
}

function toKey(col: number, row: number): string {
  return `${col},${row}`;
}

/**
 * A* pathfinding. Returns waypoints from start (exclusive) to goal (inclusive),
 * or null if unreachable within maxNodes explored.
 */
export function findPath(
  start: PathNode,
  goal: PathNode,
  isWalkable: (col: number, row: number) => boolean,
  maxNodes = 400,
): PathNode[] | null {
  if (start.col === goal.col && start.row === goal.row) {
    return [];
  }

  const open: AStarNode[] = [
    {
      col: start.col,
      row: start.row,
      g: 0,
      h: heuristic(start, goal),
      f: heuristic(start, goal),
      parent: null,
    },
  ];
  const closed = new Set<string>();
  const bestG = new Map<string, number>();
  bestG.set(toKey(start.col, start.row), 0);
  let explored = 0;

  while (open.length > 0) {
    if (explored >= maxNodes) return null;

    let bestIdx = 0;
    for (let i = 1; i < open.length; i++) {
      if (open[i].f < open[bestIdx].f) bestIdx = i;
    }
    const current = open[bestIdx];
    open[bestIdx] = open[open.length - 1];
    open.pop();

    if (current.col === goal.col && current.row === goal.row) {
      const path: PathNode[] = [];
      let node: AStarNode | null = current;
      while (node?.parent) {
        path.push({ col: node.col, row: node.row });
        node = node.parent;
      }
      path.reverse();
      return path;
    }

    const key = toKey(current.col, current.row);
    if (closed.has(key)) continue;
    closed.add(key);
    explored++;

    for (const [dc, dr] of NEIGHBORS) {
      const nc = current.col + dc;
      const nr = current.row + dr;
      const nKey = toKey(nc, nr);

      if (closed.has(nKey)) continue;
      if (!isWalkable(nc, nr)) continue;

      const g = current.g + 1;
      const prev = bestG.get(nKey);
      if (prev !== undefined && g >= prev) continue;
      bestG.set(nKey, g);

      const h = heuristic({ col: nc, row: nr }, goal);
      open.push({ col: nc, row: nr, g, h, f: g + h, parent: current });
    }
  }

  return null;
}
