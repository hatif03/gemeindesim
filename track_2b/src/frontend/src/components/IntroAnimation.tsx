"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";

interface IntroAnimationProps {
  onComplete: () => void;
}

export default function IntroAnimation({ onComplete }: IntroAnimationProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // 1. Start: parchment black-out for 1s
    const showTimer = setTimeout(() => setIsVisible(true), 1000);

    // 2. Reveal: visible for 5s (1s + 5s = 6s total)
    const hideTimer = setTimeout(() => setIsVisible(false), 6000);

    // 3. Complete: fade-out duration + extra buffer (6s + 2s = 8s total)
    const completeTimer = setTimeout(() => onComplete(), 8000);

    return () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
      clearTimeout(completeTimer);
    };
  }, [onComplete]);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center font-pixel"
      style={{ background: "#1a1208" }}
    >
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, filter: "blur(15px)" }}
            animate={{
              opacity: 1,
              scale: 1,
              filter: "blur(0px)",
              transition: {
                duration: 3,
                ease: [0.16, 1, 0.3, 1],
                opacity: { duration: 2, delay: 0.3 },
              },
            }}
            exit={{
              opacity: 0,
              scale: 1.05,
              filter: "blur(10px)",
              transition: { duration: 2, ease: [0.7, 0, 0.84, 0] },
            }}
            className="flex flex-col items-center text-center space-y-12"
          >
            {/* Metadata Lines */}
            <motion.div
              animate={{ opacity: [0.7, 1, 0.7] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="space-y-6 text-[16px] tracking-normal"
              style={{
                color: "#E8D5A3",
                textShadow:
                  "0 0 8px rgba(212,165,32,0.5), 0 0 16px rgba(212,165,32,0.25)",
              }}
            >
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{
                  opacity: 1,
                  y: 0,
                  transition: { delay: 1.0, duration: 2.0 },
                }}
                className="flex justify-center gap-12"
              >
                <span className="font-normal">{"\u00A9"}2025</span>
                <span className="font-bold" style={{ color: "#D4A520" }}>
                  GemeindeSim.
                </span>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{
                  opacity: 1,
                  y: 0,
                  transition: { delay: 1.5, duration: 2.0 },
                }}
              >
                <span className="font-normal">{"\u00A9"}2025-2026</span>{" "}
                <span className="font-bold" style={{ color: "#D4A520" }}>
                  Hack Apertus
                </span>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{
                  opacity: 1,
                  y: 0,
                  transition: { delay: 2.0, duration: 2.0 },
                }}
                className="font-bold"
              >
                All rights reserved. Track 2B.
              </motion.div>
            </motion.div>

            {/* Main Title Year */}
            <motion.div
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{
                opacity: 1,
                scale: 1,
                transition: {
                  delay: 2.8,
                  duration: 2.0,
                  ease: [0.16, 1, 0.3, 1],
                },
              }}
              className="text-7xl font-bold tracking-widest pt-4"
              style={{
                color: "#D4A520",
                textShadow:
                  "0 0 15px rgba(212,165,32,0.8), 0 0 30px rgba(212,165,32,0.4), 0 0 50px rgba(212,165,32,0.25)",
                filter: "drop-shadow(0 0 10px rgba(212,165,32,0.4))",
              }}
            >
              2026
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
