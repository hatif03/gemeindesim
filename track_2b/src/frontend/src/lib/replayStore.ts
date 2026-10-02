import type { SavedSimulation } from "@/types/backend";

let _recording: SavedSimulation | null = null;

export function setReplayData(data: SavedSimulation) {
  _recording = data;
}

export function getReplayData(): SavedSimulation | null {
  return _recording;
}

export function clearReplayData() {
  _recording = null;
}
