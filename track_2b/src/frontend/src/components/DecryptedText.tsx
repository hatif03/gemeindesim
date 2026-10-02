"use client";

import { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { motion } from "motion/react";
import type { HTMLMotionProps } from "motion/react";

const styles = {
  wrapper: {
    display: "inline-block",
    whiteSpace: "pre-wrap" as const,
  },
  srOnly: {
    position: "absolute" as const,
    width: "1px",
    height: "1px",
    padding: 0,
    margin: "-1px",
    overflow: "hidden",
    clip: "rect(0,0,0,0)",
    border: 0,
  },
};

interface DecryptedTextProps extends HTMLMotionProps<"span"> {
  text: string;
  speed?: number;
  maxIterations?: number;
  sequential?: boolean;
  revealDirection?: "start" | "end" | "center";
  useOriginalCharsOnly?: boolean;
  characters?: string;
  className?: string;
  parentClassName?: string;
  encryptedClassName?: string;
  animateOn?: "view" | "hover" | "inViewHover" | "click" | "external";
  clickMode?: "once" | "toggle";
  trigger?: boolean;
}

type Direction = "forward" | "reverse";

export default function DecryptedText({
  text,
  speed = 50,
  maxIterations = 10,
  sequential = false,
  revealDirection = "start",
  useOriginalCharsOnly = false,
  characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+",
  className = "",
  parentClassName = "",
  encryptedClassName = "",
  animateOn = "hover",
  clickMode = "once",
  trigger = false,
  ...props
}: DecryptedTextProps) {
  const [displayText, setDisplayText] = useState<string>(text);
  const [isAnimating, setIsAnimating] = useState<boolean>(false);
  const [revealedIndices, setRevealedIndices] = useState<Set<number>>(
    new Set(),
  );
  const [hasAnimated, setHasAnimated] = useState<boolean>(false);
  const [isDecrypted, setIsDecrypted] = useState<boolean>(
    animateOn !== "click" &&
      animateOn !== "view" &&
      (animateOn !== "external" || !trigger),
  );
  const [direction, setDirection] = useState<Direction>("forward");

  const containerRef = useRef<HTMLSpanElement>(null);
  const orderRef = useRef<number[]>([]);
  const pointerRef = useRef<number>(0);
  const iterationRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const availableChars = useMemo<string[]>(() => {
    return useOriginalCharsOnly
      ? Array.from(new Set(text.split(""))).filter((char) => char !== " ")
      : characters.split("");
  }, [useOriginalCharsOnly, text, characters]);

  const shuffleText = useCallback(
    (originalText: string, currentRevealed: Set<number>) => {
      return originalText
        .split("")
        .map((char, i) => {
          if (char === " ") return " ";
          if (currentRevealed.has(i)) return originalText[i];
          return availableChars[
            Math.floor(Math.random() * availableChars.length)
          ];
        })
        .join("");
    },
    [availableChars],
  );

  const computeOrder = useCallback(
    (len: number): number[] => {
      const order: number[] = [];
      if (len <= 0) return order;
      if (revealDirection === "start") {
        for (let i = 0; i < len; i++) order.push(i);
        return order;
      }
      if (revealDirection === "end") {
        for (let i = len - 1; i >= 0; i--) order.push(i);
        return order;
      }
      // center
      const middle = Math.floor(len / 2);
      let offset = 0;
      while (order.length < len) {
        if (offset % 2 === 0) {
          const idx = middle + offset / 2;
          if (idx >= 0 && idx < len) order.push(idx);
        } else {
          const idx = middle - Math.ceil(offset / 2);
          if (idx >= 0 && idx < len) order.push(idx);
        }
        offset++;
      }
      return order.slice(0, len);
    },
    [revealDirection],
  );

  const fillAllIndices = useCallback((): Set<number> => {
    const s = new Set<number>();
    for (let i = 0; i < text.length; i++) s.add(i);
    return s;
  }, [text]);

  const removeRandomIndices = useCallback(
    (set: Set<number>, count: number): Set<number> => {
      const arr = Array.from(set);
      for (let i = 0; i < count && arr.length > 0; i++) {
        const idx = Math.floor(Math.random() * arr.length);
        arr.splice(idx, 1);
      }
      return new Set(arr);
    },
    [],
  );

  const encryptInstantly = useCallback(() => {
    const emptySet = new Set<number>();
    setRevealedIndices(emptySet);
    setDisplayText(shuffleText(text, emptySet));
    setIsDecrypted(false);
  }, [text, shuffleText]);

  const triggerDecrypt = useCallback(() => {
    if (isAnimating) return;
    setIsAnimating(true);
    setDirection("forward");
    iterationRef.current = 0;
    pointerRef.current = 0;
    if (sequential) {
      orderRef.current = computeOrder(text.length);
    }
    setRevealedIndices(new Set());
    setIsDecrypted(false);
  }, [sequential, computeOrder, text.length, isAnimating]);

  const triggerReverse = useCallback(() => {
    if (isAnimating) return;
    setIsAnimating(true);
    setDirection("reverse");
    iterationRef.current = 0;
    pointerRef.current = 0;
    if (sequential) {
      orderRef.current = computeOrder(text.length).slice().reverse();
    }
    setRevealedIndices(fillAllIndices());
    setIsDecrypted(true);
  }, [sequential, computeOrder, text.length, fillAllIndices, isAnimating]);

  useEffect(() => {
    if (!isAnimating) return;

    intervalRef.current = setInterval(() => {
      if (sequential) {
        if (direction === "forward") {
          setRevealedIndices((prev) => {
            if (prev.size < text.length) {
              const nextIndex = orderRef.current[pointerRef.current++];
              const newSet = new Set(prev);
              newSet.add(nextIndex);
              setDisplayText(shuffleText(text, newSet));
              return newSet;
            } else {
              if (intervalRef.current) clearInterval(intervalRef.current);
              setIsAnimating(false);
              setIsDecrypted(true);
              setDisplayText(text);
              return prev;
            }
          });
        } else {
          // reverse sequential
          setRevealedIndices((prev) => {
            if (prev.size > 0) {
              const idxToRemove = orderRef.current[pointerRef.current++];
              const newSet = new Set(prev);
              newSet.delete(idxToRemove);
              setDisplayText(shuffleText(text, newSet));
              return newSet;
            } else {
              if (intervalRef.current) clearInterval(intervalRef.current);
              setIsAnimating(false);
              setIsDecrypted(false);
              return prev;
            }
          });
        }
      } else {
        // non-sequential
        if (direction === "forward") {
          if (iterationRef.current < maxIterations) {
            setDisplayText(shuffleText(text, new Set()));
            iterationRef.current++;
          } else {
            if (intervalRef.current) clearInterval(intervalRef.current);
            setIsAnimating(false);
            setIsDecrypted(true);
            setDisplayText(text);
          }
        } else {
          // reverse non-sequential
          if (iterationRef.current < maxIterations) {
            const removeCount = Math.max(
              1,
              Math.ceil(text.length / maxIterations),
            );
            setRevealedIndices((prev) => {
              const nextSet = removeRandomIndices(prev, removeCount);
              setDisplayText(shuffleText(text, nextSet));
              return nextSet;
            });
            iterationRef.current++;
          } else {
            if (intervalRef.current) clearInterval(intervalRef.current);
            setIsAnimating(false);
            setIsDecrypted(false);
            setDisplayText(shuffleText(text, new Set()));
          }
        }
      }
    }, speed);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [
    isAnimating,
    direction,
    text,
    sequential,
    maxIterations,
    speed,
    shuffleText,
    removeRandomIndices,
  ]);

  /* Click Behaviour */
  const handleClick = () => {
    if (animateOn !== "click" && animateOn !== "view") return;

    if (clickMode === "once") {
      if (isDecrypted) return;
      setDirection("forward");
      triggerDecrypt();
    }

    if (clickMode === "toggle") {
      if (isDecrypted) {
        triggerReverse();
      } else {
        setDirection("forward");
        triggerDecrypt();
      }
    }
  };

  /* Hover Behaviour */
  const triggerHoverDecrypt = useCallback(() => {
    if (isAnimating) return;

    // Reset animation state cleanly
    setRevealedIndices(new Set());
    setIsDecrypted(false);
    setDisplayText(text);

    setDirection("forward");
    setIsAnimating(true);
  }, [isAnimating, text]);

  const resetToPlainText = useCallback(() => {
    setIsAnimating(false);
    setRevealedIndices(new Set());
    setDisplayText(text);
    setIsDecrypted(true);
    setDirection("forward");
  }, [text]);

  /* View Observer */
  useEffect(() => {
    if (animateOn !== "view" && animateOn !== "inViewHover") return;

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !hasAnimated) {
          triggerDecrypt();
          setHasAnimated(true);
        }
      });
    };

    const observerOptions = {
      root: null,
      rootMargin: "0px",
      threshold: 0.1,
    };

    const observer = new IntersectionObserver(
      observerCallback,
      observerOptions,
    );
    const currentRef = containerRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [animateOn, hasAnimated, triggerDecrypt]);

  useEffect(() => {
    if (animateOn === "external" && trigger) {
      triggerDecrypt();
    }
  }, [animateOn, trigger, triggerDecrypt]);

  useEffect(() => {
    if (
      animateOn === "click" ||
      animateOn === "view" ||
      animateOn === "external"
    ) {
      if (animateOn === "external" && !trigger) {
        setDisplayText(text);
        setIsDecrypted(true);
      } else {
        encryptInstantly();
      }
    } else {
      setDisplayText(text);
      setIsDecrypted(true);
    }
    setRevealedIndices(new Set());
    setDirection("forward");
  }, [animateOn, text, encryptInstantly, trigger]);

  const animateProps = {
    ...((animateOn === "hover" || animateOn === "inViewHover") && {
      onMouseEnter: triggerHoverDecrypt,
      onMouseLeave: resetToPlainText,
    }),
    ...((animateOn === "click" || animateOn === "view") && {
      onClick: handleClick,
    }),
  };

  return (
    <motion.span
      ref={containerRef}
      className={parentClassName}
      style={{ ...styles.wrapper, ...(props.style as object) }}
      {...animateProps}
      {...props}
    >
      <span style={styles.srOnly}>{text}</span>

      <span aria-hidden="true">
        {displayText.split("").map((char, index) => {
          const isRevealedOrDone =
            revealedIndices.has(index) || (!isAnimating && isDecrypted);

          return (
            <span
              key={index}
              className={isRevealedOrDone ? className : encryptedClassName}
            >
              {char}
            </span>
          );
        })}
      </span>
    </motion.span>
  );
}
