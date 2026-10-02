import type * as Phaser from "phaser";
import { getCoordScale, moodToSentiment } from "@/lib/adapter";
import type { BuildingPositions } from "@/types";
import type { BackendNPC } from "@/types/backend";
import { eventBridge } from "../bridge/EventBridge";
import { CENTER_BOUNDS, TILE_SIZE, getMapConfig } from "../config";
import { spawnEmotionBubble } from "../effects/EconomicEffects";
import { Car } from "../entities/Car";
import { NPC } from "../entities/NPC";
import { WorldChatBubble } from "../entities/WorldChatBubble";
import { CAR_TEMPLATES, type CarTemplate } from "../map/CarRegistry";
import { roleToCharacter } from "../map/NPCCharacterRegistry";
import { MovementSystem } from "./MovementSystem";
import { OccupancyGrid } from "./OccupancyGrid";
import { findPath } from "./Pathfinder";

function roleToZone(role: string): string {
  switch (role) {
    case "politician":
    case "activist":
      return "government";
    case "shopkeeper":
    case "business_owner":
      return "commercial";
    case "worker":
    case "farmer":
      return "industrial";
    default:
      return "residential";
  }
}

const MIN_SPAWN_SPACING = 4;

export class NPCManager {
  private scene: Phaser.Scene;
  private npcs: Map<string, NPC> = new Map();
  private movement: MovementSystem;
  private buildingPositions: BuildingPositions;
  private isWalkable: (col: number, row: number) => boolean;
  private isRoad: (col: number, row: number) => boolean;
  private getRoadType: (col: number, row: number) => "v" | "h" | "none";
  private occupancy: OccupancyGrid;
  /** Track assigned zone per NPC for releaseNPC */
  private npcZones: Map<string, string> = new Map();
  /** Cached shuffled road tiles for incremental NPC spawning */
  private roadTilesCache: { x: number; y: number }[] = [];
  private spawnAreaReady = false;
  /** Track active position-update timers per NPC to avoid duplicates */
  private positionTimers: Map<string, Phaser.Time.TimerEvent> = new Map();
  /** Active in-world chat bubbles keyed by NPC id. */
  private chatBubbles: Map<string, WorldChatBubble> = new Map();
  /** Track active message-expiry timers per NPC so newer chats replace older ones cleanly. */
  private messageTimers: Map<string, Phaser.Time.TimerEvent> = new Map();
  /** Track delayed conversation-release timers per NPC to avoid stale releases. */
  private conversationTimers: Map<string, Phaser.Time.TimerEvent> = new Map();
  /** Monotonic version per NPC used to invalidate stale conversation callbacks. */
  private conversationVersions: Map<string, number> = new Map();
  /** Random emotion bubble timer */
  private emotionTimer?: Phaser.Time.TimerEvent;

  constructor(
    scene: Phaser.Scene,
    buildingPositions: BuildingPositions,
    isWalkable: (col: number, row: number) => boolean,
    isRoad: (col: number, row: number) => boolean,
    getRoadType: (col: number, row: number) => "v" | "h" | "none" = () =>
      "none",
  ) {
    this.scene = scene;
    this.buildingPositions = buildingPositions;
    this.isWalkable = isWalkable;
    this.isRoad = isRoad;
    this.getRoadType = getRoadType;
    this.occupancy = new OccupancyGrid();
    this.movement = new MovementSystem(
      scene,
      isWalkable,
      isRoad,
      this.occupancy,
    );

    // Listen for dynamic NPC init from backend via EventBridge
    eventBridge.on("sim:reset-npcs", this.onResetNPCs, this);
    eventBridge.on("sim:add-npc", this.onAddNPC, this);
    eventBridge.on("sim:init-npcs", this.onInitNPCs, this);
    eventBridge.on("sim:npc-move", this.onNPCMove, this);
    eventBridge.on("sim:npc-mood", this.onNPCMood, this);
  }

  private ensureSpawnArea() {
    if (this.spawnAreaReady) return;
    const mc = getMapConfig();
    for (let row = 1; row < mc.rows - 1; row++) {
      for (let col = 1; col < mc.cols - 1; col++) {
        if (this.isRoad(col, row) && this.isWalkable(col, row)) {
          this.roadTilesCache.push({ x: col, y: row });
        }
      }
    }
    for (let i = this.roadTilesCache.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [this.roadTilesCache[i], this.roadTilesCache[j]] = [
        this.roadTilesCache[j],
        this.roadTilesCache[i],
      ];
    }
    this.spawnAreaReady = true;
  }

