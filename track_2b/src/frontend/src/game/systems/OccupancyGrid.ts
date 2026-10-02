export class OccupancyGrid {
  private npcPositions: Map<string, string> = new Map();
  private tileOccupants: Map<string, string> = new Map();

  /** Reserve a tile for an NPC. Auto-releases old position first. */
  occupy(npcId: string, col: number, row: number): void {
    this.release(npcId);
    const key = `${col},${row}`;
    // Evict any previous occupant so their npcPositions entry stays consistent
    const prev = this.tileOccupants.get(key);
    if (prev !== undefined && prev !== npcId) {
      this.npcPositions.delete(prev);
    }
    this.npcPositions.set(npcId, key);
    this.tileOccupants.set(key, npcId);
  }

  /** Release the tile occupied by this NPC. */
  release(npcId: string): void {
    const key = this.npcPositions.get(npcId);
    if (key !== undefined) {
      this.tileOccupants.delete(key);
      this.npcPositions.delete(npcId);
    }
  }

  /** Is any NPC on this tile? */
  isOccupied(col: number, row: number): boolean {
    return this.tileOccupants.has(`${col},${row}`);
  }

  /** Is another NPC (not npcId) on this tile? */
  isOccupiedByOther(npcId: string, col: number, row: number): boolean {
    const occupant = this.tileOccupants.get(`${col},${row}`);
    return occupant !== undefined && occupant !== npcId;
  }

  /** Clear all tracking data. */
  clear(): void {
    this.npcPositions.clear();
    this.tileOccupants.clear();
  }
}
