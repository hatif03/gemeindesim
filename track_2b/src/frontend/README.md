# GemeindeSim frontend

Pixel-art economic policy simulation — Next.js 16 + Phaser 3 + Tailwind CSS v4.

## Stack

- **Framework:** Next.js 16.2.1 (App Router, React 19, React Compiler)
- **Game Engine:** Phaser 3.90 (client-only via `next/dynamic`)
- **Styling:** Tailwind CSS v4 (CSS-first config)
- **Linting:** Biome 2.2.0
- **Runtime:** Bun

## Getting Started

```bash
bun install
bun dev
```

Open http://localhost:3000

## Structure

```
src/
├── app/
│   ├── page.tsx              # Title screen + node editor
│   ├── simulate/page.tsx     # Simulation view — game + dashboard
│   ├── layout.tsx            # Root layout (Geist Mono, dark theme)
│   └── globals.css           # Theme vars, RPG panel styles
├── components/
│   ├── GameCanvas.tsx        # Phaser wrapper (dynamic, ssr:false)
│   ├── PolicyInput.tsx       # Textarea + 3 preset policies
│   ├── Dashboard.tsx         # Real-time metrics panel
│   ├── EventFeed.tsx         # Scrolling event log
│   └── ChatBubble.tsx        # NPC speech bubbles (DOM overlay)
├── game/
│   ├── config.ts             # Phaser game config (40x30, 16px tiles)
│   ├── bridge/EventBridge.ts # React <-> Phaser event bus (SSR-safe)
│   ├── scenes/
│   │   ├── BootScene.ts      # Asset loading (tileset + tilemap JSON)
│   │   └── WorldScene.ts     # City rendering from Tiled JSON map
│   ├── map/
│   │   ├── TileRegistry.ts   # Tile index constants
│   │   ├── CityGenerator.ts  # Legacy procedural generator (unused)
│   │   └── TILESET_REFERENCE.md # CCity tile ID documentation
│   ├── entities/NPC.ts       # NPC sprite with walk animation
│   ├── systems/
│   │   ├── NPCManager.ts     # Spawns/manages 10 NPCs, zone assignment
│   │   └── MovementSystem.ts # Road-preference roaming with zone leash
│   ├── events/
│   │   └── SimEventHandler.ts # Routes sim events to visual effects
│   └── effects/              # Protest, Closure, PriceSpike effects
├── hooks/
│   └── useSimulation.ts      # Mock event playback (1.2-1.8s intervals)
└── lib/
    ├── types.ts              # Shared types (SimEvent, SimMetrics, etc.)
    └── mockData.ts           # 29 events across 9 months
```

## Tileset

**CCity** (640 tiles, 16x16px) — `public/assets/citymap_tilesets/CCity_mockup.png`

City map is a Tiled JSON file at `public/assets/maps/city.json` (40x30 grid, 2 layers: ground + buildings).

See `src/game/map/TILESET_REFERENCE.md` for tile ID documentation.

## Key Patterns

- **Phaser is client-only** — loaded via `next/dynamic` with `ssr: false`
- **EventBridge** — custom emitter (not Phaser.Events) for SSR safety. React emits `sim:event`, Phaser listens. Phaser emits `sim:npc-position`, React renders chat bubbles.
- **Chat bubbles are DOM overlays** — positioned over the canvas using NPC world coordinates, not Phaser text objects. Testable with Playwright.
- **Mock backend** — `NEXT_PUBLIC_MOCK_BACKEND=true` plays back bundled events. Live path uses Socket.IO against the FastAPI backend.

## Commands

```bash
bun dev          # Start dev server (port 3000)
bun build        # Production build
bun lint         # Biome check
bun format       # Biome format
```
