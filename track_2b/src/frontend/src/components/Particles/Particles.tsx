"use client";

import React, {
  type ComponentPropsWithoutRef,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { cn } from "@/lib/utils";

interface MousePosition {
  x: number;
  y: number;
}

function useMousePosition(): MousePosition {
  const [mousePosition, setMousePosition] = useState<MousePosition>({
    x: 0,
    y: 0,
  });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setMousePosition({ x: event.clientX, y: event.clientY });
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return mousePosition;
}

export interface ParticlesProps extends ComponentPropsWithoutRef<"div"> {
  className?: string;
  quantity?: number;
  staticity?: number;
  ease?: number;
  size?: number;
  refresh?: boolean;
  color?: string;
  /** Per-particle opacity range (0–1). */
  alphaMin?: number;
  alphaMax?: number;
  vx?: number;
  vy?: number;
  /** `dust` = drifting dots; `rain` = subtle falling streaks */
  variant?: "dust" | "rain";
}

function hexToRgb(hex: string): number[] {
  let h = hex.replace("#", "");

  if (h.length === 3) {
    h = h
      .split("")
      .map((char) => char + char)
      .join("");
  }

  const hexInt = Number.parseInt(h, 16);
  const red = (hexInt >> 16) & 255;
  const green = (hexInt >> 8) & 255;
  const blue = hexInt & 255;
  return [red, green, blue];
}

type Particle = {
  x: number;
  y: number;
  translateX: number;
  translateY: number;
  /** dust: radius · rain: streak length (px) */
  size: number;
  alpha: number;
  targetAlpha: number;
  dx: number;
  dy: number;
  /** dust: magnetism · rain: stroke line width */
  magnetism: number;
};

function remapValue(
  value: number,
  start1: number,
  end1: number,
  start2: number,
  end2: number,
): number {
  const remapped =
    ((value - start1) * (end2 - start2)) / (end1 - start1) + start2;
  return remapped > 0 ? remapped : 0;
}

function drawRainStreak(
  ctx: CanvasRenderingContext2D,
  p: Particle,
  rgb: number[],
  dpr: number,
) {
  const {
    x,
    y,
    translateX,
    translateY,
    size: length,
    alpha,
    dx,
    magnetism,
  } = p;
  const tilt = dx * 3;
  ctx.translate(translateX, translateY);
  ctx.beginPath();
  ctx.moveTo(x + tilt * 0.35, y);
  ctx.lineTo(x - tilt * 0.35, y + length);
  ctx.strokeStyle = `rgba(${rgb.join(", ")}, ${alpha})`;
  ctx.lineWidth = magnetism;
  ctx.lineCap = "round";
  ctx.stroke();
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

export const Particles: React.FC<ParticlesProps> = ({
  className = "",
  quantity = 100,
  staticity = 50,
  ease = 50,
  size = 0.4,
  refresh = false,
  color = "#ffffff",
  alphaMin = 0.2,
  alphaMax = 0.75,
  vx = 0,
  vy = 0,
  variant = "dust",
  ...props
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const context = useRef<CanvasRenderingContext2D | null>(null);
  const particles = useRef<Particle[]>([]);
  const mousePosition = useMousePosition();
  const mouse = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const canvasSize = useRef<{ w: number; h: number }>({ w: 0, h: 0 });
  const dpr =
    typeof window !== "undefined" ? Math.min(window.devicePixelRatio, 2) : 1;
  const rafID = useRef<number | null>(null);
  const resizeTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const rgbRef = useRef(hexToRgb(color));

  useEffect(() => {
    rgbRef.current = hexToRgb(color);
  }, [color]);

  const dustParams = useCallback((): Particle => {
    const { w, h } = canvasSize.current;
    const x = Math.floor(Math.random() * w);
    const y = Math.floor(Math.random() * h);
    const pSize = Math.floor(Math.random() * 2) + size;
    const span = Math.max(0.02, alphaMax - alphaMin);
    const targetAlpha = Number.parseFloat(
      (Math.random() * span + alphaMin).toFixed(2),
    );
    return {
      x,
      y,
      translateX: 0,
      translateY: 0,
      size: pSize,
      alpha: 0,
      targetAlpha,
      dx: (Math.random() - 0.5) * 0.1,
      dy: (Math.random() - 0.5) * 0.1,
      magnetism: 0.1 + Math.random() * 4,
    };
  }, [size, alphaMin, alphaMax]);

  const rainParams = useCallback((): Particle => {
    const { w, h } = canvasSize.current;
    const span = Math.max(0.02, alphaMax - alphaMin);
    const targetAlpha = Number.parseFloat(
      (Math.random() * span + alphaMin).toFixed(2),
    );
    const length = 7 + Math.random() * 11;
    return {
      x: Math.random() * w,
      y: Math.random() * (h + 140) - 140,
      translateX: 0,
      translateY: 0,
      size: length,
      alpha: targetAlpha,
      targetAlpha,
      dx: (Math.random() - 0.5) * 0.55,
      dy: 2.1 + Math.random() * 2.4,
      magnetism: 0.45 + Math.random() * 0.45,
    };
  }, [alphaMin, alphaMax]);

  const spawnParticle = useCallback(
    (): Particle => (variant === "rain" ? rainParams() : dustParams()),
    [variant, rainParams, dustParams],
  );

  const drawCircle = useCallback(
    (p: Particle, update = false) => {
      if (!context.current) return;
      const { x, y, translateX, translateY, size: s, alpha } = p;
      const rgb = rgbRef.current;
      context.current.translate(translateX, translateY);
      context.current.beginPath();
      context.current.arc(x, y, s, 0, 2 * Math.PI);
      context.current.fillStyle = `rgba(${rgb.join(", ")}, ${alpha})`;
      context.current.fill();
      context.current.setTransform(dpr, 0, 0, dpr, 0, 0);

      if (!update) {
        particles.current.push(p);
      }
    },
    [dpr],
  );

  const clearContext = useCallback(() => {
    if (!context.current) return;
    context.current.clearRect(0, 0, canvasSize.current.w, canvasSize.current.h);
  }, []);

  const drawParticles = useCallback(() => {
    clearContext();
    particles.current = [];
    const rgb = rgbRef.current;
    for (let i = 0; i < quantity; i++) {
      const p = spawnParticle();
      if (variant === "rain") {
        particles.current.push(p);
        if (context.current) {
          drawRainStreak(context.current, p, rgb, dpr);
        }
      } else {
        drawCircle(p);
      }
    }
  }, [quantity, spawnParticle, drawCircle, clearContext, variant, dpr]);

  const resizeCanvas = useCallback(() => {
    if (!canvasContainerRef.current || !canvasRef.current || !context.current) {
      return;
    }
    canvasSize.current.w = canvasContainerRef.current.offsetWidth;
    canvasSize.current.h = canvasContainerRef.current.offsetHeight;

    canvasRef.current.width = canvasSize.current.w * dpr;
    canvasRef.current.height = canvasSize.current.h * dpr;
    canvasRef.current.style.width = `${canvasSize.current.w}px`;
    canvasRef.current.style.height = `${canvasSize.current.h}px`;
    context.current.setTransform(dpr, 0, 0, dpr, 0, 0);

    drawParticles();
  }, [dpr, drawParticles]);

  const onMouseMove = useCallback(() => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const { w, h } = canvasSize.current;
    const x = mousePosition.x - rect.left - w / 2;
    const y = mousePosition.y - rect.top - h / 2;
    const inside = x < w / 2 && x > -w / 2 && y < h / 2 && y > -h / 2;
    if (inside) {
      mouse.current.x = x;
      mouse.current.y = y;
    }
  }, [mousePosition.x, mousePosition.y]);

  const animate = useCallback(() => {
    if (!context.current) {
      rafID.current = window.requestAnimationFrame(animate);
      return;
    }
    clearContext();
    const { w, h } = canvasSize.current;
    const rgb = rgbRef.current;

    if (variant === "rain") {
      for (let i = particles.current.length - 1; i >= 0; i--) {
        const p = particles.current[i];
        if (!p) continue;

        p.x += p.dx + vx;
        p.y += p.dy + vy;

        if (p.y > h + p.size + 24) {
          p.x = Math.random() * w;
          p.y = -p.size - Math.random() * 120;
          p.dx = (Math.random() - 0.5) * 0.55;
          p.dy = 2.1 + Math.random() * 2.4;
          p.size = 7 + Math.random() * 11;
          p.magnetism = 0.45 + Math.random() * 0.45;
          const span = Math.max(0.02, alphaMax - alphaMin);
          p.targetAlpha = Number.parseFloat(
            (Math.random() * span + alphaMin).toFixed(2),
          );
          p.alpha = p.targetAlpha;
        }

        drawRainStreak(context.current, p, rgb, dpr);
      }
      rafID.current = window.requestAnimationFrame(animate);
      return;
    }

    for (let i = particles.current.length - 1; i >= 0; i--) {
      const circle = particles.current[i];
      if (!circle) continue;

      const edge = [
        circle.x + circle.translateX - circle.size,
        w - circle.x - circle.translateX - circle.size,
        circle.y + circle.translateY - circle.size,
        h - circle.y - circle.translateY - circle.size,
      ];
      const closestEdge = edge.reduce((a, b) => Math.min(a, b));
      const remapClosestEdge = Number.parseFloat(
        remapValue(closestEdge, 0, 20, 0, 1).toFixed(2),
      );

      if (remapClosestEdge > 1) {
        circle.alpha += 0.02;
        if (circle.alpha > circle.targetAlpha) {
          circle.alpha = circle.targetAlpha;
        }
      } else {
        circle.alpha = circle.targetAlpha * remapClosestEdge;
      }

      circle.x += circle.dx + vx;
      circle.y += circle.dy + vy;
      circle.translateX +=
        (mouse.current.x / (staticity / circle.magnetism) - circle.translateX) /
        ease;
      circle.translateY +=
        (mouse.current.y / (staticity / circle.magnetism) - circle.translateY) /
        ease;

      const out =
        circle.x < -circle.size ||
        circle.x > w + circle.size ||
        circle.y < -circle.size ||
        circle.y > h + circle.size;

      if (out) {
        particles.current.splice(i, 1);
        particles.current.push(spawnParticle());
      } else {
        const { x, y, translateX, translateY, size: s, alpha } = circle;
        context.current.translate(translateX, translateY);
        context.current.beginPath();
        context.current.arc(x, y, s, 0, 2 * Math.PI);
        context.current.fillStyle = `rgba(${rgb.join(", ")}, ${alpha})`;
        context.current.fill();
        context.current.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    }

    rafID.current = window.requestAnimationFrame(animate);
  }, [
    clearContext,
    spawnParticle,
    dpr,
    ease,
    staticity,
    vx,
    vy,
    variant,
    alphaMin,
    alphaMax,
  ]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: `refresh` toggles re-seed particles from parent
  useLayoutEffect(() => {
    if (canvasRef.current) {
      context.current = canvasRef.current.getContext("2d");
    }
    resizeCanvas();
    rafID.current = window.requestAnimationFrame(animate);

    const handleResize = () => {
      if (resizeTimeout.current) {
        clearTimeout(resizeTimeout.current);
      }
      resizeTimeout.current = setTimeout(() => {
        resizeCanvas();
      }, 200);
    };

    window.addEventListener("resize", handleResize);

    const el = canvasContainerRef.current;
    let ro: ResizeObserver | undefined;
    if (el && typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(() => {
        resizeCanvas();
      });
      ro.observe(el);
    }

    const rafResize = requestAnimationFrame(() => {
      resizeCanvas();
    });

    return () => {
      if (rafID.current != null) {
        window.cancelAnimationFrame(rafID.current);
      }
      if (resizeTimeout.current) {
        clearTimeout(resizeTimeout.current);
      }
      window.removeEventListener("resize", handleResize);
      ro?.disconnect();
      cancelAnimationFrame(rafResize);
    };
  }, [resizeCanvas, animate, refresh]);

  useEffect(() => {
    onMouseMove();
  }, [onMouseMove]);

  return (
    <div
      ref={canvasContainerRef}
      className={cn("pointer-events-none", className)}
      aria-hidden="true"
      {...props}
    >
      <canvas ref={canvasRef} className="size-full" />
    </div>
  );
};

Particles.displayName = "Particles";