  private onResetNPCs() {
    this.emotionTimer?.destroy();
    this.emotionTimer = undefined;
    this.movement.destroy();
    for (const bubble of this.chatBubbles.values()) bubble.destroy();
    this.chatBubbles.clear();
    for (const timer of this.positionTimers.values()) timer.destroy();
    this.positionTimers.clear();
    for (const timer of this.messageTimers.values()) timer.destroy();
    this.messageTimers.clear();
    for (const timer of this.conversationTimers.values()) timer.destroy();
    this.conversationTimers.clear();
    this.conversationVersions.clear();
    for (const npc of this.npcs.values()) npc.destroy();
    this.npcs.clear();
    this.npcZones.clear();
    this.occupancy.clear();
    this.roadTilesCache = [];
    this.spawnAreaReady = false;
    this.movement = new MovementSystem(
      this.scene,
      this.isWalkable,
      this.isRoad,
      this.occupancy,
    );
  }

  private onAddNPC(bn: BackendNPC) {
    this.ensureSpawnArea();
    let tileX = -1;
    let tileY = -1;

    for (const candidate of this.roadTilesCache) {
      if (this.occupancy.isOccupied(candidate.x, candidate.y)) continue;
      if (this.hasMinSpacing(candidate.x, candidate.y, MIN_SPAWN_SPACING)) {
        tileX = candidate.x;
        tileY = candidate.y;
        break;
      }
    }
    if (tileX === -1) {
      for (const candidate of this.roadTilesCache) {
        if (!this.occupancy.isOccupied(candidate.x, candidate.y)) {
          tileX = candidate.x;
          tileY = candidate.y;
          break;
        }
      }
    }
    if (tileX === -1) {
      tileX = Math.max(
        CENTER_BOUNDS.minCol,
        Math.min(CENTER_BOUNDS.maxCol, bn.x * getCoordScale()),
      );
      tileY = Math.max(
        CENTER_BOUNDS.minRow,
        Math.min(CENTER_BOUNDS.maxRow, bn.y * getCoordScale()),
      );
    }

    const entity = this.spawnEntity(bn, tileX, tileY, this.npcs.size, this.roadTilesCache);
    this.npcs.set(bn.id, entity);
    const zone = roleToZone(bn.role);
    this.npcZones.set(bn.id, zone);
    this.movement.startRoaming(entity, zone);
  }

