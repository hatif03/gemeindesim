import { CENTER_BOUNDS } from "../config";
import type { NPC } from "../entities/NPC";
import type { OccupancyGrid } from "./OccupancyGrid";

type TileCheck = (col: number, row: number) => boolean;

/** Cardinal direction deltas */
const DIRS = [
  { dx: 0, dy: -1 }, // up
  { dx: 0, dy: 1 }, // down
  { dx: -1, dy: 0 }, // left
  { dx: 1, dy: 0 }, // right
] as const;

/** Opposite direction index: up↔down, left↔right */
const OPPOSITE = [1, 0, 3, 2] as const;

interface ZoneBounds {
  minRow: number;
  maxRow: number;
}

const ZONE_BOUNDS: Record<string, ZoneBounds> = {
  government: { minRow: 3, maxRow: 10 },
  commercial: { minRow: 11, maxRow: 16 },
  industrial: { minRow: 19, maxRow: 24 },
  residential: { minRow: 0, maxRow: 29 },
};

/**
 * Handles NPC roaming with natural movement behavior.
 * - NPCs prefer roads and sidewalks over grass
 * - NPCs maintain momentum (avoid instant 180-degree turns)
 * - NPCs are leashed to their assigned zone
 * - Walk→pause→walk cycle with variable timing
 */
export class MovementSystem {
  private timers: Map<string, Phaser.Time.TimerEvent> = new Map();
  private scene: Phaser.Scene;
  private isWalkable: TileCheck;
  private isRoad: TileCheck;
  /** Last movement direction index per NPC (0=up,1=down,2=left,3=right) */
  private lastDir: Map<string, number> = new Map();
  /** Assigned zone per NPC */
  private npcZone: Map<string, string> = new Map();
  /** NPCs currently overridden (protesting/striking) — skip random movement */
  private overridden = new Set<string>();
  private occupancy: OccupancyGrid;

  constructor(
    scene: Phaser.Scene,
    isWalkable: TileCheck,
    isRoad: TileCheck,
    occupancy: OccupancyGrid,
  ) {
    this.scene = scene;
    this.isWalkable = isWalkable;
    this.isRoad = isRoad;
    this.occupancy = occupancy;
  }

  /** Start random roaming for an NPC */
  startRoaming(npc: NPC, zone?: string) {
    if (zone) {
      this.npcZone.set(npc.npcId, zone);
    }
    // Stagger initial delay so NPCs don't all move at once
    const delay = 1500 + Math.random() * 3000;
    const timer = this.scene.time.addEvent({
      delay,
      callback: () => this.step(npc),
      loop: false,
    });
    this.timers.set(npc.npcId, timer);
  }

  /** Pause random movement for an NPC (e.g. while protesting) */
  override(npcId: string) {
    this.overridden.add(npcId);
    const timer = this.timers.get(npcId);
    if (timer) timer.destroy();
    this.timers.delete(npcId);
  }

  /** Resume random movement */
  release(npcId: string) {
    this.overridden.delete(npcId);
  }

  private step(npc: NPC) {
    if (this.overridden.has(npc.npcId)) return;
    if (npc.isMoving) {
      this.scheduleNext(npc, 200);
      return;
    }

    // 30% chance to idle (look around), 70% chance to walk
    if (Math.random() < 0.3) {
      // Idle: face a random direction without moving
      const dirs = ["up", "down", "left", "right"] as const;
      npc.face(dirs[Math.floor(Math.random() * dirs.length)]);
      npc.npcState = "idle";
      // Longer pause when idling
      this.scheduleNext(npc, 1500 + Math.random() * 2500);
      return;
    }

    const chosen = this.pickDirection(npc);
    if (chosen === null) {
      // Stuck — idle and try again soon
      npc.npcState = "idle";
      this.scheduleNext(npc, 500);
      return;
    }

    const dir = DIRS[chosen];
    this.lastDir.set(npc.npcId, chosen);
    npc.npcState = "walking";
    this.occupancy.occupy(npc.npcId, npc.tileX + dir.dx, npc.tileY + dir.dy);
    npc.walkTo(npc.tileX + dir.dx, npc.tileY + dir.dy).then(() => {
      npc.npcState = "idle";
      // Brief pause after each step
      this.scheduleNext(npc, 400 + Math.random() * 800);
    });
  }

