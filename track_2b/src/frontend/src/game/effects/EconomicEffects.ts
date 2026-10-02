import * as Phaser from "phaser";

/** Spawn a floating text that drifts up and fades — SimCity style */
export function floatText(
  scene: Phaser.Scene,
  worldX: number,
  worldY: number,
  text: string,
  color: string = "#ffffff",
  fontSize = 14,
) {
  const txt = scene.add
    .text(worldX, worldY, text, {
      fontSize: `${fontSize}px`,
      color,
      fontFamily: "monospace",
      stroke: "#000000",
      strokeThickness: 2,
    })
    .setDepth(20)
    .setOrigin(0.5, 1);

  scene.tweens.add({
    targets: txt,
    y: worldY - 60,
    alpha: { from: 1, to: 0 },
    duration: 2000,
    ease: "Power2",
    onComplete: () => txt.destroy(),
  });
}

/** Protest / closure → persistent bankruptcy marker */
export function spawnBankruptcy(
  scene: Phaser.Scene,
  worldX: number,
  worldY: number,
) {
  const txt = scene.add
    .text(worldX, worldY - 8, "!! BANKRUPT", {
      fontSize: "11px",
      color: "#ff4444",
      fontFamily: "monospace",
      stroke: "#000000",
      strokeThickness: 2,
      backgroundColor: "#00000066",
      padding: { x: 3, y: 2 },
    })
    .setDepth(20)
    .setOrigin(0.5, 1)
    .setScale(0);

  // Pop in animation — then stays forever
  scene.tweens.add({
    targets: txt,
    scaleX: 1,
    scaleY: 1,
    duration: 400,
    ease: "Back.easeOut",
  });

  floatText(
    scene,
    worldX + Phaser.Math.Between(-15, 15),
    worldY - 20,
    "CRASH",
    "#ff6666",
    12,
  );
}

/** Price spike → money draining */
export function spawnMoneyLoss(
  scene: Phaser.Scene,
  worldX: number,
  worldY: number,
) {
  floatText(scene, worldX, worldY, "-$$$", "#ff8800", 14);
}

/** Price drop / good economy → money in */
export function spawnMoneyGain(
  scene: Phaser.Scene,
  worldX: number,
  worldY: number,
) {
  floatText(scene, worldX, worldY, "+$", "#44ff88", 14);
}

/** Phase change → full screen flash with sentiment-driven color */
export function spawnPhaseFlash(
  scene: Phaser.Scene,
  phase: number,
  gameW: number,
  gameH: number,
  sentiment?: number,
) {
  const s = sentiment ?? 0.5;
  const color = s >= 0.6 ? 0x00ff44 : s <= 0.35 ? 0xff2200 : 0xff8800;

  const posLabels: Record<number, string> = {
    1: "POLICY WELCOMED",
    2: "GROWTH EMERGING",
    3: "PROSPERITY",
  };
  const midLabels: Record<number, string> = {
    1: "POLICY ANNOUNCED",
    2: "ECONOMIC SHIFT",
    3: "SOCIAL RECKONING",
  };
  const negLabels: Record<number, string> = {
    1: "PUBLIC CONCERN",
    2: "ECONOMIC PRESSURE",
    3: "SOCIAL CRISIS",
  };
  const labelMap = s >= 0.6 ? posLabels : s <= 0.35 ? negLabels : midLabels;
  const labelText = labelMap[phase] ?? `PHASE ${phase}`;

  const rect = scene.add
    .rectangle(gameW / 2, gameH / 2, gameW * 4, gameH * 4, color, 0.3)
    .setDepth(6)
    .setScrollFactor(0);
  const label = scene.add
    .text(gameW / 2, gameH / 2, labelText, {
      fontSize: "22px",
      color: "#ffffff",
      fontFamily: "monospace",
      stroke: "#000000",
      strokeThickness: 3,
    })
    .setDepth(7)
    .setOrigin(0.5)
    .setScrollFactor(0);

  scene.tweens.add({
    targets: [rect, label],
    alpha: { from: 1, to: 0 },
    duration: 2500,
    ease: "Power2",
    onComplete: () => {
      rect.destroy();
      label.destroy();
    },
  });
}

/** Emotion bubble above NPC head */
export function spawnEmotionBubble(
  scene: Phaser.Scene,
  worldX: number,
  worldY: number,
  sentiment: string,
) {
  const label =
    sentiment === "angry" ? ">:(" : sentiment === "happy" ? ":)" : ":|";
  const txt = scene.add
    .text(worldX, worldY - 24, label, {
      fontSize: "14px",
      fontFamily: "monospace",
      stroke: "#000000",
      strokeThickness: 2,
      color:
        sentiment === "angry"
          ? "#ff4444"
          : sentiment === "happy"
            ? "#44ff88"
            : "#cccccc",
    })
    .setDepth(20)
    .setOrigin(0.5, 1);
  scene.tweens.add({
    targets: txt,
    y: worldY - 70,
    alpha: { from: 1, to: 0 },
    scaleX: { from: 0.5, to: 1.2 },
    scaleY: { from: 0.5, to: 1.2 },
    duration: 1800,
    ease: "Back.easeOut",
    onComplete: () => txt.destroy(),
  });
}