  private onInitNPCs(backendNPCs: unknown[]) {
    // If NPCs were already streamed individually, skip batch creation
    if (this.npcs.size > 0) return;

    // Clear any existing NPCs (sprites + movement timers)
    this.movement.destroy();
    for (const timer of this.positionTimers.values()) timer.destroy();
    this.positionTimers.clear();
    for (const bubble of this.chatBubbles.values()) bubble.destroy();
    this.chatBubbles.clear();
    for (const timer of this.messageTimers.values()) timer.destroy();
    this.messageTimers.clear();
    for (const timer of this.conversationTimers.values()) timer.destroy();
    this.conversationTimers.clear();
    this.conversationVersions.clear();
    for (const npc of this.npcs.values()) {
      npc.message = undefined;
      this.emitNPCPosition(npc);
      npc.destroy();
    }
    this.npcs.clear();
    this.npcZones.clear();
    this.occupancy.clear();

    // Re-create movement system (timers were destroyed)
    this.movement = new MovementSystem(
      this.scene,
      this.isWalkable,
      this.isRoad,
      this.occupancy,
    );

    const npcs = backendNPCs as BackendNPC[];

    // Collect all road+walkable tiles for spread-out spawning
    const roadTiles: { x: number; y: number }[] = [];
    for (let row = CENTER_BOUNDS.minRow; row <= CENTER_BOUNDS.maxRow; row++) {
      for (let col = CENTER_BOUNDS.minCol; col <= CENTER_BOUNDS.maxCol; col++) {
        if (this.isRoad(col, row) && this.isWalkable(col, row)) {
          roadTiles.push({ x: col, y: row });
        }
      }
    }

    // Shuffle for random distribution
    for (let i = roadTiles.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [roadTiles[i], roadTiles[j]] = [roadTiles[j], roadTiles[i]];
    }

    for (let i = 0; i < npcs.length; i++) {
      const bn = npcs[i];

      // Find a road tile with adequate spacing from other NPCs
      let tileX = -1;
      let tileY = -1;

      for (const candidate of roadTiles) {
        if (this.occupancy.isOccupied(candidate.x, candidate.y)) continue;
        if (this.hasMinSpacing(candidate.x, candidate.y, MIN_SPAWN_SPACING)) {
          tileX = candidate.x;
          tileY = candidate.y;
          break;
        }
      }

      if (tileX === -1) {
        for (const candidate of roadTiles) {
          if (!this.occupancy.isOccupied(candidate.x, candidate.y)) {
            tileX = candidate.x;
            tileY = candidate.y;
            break;
          }
        }
      }

      if (tileX === -1) {
        tileX = Math.max(
          CENTER_BOUNDS.minCol,
          Math.min(CENTER_BOUNDS.maxCol, bn.x * getCoordScale()),
        );
        tileY = Math.max(
          CENTER_BOUNDS.minRow,
          Math.min(CENTER_BOUNDS.maxRow, bn.y * getCoordScale()),
        );
        const snapped = this.findNearestTile(
          tileX,
          tileY,
          (c, r) => this.isRoad(c, r) && this.isWalkable(c, r),
          10,
        );
        if (snapped) {
          tileX = snapped.x;
          tileY = snapped.y;
        }
      }

      if (tileX === -1) continue;

      const entity = this.spawnEntity(bn, tileX, tileY, i, roadTiles);
      this.npcs.set(bn.id, entity);
      const zone = roleToZone(bn.role);
      this.npcZones.set(bn.id, zone);
      this.movement.startRoaming(entity, zone);
    }

    // Center camera on NPC cluster

    // Random emotion bubbles — every 3-7 seconds pick a random NPC
    this.emotionTimer?.destroy();
    const scheduleEmotionBubble = () => {
      this.emotionTimer = this.scene.time.addEvent({
        delay: 3000 + Math.random() * 4000,
        callback: () => {
          const npcs = [...this.npcs.values()].filter(
            (n) => n.role !== "driver",
          );
          if (npcs.length === 0) return;
          const npc = npcs[Math.floor(Math.random() * npcs.length)];
          const worldX = npc.tileX * TILE_SIZE + TILE_SIZE / 2;
          const worldY = npc.tileY * TILE_SIZE + TILE_SIZE / 2;
          const sentiment =
            npc.sentiment === "happy"
              ? "happy"
              : npc.sentiment === "angry"
                ? "angry"
                : "neutral";
          spawnEmotionBubble(this.scene, worldX, worldY, sentiment);
          scheduleEmotionBubble();
        },
        loop: false,
      });
    };
    scheduleEmotionBubble();
  }

  /** Check whether a car template fits at the given tile position. */
  private canFitCar(
    col: number,
    row: number,
    template: CarTemplate,
  ): boolean {
    if (template.orientation === "portrait") {
      return (
        this.getRoadType(col, row) === "v" &&
        this.getRoadType(col + 1, row) === "v" &&
        this.isWalkable(col, row) &&
        this.isWalkable(col + 1, row) &&
        !this.occupancy.isOccupied(col, row) &&
        !this.occupancy.isOccupied(col + 1, row)
      );
    }
    for (let dc = 0; dc < template.cols; dc++) {
      for (let dr = 0; dr < template.rows; dr++) {
        if (this.getRoadType(col + dc, row + dr) !== "h") return false;
        if (!this.isWalkable(col + dc, row + dr)) return false;
        if (this.occupancy.isOccupied(col + dc, row + dr)) return false;
      }
    }
    return true;
  }

