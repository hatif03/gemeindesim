import type { SimEvent } from "@/types";
import { eventBridge } from "../bridge/EventBridge";
import { GAME_HEIGHT, GAME_WIDTH, TILE_SIZE } from "../config";
import { ClosureEffect } from "../effects/ClosureEffect";
import {
  spawnBankruptcy,
  spawnMoneyGain,
  spawnMoneyLoss,
  spawnPhaseFlash,
} from "../effects/EconomicEffects";
import { PriceSpikeEffect } from "../effects/PriceSpikeEffect";
import { ProtestEffect } from "../effects/ProtestEffect";
import type { NPCManager } from "../systems/NPCManager";

/**
 * Listens for SimEvents via EventBridge and dispatches visual effects.
 * Connects the event stream from React/useSimulation to the Phaser world.
 */
export class SimEventHandler {
  private scene: Phaser.Scene;
  private npcManager: NPCManager;
  private protestEffect: ProtestEffect;
  private closureEffect: ClosureEffect;
  private priceSpikeEffect: PriceSpikeEffect;

  constructor(scene: Phaser.Scene, npcManager: NPCManager) {
    this.scene = scene;
    this.npcManager = npcManager;
    this.protestEffect = new ProtestEffect(scene, npcManager);
    this.closureEffect = new ClosureEffect(scene);
    this.priceSpikeEffect = new PriceSpikeEffect(scene);

    eventBridge.on("sim:event", this.onSimEvent, this);
    eventBridge.on("sim:phase-change", this.onPhaseChange, this);
  }

  private onPhaseChange(data: { phase: number; round: number; sentiment?: number }) {
    spawnPhaseFlash(this.scene, data.phase, GAME_WIDTH, GAME_HEIGHT, data.sentiment);
  }

  private onSimEvent(event: SimEvent) {
    // Always show chat bubble if there's a message and an agent
    if (event.message && event.agentId !== "system") {
      // Use agentId directly — backend NPC IDs match NPCManager keys
      const npcId = event.agentId;
      this.npcManager.showMessage(npcId, event.message);

      // If this event has a valid targetNpcId, trigger conversation between speaker and target
      if (event.targetNpcId && event.targetNpcId !== npcId) {
        // Only converseWith if the target NPC actually exists in our NPC list
        const allNPCs = this.npcManager.getAllNPCs();
        const targetExists = allNPCs.some((n) => n.npcId === event.targetNpcId);
        if (targetExists) {
          this.npcManager.converseWith(npcId, event.targetNpcId);
        }
      }
    }

    switch (event.type) {
      case "protest":
        this.handleProtest();
        break;
      case "strike":
        this.handleStrike();
        break;
      case "closure":
        this.handleClosure();
        break;
      case "price_change":
        this.handlePriceChange(event.message);
        break;
      case "layoff":
        this.handleLayoff(event.agentId);
        break;
      case "policy_response":
      case "reaction":
      case "mood_shift":
        // No additional visual effect — chat bubble already shown above
        break;
    }
  }

  private handleProtest() {
    // Dynamically pick angry/worried NPCs for the protest (up to 5)
    const allNPCs = this.npcManager.getAllNPCs();
    const protestNPCs = allNPCs
      .filter((n) => n.sentiment === "angry" || n.sentiment === "worried")
      .slice(0, 5);
    // Fallback: if nobody is angry/worried, pick first 3 NPCs
    if (protestNPCs.length === 0) {
      protestNPCs.push(...allNPCs.slice(0, 3));
    }
    const protestNPCIds = protestNPCs.map((n) => n.npcId);
    this.protestEffect.trigger(protestNPCIds);

    // Floating bankruptcy text above each protesting NPC
    for (const npc of protestNPCs) {
      const worldX = npc.tileX * TILE_SIZE + TILE_SIZE / 2;
      const worldY = npc.tileY * TILE_SIZE;
      spawnBankruptcy(this.scene, worldX, worldY);
    }
  }

  private handleStrike() {
    // Strike: gather NPCs whose role contains "worker" (up to 3)
    const allNPCs = this.npcManager.getAllNPCs();
    const strikeNPCs = allNPCs
      .filter((n) => n.role.toLowerCase().includes("worker"))
      .slice(0, 3);
    // Fallback: pick first 2 NPCs if no workers found
    if (strikeNPCs.length === 0) {
      strikeNPCs.push(...allNPCs.slice(0, 2));
    }
    const strikeIds = strikeNPCs.map((n) => n.npcId);

    const buildings = this.npcManager.getBuildings();
    const factory = buildings.factories[0];
    if (!factory) return;

    for (const id of strikeIds) {
      const targetCol = factory.x + (strikeIds.indexOf(id) % 3);
      const targetRow = factory.y + 2;
      this.npcManager.sendTo(id, targetCol, targetRow);
    }

    // Release after a while
    this.scene.time.delayedCall(8000, () => {
      for (const id of strikeIds) {
        this.npcManager.releaseNPC(id);
      }
    });
  }

  private handleLayoff(npcId: string) {
    const allNPCs = this.npcManager.getAllNPCs();
    const npc = allNPCs.find((n) => n.npcId === npcId);
    if (!npc) return;
    const worldX = npc.tileX * TILE_SIZE + TILE_SIZE / 2;
    const worldY = npc.tileY * TILE_SIZE;
    spawnBankruptcy(this.scene, worldX, worldY);
  }

  private handleClosure() {
    const shops = this.npcManager.getBuildings().shops;
    if (shops.length > 0) {
      const shop = shops[Math.floor(Math.random() * shops.length)];
      this.closureEffect.trigger(shop.x, shop.y);
      spawnBankruptcy(
        this.scene,
        shop.x * TILE_SIZE + TILE_SIZE,
        shop.y * TILE_SIZE,
      );
    } else {
      const allNPCs = this.npcManager.getAllNPCs();
      const bizNPC =
        allNPCs.find(
          (n) => n.role === "business_owner" || n.role === "shopkeeper",
        ) ?? allNPCs[0];
      if (!bizNPC) return;
      spawnBankruptcy(
        this.scene,
        bizNPC.tileX * TILE_SIZE + TILE_SIZE / 2,
        bizNPC.tileY * TILE_SIZE,
      );
    }
  }

  private handlePriceChange(message: string) {
    const allNPCs = this.npcManager.getAllNPCs();
    const shops = this.npcManager.getBuildings().shops;

    let worldX: number;
    let worldY: number;

    if (shops.length > 0) {
      const shop = shops[Math.floor(Math.random() * shops.length)];
      worldX = shop.x * TILE_SIZE + TILE_SIZE;
      worldY = shop.y * TILE_SIZE;
      this.priceSpikeEffect.trigger(shop.x, shop.y, message);
    } else if (allNPCs.length > 0) {
      const npc = allNPCs[Math.floor(Math.random() * allNPCs.length)];
      worldX = npc.tileX * TILE_SIZE + TILE_SIZE / 2;
      worldY = npc.tileY * TILE_SIZE;
    } else {
      return;
    }

    const isNegative =
      /decrease|drop|lower|cut|reduc|down|fell|decline/i.test(message);
    if (isNegative) {
      spawnMoneyGain(this.scene, worldX, worldY);
    } else {
      spawnMoneyLoss(this.scene, worldX, worldY);
    }
  }

  destroy() {
    eventBridge.off("sim:event", this.onSimEvent, this);
    eventBridge.off("sim:phase-change", this.onPhaseChange, this);
  }
}
