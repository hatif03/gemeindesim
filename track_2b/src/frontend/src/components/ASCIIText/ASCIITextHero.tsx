"use client";

import dynamic from "next/dynamic";
import { stackLogos } from "@/lib/stackLogos";
import LogoLoop from "../LogoLoop/LogoLoop";

const ASCIIText = dynamic(() => import("./ASCIIText"), { ssr: false });

export default function ASCIITextHero() {
  return (
    <div className="flex flex-col items-center">
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "176px",
          zIndex: 100,
          filter:
            "drop-shadow(0 0 30px rgba(255,255,255,0.5)) drop-shadow(0 0 80px rgba(255,255,255,0.2)) drop-shadow(0 0 140px rgba(255,255,255,0.1))",
        }}
      >
        <ASCIIText
          text="GEMEINDE"
          enableWaves
          asciiFontSize={8}
          textFontSize={288}
          textColor="#ffffff"
          planeBaseHeight={10}
        />
      </div>
      <div
        className="w-[360px] mt-2 opacity-40 hover:opacity-100 transition-opacity"
        style={{ filter: "drop-shadow(0 0 20px rgba(255,255,255,0.4))" }}
      >
        <LogoLoop
          logos={stackLogos}
          speed={30}
          direction="left"
          logoHeight={24}
          gap={40}
          hoverSpeed={0}
          fadeOut
          fadeOutColor="#060010"
        />
      </div>
    </div>
  );
}