  /**
   * Spawn a single NPC or Car entity depending on role.
   * Shared by both onAddNPC (streaming) and onInitNPCs (batch).
   */
  private spawnEntity(
    bn: BackendNPC,
    tileX: number,
    tileY: number,
    index: number,
    roadTiles: { x: number; y: number }[],
  ): NPC {
    if (bn.role === "driver") {
      const template = CAR_TEMPLATES[index % CAR_TEMPLATES.length];

      // Try to find a road tile where the car template fits
      let carX = -1;
      let carY = -1;
      for (const candidate of roadTiles) {
        if (this.occupancy.isOccupied(candidate.x, candidate.y)) continue;
        if (this.canFitCar(candidate.x, candidate.y, template)) {
          carX = candidate.x;
          carY = candidate.y;
          break;
        }
      }

      // Fallback: snap backend coords to nearest road
      if (carX === -1) {
        carX = tileX;
        carY = tileY;
        const snapped = this.findNearestTile(
          carX,
          carY,
          (c, r) => this.isRoad(c, r) && this.isWalkable(c, r),
          10,
        );
        if (snapped) {
          carX = snapped.x;
          carY = snapped.y;
        }
      }

      const car = new Car(this.scene, bn.id, bn.name, template, carX, carY);
      car.profession = bn.profession;
      car.role = bn.role;
      car.category = bn.category ?? "";
      car.reputation = bn.reputation;
      car.sentiment = moodToSentiment(bn.mood);

      for (let dc = 0; dc < template.cols; dc++) {
        for (let dr = 0; dr < template.rows; dr++) {
          this.occupancy.occupy(
            `${bn.id}_${dc}_${dr}`,
            carX + dc,
            carY + dr,
          );
        }
      }

      return car as unknown as NPC;
    }

    // Regular NPC
    const charType = roleToCharacter(bn.role, index);
    const npc = new NPC(this.scene, bn.id, bn.name, charType, index, tileX, tileY);
    npc.role = bn.role;
    npc.profession = bn.profession;
    npc.category = bn.category ?? "";
    npc.reputation = bn.reputation;
    npc.sentiment = moodToSentiment(bn.mood);
    this.occupancy.occupy(bn.id, tileX, tileY);
    return npc;
  }

  /** Check if position has minimum Manhattan distance from all placed NPCs */
  private hasMinSpacing(x: number, y: number, minDist: number): boolean {
    for (const npc of this.npcs.values()) {
      if (Math.abs(npc.tileX - x) + Math.abs(npc.tileY - y) < minDist) {
        return false;
      }
    }
    return true;
  }

  /** Search outward in rings for a tile matching `predicate` */
  private findNearestTile(
    x: number,
    y: number,
    predicate: (col: number, row: number) => boolean,
    maxRadius = 5,
  ): { x: number; y: number } | null {
    for (let r = 0; r <= maxRadius; r++) {
      for (let dx = -r; dx <= r; dx++) {
        for (let dy = -r; dy <= r; dy++) {
          const nx = x + dx;
          const ny = y + dy;
          if (predicate(nx, ny) && !this.occupancy.isOccupied(nx, ny)) {
            return { x: nx, y: ny };
          }
        }
      }
    }
    return null;
  }

  private emitNPCPosition(npc: NPC) {
    const state = npc.toState();
    if (!state) return;
    eventBridge.emitNPCPosition(state);
  }

  private upsertChatBubble(npc: NPC) {
    if (!npc.message) {
      this.chatBubbles.get(npc.npcId)?.destroy();
      this.chatBubbles.delete(npc.npcId);
      return;
    }

    const existing = this.chatBubbles.get(npc.npcId);
    const category =
      "category" in npc && typeof npc.category === "string"
        ? npc.category
        : undefined;

    if (existing) {
      existing.updateContent(npc.npcName, npc.message, category);
      existing.updateAnchor(npc.x, npc.y);
      return;
    }

    const bubble = new WorldChatBubble(
      this.scene,
      npc.npcName,
      npc.message,
      category,
    );
    bubble.updateAnchor(npc.x, npc.y);
    this.chatBubbles.set(npc.npcId, bubble);
  }

  private clearConversationTimer(npcId: string) {
    this.conversationTimers.get(npcId)?.destroy();
    this.conversationTimers.delete(npcId);
  }

  private bumpConversationVersion(npcId: string): number {
    const next = (this.conversationVersions.get(npcId) ?? 0) + 1;
    this.conversationVersions.set(npcId, next);
    return next;
  }

