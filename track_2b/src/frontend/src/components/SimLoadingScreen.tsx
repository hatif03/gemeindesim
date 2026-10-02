"use client";

import { AnimatePresence, motion } from "motion/react";
import type { SetupProgress } from "@/hooks/useSimulation";
import { Particles } from "./Particles/Particles";

interface SimLoadingScreenProps {
  isVisible: boolean;
  stage?: SetupProgress["stage"];
  npcsReady?: number;
  numNpcs?: number;
  label?: string;
}

export function SimLoadingScreen({ isVisible, stage, npcsReady = 0, numNpcs = 0, label }: SimLoadingScreenProps) {
  const stageLabel = label ||
    (stage === "analyzing" ? "Analyzing policy..." :
    stage === "generating" ? `Generating personalities... ${npcsReady}${numNpcs > 0 ? `/${numNpcs}` : ""}` :
    stage === "ready" ? "Loading world..." :
    "Connecting...");

  // Evenly distribute progress across known stages based on label content
  function getFill(): number {
    if (stage === "waiting") return 2;
    if (stage === "ready") return 100;
    const l = label || "";
    if (l.includes("Analyzing policy")) return 12;
    if (l.includes("Starting simulation")) return 20;
    if (l.includes("Extracted")) return 30;
    if (l.includes("random residents")) return 40;
    if (l.includes("personalities") && !l.includes("/")) return 46;
    if (stage === "generating" && numNpcs > 0) {
      return 46 + Math.round((npcsReady / numNpcs) * 36); // 46→82
    }
    if (l.includes("Building social network")) return 88;
    if (stage === "analyzing") return 12;
    return 8; // connected but no label yet
  }
  const fill = getFill();
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8 }}
          className="fixed inset-0 z-[200] flex items-center justify-center font-pixel"
          style={{ background: "#1a1208" }}
        >
          <div className="pointer-events-none absolute inset-0 z-[1]">
            <Particles
              variant="dust"
              className="h-full w-full min-h-0"
              quantity={40}
              color="#FDF5E6"
              alphaMin={0.03}
              alphaMax={0.1}
              size={0.4}
              vx={0.02}
              vy={0.01}
            />
          </div>
          <div className="relative z-10 flex flex-col items-center text-center space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 1.2 }}
              className="text-[14px] font-pixel uppercase tracking-[0.3em]"
              style={{
                color: "#D4A520",
                textShadow:
                  "0 0 8px rgba(212,165,32,0.5), 0 0 16px rgba(212,165,32,0.25)",
              }}
            >
              {"\u2605"} Linden {"\u2605"}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0, duration: 1.0 }}
              className="text-[20px] font-pixel uppercase tracking-wide"
              style={{ color: "#E8D5A3" }}
            >
              Day 1 {"\u2014"} Spring
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 1, 0.6, 1] }}
              transition={{
                delay: 1.5,
                duration: 2,
                repeat: Number.POSITIVE_INFINITY,
              }}
              className="text-[10px] font-mono uppercase tracking-[0.3em]"
              style={{ color: "#8B7355" }}
            >
              {stageLabel}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.8, duration: 0.8 }}
              className="w-64"
            >
              <div
                className="h-4 overflow-hidden rounded-sm"
                style={{
                  background: "#E8D5A3",
                  border: "2px solid #6B4226",
                  boxShadow:
                    "inset 1px 1px 0 rgba(196,164,108,.4), 2px 2px 0 rgba(61,37,16,.3)",
                }}
              >
                <motion.div
                  className="h-full rounded-sm progress-glow"
                  animate={{ width: `${fill}%` }}
                  transition={{ duration: 0.7, ease: "easeOut" }}
                  style={{ background: "linear-gradient(90deg, #D4A520, #C97D1A)" }}
                />
              </div>
              {stage === "generating" && numNpcs > 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-between text-[8px] font-pixel mt-1 px-0.5"
                  style={{ color: "#A0824A" }}
                >
                  <span>RESIDENTS</span>
                  <span>{npcsReady}/{numNpcs}</span>
                </motion.div>
              )}
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
