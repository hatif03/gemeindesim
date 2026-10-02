"use client";

import { useEffect, useRef } from "react";
import { GAME_HEIGHT, GAME_WIDTH, SCALE_FACTOR } from "@/game/config";

/**
 * GameCanvas wraps the Phaser game instance.
 * Agent A builds the real scenes (BootScene, WorldScene) in a separate worktree.
 * This component uses a fallback placeholder scene until those are available.
 */
export function GameCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<unknown>(null);

  useEffect(() => {
    if (!containerRef.current || gameRef.current) return;

    let destroyed = false;

    async function initGame() {
      const Phaser = await import("phaser");
      const { createGameConfig, setSelectedMap } = await import(
        "@/game/config"
      );

      // Read map param from URL and set before Phaser initializes
      const params = new URLSearchParams(window.location.search);
      const mapParam = params.get("map");
      if (
        mapParam === "pico8" ||
        mapParam === "ccity" ||
        mapParam === "citypack"
      ) {
        setSelectedMap(mapParam);
      }

      const proceduralParam = params.get("procedural");
      if (proceduralParam === "true") {
        const { setProceduralMap } = await import("@/game/config");
        setProceduralMap(true);
      }

      // Try to load the real scenes from Agent A's build
      // turbopackOptional suppresses build errors when these files don't exist yet
      let scenes: Phaser.Types.Scenes.SceneType[];
      try {
        const { BootScene } = await import(
          /* turbopackOptional: true */ "@/game/scenes/BootScene"
        );
        const { WorldScene } = await import(
          /* turbopackOptional: true */ "@/game/scenes/WorldScene"
        );
        scenes = [BootScene, WorldScene];
      } catch {
        // Fallback placeholder scene with warm Stardew theme
        scenes = [
          class PlaceholderScene extends Phaser.Scene {
            constructor() {
              super({ key: "PlaceholderScene" });
            }
            create() {
              this.cameras.main.setBackgroundColor("#E8D5A3");
              const g = this.add.graphics();
              g.lineStyle(1, 0xc4a46c, 0.3);
              for (let x = 0; x <= GAME_WIDTH; x += 16) {
                g.moveTo(x, 0);
                g.lineTo(x, GAME_HEIGHT);
              }
              for (let y = 0; y <= GAME_HEIGHT; y += 16) {
                g.moveTo(0, y);
                g.lineTo(GAME_WIDTH, y);
              }
              g.strokePath();

              // Title
              const title = this.add
                .text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 20, "GEMEINDESIM", {
                  fontSize: "28px",
                  color: "#5B3A1E",
                  fontFamily: "monospace",
                  fontStyle: "bold",
                })
                .setOrigin(0.5);

              title.setShadow(1, 1, "#A0824A", 4, true, true);

              this.add
                .text(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 16, "Loading city...", {
                  fontSize: "12px",
                  color: "#8B7355",
                  fontFamily: "monospace",
                })
                .setOrigin(0.5);

              // Pulsing golden dot
              const dot = this.add.circle(
                GAME_WIDTH / 2,
                GAME_HEIGHT / 2 + 40,
                3,
                0xd4a520,
              );
              this.tweens.add({
                targets: dot,
                alpha: 0.2,
                duration: 800,
                yoyo: true,
                repeat: -1,
              });
            }
          },
        ];
      }

      if (destroyed) return;

      const config = createGameConfig(containerRef.current!, scenes);
      gameRef.current = new Phaser.Game(config);
    }

    initGame();

    return () => {
      destroyed = true;
      if (gameRef.current) {
        (gameRef.current as { destroy: (b: boolean) => void }).destroy(true);
        gameRef.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      data-testid="game-canvas"
      className="overflow-hidden pixel-crisp w-full h-full"
    />
  );
}
