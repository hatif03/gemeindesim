import * as Phaser from "phaser";
import {
  type MapType,
  MAP_CONFIGS,
  GAME_WIDTH,
  GAME_HEIGHT,
  SCALE_FACTOR,
  CENTER_BOUNDS,
  selectedMap,
  proceduralMap,
  setSelectedMap,
  setProceduralMap,
  getMapConfig,
  TILE_SIZE,
  MAP_COLS,
  MAP_ROWS,
} from "./constants";

export {
  type MapType,
  MAP_CONFIGS,
  GAME_WIDTH,
  GAME_HEIGHT,
  SCALE_FACTOR,
  CENTER_BOUNDS,
  selectedMap,
  proceduralMap,
  setSelectedMap,
  setProceduralMap,
  getMapConfig,
  TILE_SIZE,
  MAP_COLS,
  MAP_ROWS,
};

export function createGameConfig(
  parent: string | HTMLElement,
  scenes: Phaser.Types.Scenes.SceneType[],
): Phaser.Types.Core.GameConfig {
  return {
    type: Phaser.CANVAS,
    width: GAME_WIDTH,
    height: GAME_HEIGHT,
    parent,
    pixelArt: true,
    roundPixels: true,
    scale: {
      mode: Phaser.Scale.ENVELOP,
      autoCenter: Phaser.Scale.CENTER_BOTH,
    },
    scene: scenes,
    backgroundColor: "#1a1510",
  };
}