  private onNPCMove(data: { npcId: string; toX: number; toY: number }) {
    const npc = this.npcs.get(data.npcId);
    if (!npc) return;
    const targetX = data.toX * getCoordScale();
    const targetY = data.toY * getCoordScale();
    this.stepToward(npc, targetX, targetY, 5);
  }

  private onNPCMood(data: { npcId: string; mood: string }) {
    const npc = this.npcs.get(data.npcId);
    if (!npc) return;
    npc.sentiment = moodToSentiment(data.mood);
  }

  getNPC(id: string): NPC | undefined {
    return this.npcs.get(id);
  }

  getAllNPCs(): NPC[] {
    return [...this.npcs.values()];
  }

  /** Re-emit positions for NPCs with active bubbles so camera pan/zoom stays in sync. */
  refreshActiveBubblePositions() {
    for (const npc of this.npcs.values()) {
      if (!npc.message) {
        this.upsertChatBubble(npc);
        continue;
      }
      this.upsertChatBubble(npc);
    }
  }

  /** Override movement: NPC stops roaming and enters protest/override state at current position */
  sendTo(npcId: string, _targetCol: number, _targetRow: number) {
    const npc = this.npcs.get(npcId);
    if (!npc) return;

    this.movement.override(npcId);
    npc.npcState = "protesting";
    // NPC stays at current position — no teleporting across the map
  }

  /** Release an NPC back to normal roaming in their assigned zone */
  releaseNPC(npcId: string) {
    const npc = this.npcs.get(npcId);
    if (!npc) return;
    this.clearConversationTimer(npcId);
    this.bumpConversationVersion(npcId);
    npc.npcState = "idle";
    this.movement.release(npcId);
    this.movement.startRoaming(npc, this.npcZones.get(npcId));
  }

  /** Show chat bubble via EventBridge → React */
  showMessage(npcId: string, message: string) {
    const npc = this.npcs.get(npcId);
    if (!npc) return;

    npc.message = message;
    this.upsertChatBubble(npc);
    this.emitNPCPosition(npc);

    // Cancel existing position timer for this NPC if any
    this.positionTimers.get(npcId)?.destroy();
    this.positionTimers.delete(npcId);
    // Cancel any prior expiry timer so a newer message cannot be cleared by an older one.
    this.messageTimers.get(npcId)?.destroy();
    this.messageTimers.delete(npcId);

    // Continuously emit position updates while message is active so React bubble follows NPC
    const posTimer = this.scene.time.addEvent({
      delay: 16,
      callback: () => {
        if (!npc.message) {
          posTimer.destroy();
          this.positionTimers.delete(npcId);
          this.emitNPCPosition(npc);
          return;
        }
        this.emitNPCPosition(npc);
      },
      loop: true,
    });
    this.positionTimers.set(npcId, posTimer);

    // Clear message after display time
    const messageTimer = this.scene.time.delayedCall(5000, () => {
      npc.message = undefined;
      this.upsertChatBubble(npc);
      this.messageTimers.delete(npcId);
    });
    this.messageTimers.set(npcId, messageTimer);
  }

