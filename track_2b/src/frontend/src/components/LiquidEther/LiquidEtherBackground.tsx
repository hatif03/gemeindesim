"use client";

import dynamic from "next/dynamic";

const LiquidEther = dynamic(() => import("./LiquidEther"), { ssr: false });

export default function LiquidEtherBackground() {
  return (
    <div className="fixed inset-0 z-0">
      <LiquidEther
        mouseForce={20}
        cursorSize={100}
        isViscous
        viscous={30}
        colors={["#694ed4", "#FF9FFC", "#B19EEF"]}
        autoDemo
        autoSpeed={0.5}
        autoIntensity={2.2}
        isBounce={false}
        resolution={0.5}
      />
    </div>
  );
}