  private pickDirection(npc: NPC): number | null {
    const lastDirIdx = this.lastDir.get(npc.npcId);
    const zone = this.npcZone.get(npc.npcId);
    const bounds = zone ? ZONE_BOUNDS[zone] : undefined;
    const isDriver = npc.role === "driver";
    const carOrientation: string | undefined = (
      npc as { template?: { orientation?: string } }
    ).template?.orientation;

    // Score each direction — road tiles only; non-road as last resort
    const roadScored: { idx: number; score: number }[] = [];
    const offRoadScored: { idx: number; score: number }[] = [];

    for (let i = 0; i < DIRS.length; i++) {
      const { dx, dy } = DIRS[i];
      const nx = npc.tileX + dx;
      const ny = npc.tileY + dy;

      if (!this.isWalkable(nx, ny)) continue;
      if (this.occupancy.isOccupiedByOther(npc.npcId, nx, ny)) continue;

      // Portrait cars: vertical road lane — up/down only
      if (isDriver && carOrientation === "portrait" && (i === 2 || i === 3))
        continue;
      // Landscape cars: horizontal road lane — left/right only
      if (isDriver && carOrientation === "landscape" && (i === 0 || i === 1))
        continue;

      // Drivers can only move to road tiles
      if (isDriver && !this.isRoad(nx, ny)) continue;

      // Check full car footprint is on road at the new position
      if (isDriver && carOrientation === "portrait") {
        // Check both columns for the new row
        if (!this.isRoad(nx, ny) || !this.isRoad(nx + 1, ny)) continue;
      }
      if (isDriver && carOrientation === "landscape") {
        // Check both rows for the new column
        if (!this.isRoad(nx, ny) || !this.isRoad(nx, ny + 1)) continue;
      }

      // Reject tiles outside center bounds
      if (
        nx < CENTER_BOUNDS.minCol ||
        nx > CENTER_BOUNDS.maxCol ||
        ny < CENTER_BOUNDS.minRow ||
        ny > CENTER_BOUNDS.maxRow
      )
        continue;

      const onRoad = this.isRoad(nx, ny);
      let score = onRoad ? 10 : 1;

      // Momentum: prefer continuing in the same direction
      if (lastDirIdx !== undefined && i === lastDirIdx) {
        score *= 2;
      }

      // Penalize instant 180-degree turns
      if (lastDirIdx !== undefined && i === OPPOSITE[lastDirIdx]) {
        score *= 0.15;
      }

      // Zone leashing: penalize moves that go away from home zone
      if (bounds) {
        const zoneCenterRow = (bounds.minRow + bounds.maxRow) / 2;
        const currentDist = Math.abs(npc.tileY - zoneCenterRow);
        const nextDist = Math.abs(ny - zoneCenterRow);

        // If already outside zone, strongly pull back
        if (npc.tileY < bounds.minRow || npc.tileY > bounds.maxRow) {
          if (nextDist < currentDist) score *= 4;
          else score *= 0.1;
        }
        // If near zone boundary, mild bias inward
        else if (
          npc.tileY <= bounds.minRow + 1 ||
          npc.tileY >= bounds.maxRow - 1
        ) {
          if (nextDist < currentDist) score *= 1.5;
          else if (nextDist > currentDist) score *= 0.5;
        }
      }

      if (onRoad) {
        roadScored.push({ idx: i, score });
      } else {
        offRoadScored.push({ idx: i, score });
      }
    }

    // Prefer road tiles; only fall back to off-road if completely stuck
    const scored = roadScored.length > 0 ? roadScored : offRoadScored;

    if (scored.length === 0) return null;

    // Weighted random selection
    const totalWeight = scored.reduce((sum, s) => sum + s.score, 0);
    let roll = Math.random() * totalWeight;
    for (const s of scored) {
      roll -= s.score;
      if (roll <= 0) return s.idx;
    }
    return scored[scored.length - 1].idx;
  }

  private scheduleNext(npc: NPC, delay: number) {
    if (this.overridden.has(npc.npcId)) return;
    const timer = this.scene.time.addEvent({
      delay,
      callback: () => this.step(npc),
      loop: false,
    });
    this.timers.set(npc.npcId, timer);
  }

  destroy() {
    for (const timer of this.timers.values()) {
      timer.destroy();
    }
    this.timers.clear();
    this.overridden.clear();
    this.lastDir.clear();
    this.npcZone.clear();
  }
}