  /** Walk npcA toward npcB, pause for conversation, then release both */
  converseWith(npcIdA: string, npcIdB: string) {
    const npcA = this.npcs.get(npcIdA);
    const npcB = this.npcs.get(npcIdB);
    if (!npcA || !npcB) return;

    const versionA = this.bumpConversationVersion(npcIdA);
    const versionB = this.bumpConversationVersion(npcIdB);
    this.clearConversationTimer(npcIdA);
    this.clearConversationTimer(npcIdB);

    // Override both so they stop roaming
    this.movement.override(npcIdA);
    this.movement.override(npcIdB);

    // Drivers stay in their lane — skip walk-toward to avoid leaving road tiles
    const eitherIsDriver = npcA.role === "driver" || npcB.role === "driver";
    const walkPromise = eitherIsDriver
      ? Promise.resolve()
      : (() => {
          const adj = this.findAdjacentWalkable(
            npcB.tileX,
            npcB.tileY,
            npcA.npcId,
          );
          const goalX = adj ? adj.x : npcB.tileX;
          const goalY = adj ? adj.y : npcB.tileY;
          return this.stepToward(npcA, goalX, goalY, 5);
        })();

    walkPromise.then(() => {
      if (
        this.conversationVersions.get(npcIdA) !== versionA ||
        this.conversationVersions.get(npcIdB) !== versionB
      ) {
        return;
      }

      // Face each other
      if (npcA.tileX < npcB.tileX) {
        npcA.face("right");
        npcB.face("left");
      } else if (npcA.tileX > npcB.tileX) {
        npcA.face("left");
        npcB.face("right");
      } else if (npcA.tileY < npcB.tileY) {
        npcA.face("down");
        npcB.face("up");
      } else {
        npcA.face("up");
        npcB.face("down");
      }

      // Release both after chat bubble fades (6s — slightly after 5s message timeout)
      const scheduleRelease = (npcId: string, version: number) => {
        const timer = this.scene.time.delayedCall(6000, () => {
          if (
            this.conversationVersions.get(npcId) !== version ||
            this.conversationTimers.get(npcId) !== timer
          ) {
            return;
          }
          this.conversationTimers.delete(npcId);
          this.releaseNPC(npcId);
        });
        this.conversationTimers.set(npcId, timer);
      };

      scheduleRelease(npcIdA, versionA);
      scheduleRelease(npcIdB, versionB);
    });
  }

  /** Walk an NPC step-by-step toward a target using A* pathfinding */
  private async stepToward(
    npc: NPC,
    targetX: number,
    targetY: number,
    maxSteps: number,
  ) {
    // Snap goal to walkable tile if it's inside a building
    let goalX = targetX;
    let goalY = targetY;
    if (!this.isWalkable(goalX, goalY)) {
      const snapped = this.findNearestTile(goalX, goalY, (c, r) =>
        this.isWalkable(c, r),
      );
      if (!snapped) return;
      goalX = snapped.x;
      goalY = snapped.y;
    }

    const path = findPath(
      { col: npc.tileX, row: npc.tileY },
      { col: goalX, row: goalY },
      this.isWalkable,
    );
    if (!path || path.length === 0) return;

    for (let i = 0; i < Math.min(maxSteps, path.length); i++) {
      const next = path[i];
      // Re-check occupancy at step time — another NPC may have moved here
      if (this.occupancy.isOccupiedByOther(npc.npcId, next.col, next.row))
        break;
      this.occupancy.occupy(npc.npcId, next.col, next.row);
      await npc.walkTo(next.col, next.row);
    }
  }

  /** Find a walkable, unoccupied tile adjacent to (col, row) */
  private findAdjacentWalkable(
    col: number,
    row: number,
    forNpcId: string,
  ): { x: number; y: number } | null {
    for (const [dx, dy] of [
      [0, -1],
      [0, 1],
      [-1, 0],
      [1, 0],
    ] as const) {
      const nx = col + dx;
      const ny = row + dy;
      if (
        this.isWalkable(nx, ny) &&
        !this.occupancy.isOccupiedByOther(forNpcId, nx, ny)
      ) {
        return { x: nx, y: ny };
      }
    }
    return null;
  }

  /** Get building positions for effects */
  getBuildings(): BuildingPositions {
    return this.buildingPositions;
  }

  destroy() {
    this.emotionTimer?.destroy();
    this.emotionTimer = undefined;
    eventBridge.off("sim:reset-npcs", this.onResetNPCs, this);
    eventBridge.off("sim:add-npc", this.onAddNPC, this);
    eventBridge.off("sim:init-npcs", this.onInitNPCs, this);
    eventBridge.off("sim:npc-move", this.onNPCMove, this);
    eventBridge.off("sim:npc-mood", this.onNPCMood, this);
    for (const t of this.positionTimers.values()) t.destroy();
    this.positionTimers.clear();
    for (const bubble of this.chatBubbles.values()) bubble.destroy();
    this.chatBubbles.clear();
    for (const t of this.messageTimers.values()) t.destroy();
    this.messageTimers.clear();
    for (const t of this.conversationTimers.values()) t.destroy();
    this.conversationTimers.clear();
    this.conversationVersions.clear();
    this.movement.destroy();
    for (const npc of this.npcs.values()) {
      npc.destroy();
    }
    this.npcs.clear();
    this.npcZones.clear();
    this.occupancy.clear();
  }
}
