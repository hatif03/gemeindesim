"use client";

import {
  SiBun,
  SiD3,
  SiFastapi,
  SiFramer,
  SiLangchain,
  SiLanggraph,
  SiNextdotjs,
  SiPython,
  SiReact,
  SiSocketdotio,
  SiTailwindcss,
  SiThreedotjs,
  SiTypescript,
  SiXyflow,
} from "react-icons/si";
import type { LogoItem } from "@/components/LogoLoop/LogoLoop";

/**
 * Icons match declared dependencies in frontend/package.json and backend/pyproject.toml.
 * Phaser has no Simple Icons glyph — text label only.
 */
export const stackLogos: LogoItem[] = [
  {
    node: <SiNextdotjs title="Next.js" />,
    title: "Next.js",
    href: "https://nextjs.org",
  },
  {
    node: <SiReact title="React" />,
    title: "React",
    href: "https://react.dev",
  },
  {
    node: <SiTypescript title="TypeScript" />,
    title: "TypeScript",
    href: "https://www.typescriptlang.org",
  },
  {
    node: <SiTailwindcss title="Tailwind CSS" />,
    title: "Tailwind CSS",
    href: "https://tailwindcss.com",
  },
  {
    node: (
      <span className="font-pixel uppercase tracking-widest opacity-95">
        Phaser
      </span>
    ),
    title: "Phaser",
    href: "https://phaser.io",
    ariaLabel: "Phaser 3",
  },
  {
    node: <SiFramer title="Motion" />,
    title: "Motion",
    href: "https://motion.dev",
  },
  {
    node: <SiD3 title="D3.js" />,
    title: "D3.js",
    href: "https://d3js.org",
  },
  {
    node: <SiXyflow title="XYFlow" />,
    title: "XYFlow",
    href: "https://xyflow.com",
  },
  {
    node: <SiThreedotjs title="Three.js" />,
    title: "Three.js",
    href: "https://threejs.org",
  },
  {
    node: <SiSocketdotio title="Socket.IO" />,
    title: "Socket.IO",
    href: "https://socket.io",
  },
  {
    node: <SiBun title="Bun" />,
    title: "Bun",
    href: "https://bun.sh",
  },
  {
    node: <SiPython title="Python" />,
    title: "Python",
    href: "https://www.python.org",
  },
  {
    node: <SiFastapi title="FastAPI" />,
    title: "FastAPI",
    href: "https://fastapi.tiangolo.com",
  },
  {
    node: <SiLanggraph title="LangGraph" />,
    title: "LangGraph",
    href: "https://langchain-ai.github.io/langgraph/",
  },
  {
    node: <SiLangchain title="LangChain" />,
    title: "LangChain",
    href: "https://langchain.com",
  },
];
