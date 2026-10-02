"use client";

import dynamic from "next/dynamic";

const NodeCanvas = dynamic(() => import("./index"), { ssr: false });

interface NodeCanvasClientProps {
  onSimulateStart?: () => void;
}

export default function NodeCanvasClient({
  onSimulateStart,
}: NodeCanvasClientProps) {
  return (
    <div style={{ width: "100%", height: "100%" }}>
      <NodeCanvas onSimulateStart={onSimulateStart} />
    </div>
  );
}
