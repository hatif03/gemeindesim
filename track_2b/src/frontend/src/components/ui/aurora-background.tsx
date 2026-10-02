"use client";
import { cn } from "@/lib/utils";
import React, { type ReactNode } from "react";

interface AuroraBackgroundProps extends React.HTMLProps<HTMLDivElement> {
  children: ReactNode;
  showRadialGradient?: boolean;
}


/** Drop-in absolute background layer — use inside any `relative` container. */
export const AuroraLayer = ({
  showRadialGradient = true,
  className,
}: {
  showRadialGradient?: boolean;
  className?: string;
}) => (
  <div
    className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    aria-hidden
  >
    <div
      className={cn(
        "absolute -inset-[10px] will-change-transform",
        showRadialGradient &&
          "[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,transparent_70%)]",
      )}
      style={{
        background:
          "repeating-linear-gradient(100deg,#3b82f6 10%,#a5b4fc 15%,#93c5fd 20%,#ddd6fe 25%,#60a5fa 30%)",
        backgroundSize: "300% 200%",
        animation: "aurora 60s linear infinite",
        opacity: 0.45,
        filter: "blur(48px)",
        mixBlendMode: "screen",
      }}
    />
  </div>
);

export const AuroraBackground = ({
  className,
  children,
  showRadialGradient = true,
  ...props
}: AuroraBackgroundProps) => {
  return (
    <main>
      <div
        className={cn(
          "transition-bg relative flex h-[100vh] flex-col items-center justify-center bg-zinc-50 text-slate-950 dark:bg-zinc-900",
          className,
        )}
        {...props}
      >
        <AuroraLayer showRadialGradient={showRadialGradient} />
        {children}
      </div>
    </main>
  );
};
