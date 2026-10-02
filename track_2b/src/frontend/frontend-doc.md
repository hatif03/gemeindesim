# GemeindeSim frontend reference

Authoritative reference for the GemeindeSim frontend: map generation, NPC behavior, visual effects, UI layout, and event contracts. Read this before modifying any frontend code.

---

## 1. Map & Tileset Rules

### Tileset

- **Image:** `/assets/citymap_tilesets/CCity_mockup.png`
- **Dimensions:** 640 x 256 px
- **Grid:** 40 columns x 16 rows = 640 tiles
- **Tile size:** 16 x 16 px
- **Margin:** 0, **Spacing:** 0

### GID Conversion Rule

Tiled JSON uses `firstgid = 1`. Every tile index in the code is 0-indexed; the generator adds 1 when writing to the JSON map file:

```
GID = tile_index + 1
GID 0 = empty / transparent
```

Example: Grass tile index `0` becomes GID `1`. Road top tile index `350` becomes GID `351`.

### Tile ID Groups (0-indexed)

**Ground:**

| Element | Tile ID(s) | Notes |
|---|---|---|
| Grass | 0 | Single tile, park fill |
| Water (full) | 566 | Deep water fill |
| River edge (horizontal) | 490 | Land-to-water transition |
| Concrete floor | 290, 291 | 1x2 pair, parking lots and plazas |
| Parking (car) | 250, 251 | 1x2 pair on buildings layer |
| Rock | 404, 405, 444, 445 | 2x2 group |

**Roads:**

| Element | Tile ID(s) | Notes |
|---|---|---|
| Road X-axis (top lane) | 350 | Horizontal road, top half |
| Road X-axis (bottom lane) | 390 | Horizontal road, bottom half |
| Road Y-axis | 194, 195 | Vertical road, 2 tiles side by side |
| Road interior | 354 | Plain fill for intersections |
| Crossing X-axis | 282, 283 | Pedestrian crossing, horizontal |
| Crossing Y-axis (right) | 321, 361 | Pedestrian crossing, vertical right |
| Crossing Y-axis (left) | 324, 364 | Pedestrian crossing, vertical left |

**Buildings (multi-tile groups):**

| Building | Size (W x H) | Top-left tile IDs (row-major) |
|---|---|---|
| Factory | 4 x 3 | 226, 227, 228, 229 / 266-269 / 306-309 |
| Shop #1 | 2 x 4 | 176, 177 / 216-217 / 256-257 / 296-297 |
| Shop #2 | 2 x 2 | 248, 249 / 288, 289 |
| Long Shop | 4 x 2 | 252-255 / 292-295 |
| House | 2 x 2 | 270, 271 / 310, 311 |
| Hospital | 4 x 4 | 178-181 / 218-221 / 258-261 / 298-301 |
| Concrete Building | 4 x 4 | 164-167 / 204-207 / 244-247 / 284-287 |

**Nature:**

| Element | Tile ID(s) | Notes |
|---|---|---|
| Tree | 356, 357, 396, 397 | 2x2 group |
| Rock | 404, 405, 444, 445 | 2x2 group |

### Map Dimensions

- **Grid:** 80 columns x 60 rows
- **Tile size:** 16 x 16 px
- **Total pixel size:** 1280 x 960 px (before scaling)

### Road Grid Positions

**Horizontal road pairs** (row indices, each pair = top lane + bottom lane):

| Pair | Rows |
|---|---|
| 1 | 5, 6 |
| 2 | 13, 14 |
| 3 | 21, 22 |
| 4 | 37, 38 |
| 5 | 45, 46 |
| 6 | 53, 54 |

**Vertical road pairs** (column indices, each pair = left lane + right lane):

| Pair | Columns |
|---|---|
| 1 | 9, 10 |
| 2 | 24, 25 |
| 3 | 39, 40 |
| 4 | 54, 55 |
| 5 | 69, 70 |

### River Positions

**River 1:**
- Edge top: row 29
- Water: rows 30-32
- Edge bottom: row 33

**River 2:**
- Edge top: row 50
- Water: row 51
- Edge bottom: row 52

Riverbanks (rows adjacent to edges: 28, 34, 49, 53) get decorative trees scattered along them.

### Zone Types and Row Ranges

Zones are assigned to city blocks (rectangular regions between roads). Assignment logic uses the block's center row (`midR`) and center column (`midC`), with `centerCol = 40`:

| Zone | Row Range (midR) | Column Constraint | Notes |
|---|---|---|---|
| PARK | r2 <= 4 or r1 >= 55 | Any | Top and bottom edges of the map |
| GOVERNMENT | midR 7-12 | abs(midC - 40) < 20 | Largest block in upper-center area |
| WATERFRONT | Adjacent to river rows | Any | Blocks overlapping river edge rows |
| INDUSTRIAL | midR 39-49 | Any | Lower-middle area |
| COMMERCIAL | midR 15-28 | abs(midC - 40) < 30 | Middle rows near center |
| RESIDENTIAL | midR 7-14 or 39-54 | Any | Default fallback for remaining blocks |

---

## 2. Procedural Generation Rules

### Block Computation

City blocks are the rectangular regions formed by the intersections of horizontal and vertical roads. The generator:

1. Collects all unique road rows and columns into sorted sets.
2. Computes row ranges (gaps between consecutive horizontal road rows).
3. Computes column ranges (gaps between consecutive vertical road columns).
4. Takes the cross product of all row ranges x column ranges to produce blocks.
5. Blocks entirely inside a river are discarded.

### Zone Assignment Logic

Each block is assigned exactly one zone based on its center position:

1. **PARK** if the block is entirely in the top 5 rows or bottom 5 rows.
2. **GOVERNMENT** if the block is the largest block in the upper-center area (midR 7-12, within 20 cols of center).
3. **WATERFRONT** if the block overlaps any river edge row (+/- 1 row).
4. **INDUSTRIAL** if midR is 39-49.
5. **COMMERCIAL** if midR is 15-28 and within 30 cols of center.
6. **RESIDENTIAL** for all remaining blocks.

### Building Palette per Zone

| Zone | Building Types (weighted) |
|---|---|
| GOVERNMENT | Hospital, Concrete Building, Shop #1, Shop #2 |
| COMMERCIAL | Concrete Building, Long Shop, Shop #1, Shop #2, House |
| RESIDENTIAL | House, Shop #2, House, House (3:1 house weighting) |
| INDUSTRIAL | Factory, Factory, Long Shop, House (2:1 factory weighting) |
| WATERFRONT | Shop #2, House, Long Shop |

### Packing Algorithm

Buildings are placed left-to-right, top-to-bottom within each block:

1. A 1-tile sidewalk border is reserved around the block perimeter (except waterfront blocks which use 0 border on columns).
2. The palette is shuffled with a per-block seeded PRNG (seed = `r1 * 1000 + c1 * 37 + 42`).
3. For each position, try each building in the shuffled palette. Place the first one that fits.
4. Track the tallest building placed in each row; advance by that height to avoid overlap.
5. Small gaps (1x2) in commercial/industrial zones are filled with parking lots.

### Waterfront Rules

- Ground is filled with concrete floor pairs (no grass).
- No trees are placed.
- Parking lots and small shops (Shop #2, House) are placed with random density (~35% parking, ~20% Shop #2, ~15% House, ~30% empty concrete plaza).

### Park Rules

- Trees and rocks only, scattered with minimum 1-tile spacing on a 2x2 grid.
- Probability: ~45% tree, ~15% rock, ~40% open grass.
- A few concrete plaza pairs are scattered randomly.

### River Placement and Bridge Logic

Rivers are horizontal bands spanning the full map width. Vertical roads cross rivers as bridges: where a vertical road column intersects a river row, the road tile is placed instead of water/edge, creating a bridge.

### No Crossing Tiles Rule

Pedestrian crossing tiles were originally planned for road intersections but were removed ("crossing removed -- clean roads look better"). Crossings are defined in code but not placed in the final map.

---

## 3. NPC / Agent Rules

### NPC Sprite Source

NPC sprites come from the Kenney RPG Urban Pack spritesheet (`tilemap_packed.png`, 27 cols x 18 rows, 16x16 tiles). NPC character tiles occupy columns 23-26, rows 14-17 (16 unique static characters). Each NPC is assigned a character index `i % 16`.

### NPC Initialization

NPCs are created dynamically from backend data via the `sim:init-npcs` event. The backend provides NPCs on a 20x15 coordinate grid; the frontend scales these by `COORD_SCALE = 2` to map onto the 80x60 tile grid.

### Spawn Constraints

NPCs must spawn on walkable tiles only. A tile is walkable if the buildings layer has no tile at that position (`buildingLayer.getTileAt(col, row)` returns null). If the scaled spawn position lands on a building, a spiral search (radius up to 5 tiles) finds the nearest walkable tile.

### Movement System

**Road-preference scoring:** Each candidate direction is scored:
- Road/sidewalk/concrete tile: +10 base score
- Grass or other: 0.1 base score (heavily penalized, last resort)

**Momentum:** Continuing in the same direction gets a 2x score multiplier. Instant 180-degree reversal gets a 0.15x penalty.

**Zone leashing:** Each NPC is assigned a home zone based on role:
- `politician`, `activist` -> government (rows 3-10)
- `shopkeeper`, `business_owner` -> commercial (rows 11-16)
- `worker`, `farmer` -> industrial (rows 19-24)
- All others -> residential (rows 0-29)

If an NPC drifts outside their zone, moves back toward the zone center get a 4x score boost. Moves away get 0.1x penalty. Near zone boundaries, a milder 1.5x/0.5x bias applies.

**Walk/pause cycle:** 30% chance to idle (face random direction, pause 1.5-2.5s), 70% chance to walk. After each step, pause 0.4-0.8s. Initial roaming delay is staggered (1.5-3.0s) so NPCs don't all start moving at once.

**Direction selection:** Weighted random selection across all scored candidate directions.

### Walk Animation

Kenney RPG Urban characters are single static tiles with no walk frames. Walking is simulated with a squash-stretch bob tween:
- ScaleY: 1.0 -> 0.9 (squash)
- ScaleX: 1.0 -> 1.1 (stretch)
- Angle: -3 to +3 degrees (sway)
- Duration: 80ms, yoyo, infinite repeat
- Stopped and reset to neutral on walk completion

Horizontal flipping: sprite is flipped X when facing left, normal when facing right. No up/down sprite variants.

### Movement Tween

Each walk step is a 300ms linear tween to the target tile center. Moves greater than 2 tiles are rejected to prevent teleporting.

### NPC Depth

NPCs render at depth 10, above: ground (0), buildings (1), closure overlays (3-4), phase overlay (5).

### Conversation Meetup

When two NPCs emit `reaction`-type events within 5 seconds of each other, `converseWith` is triggered:
1. Both NPCs stop roaming (movement override).
2. NPC A step-walks toward NPC B (up to 5 steps, greedy best-first toward target).
3. They face each other.
4. Both are released back to roaming after 6 seconds.

### Hover Tooltip

Each NPC sprite has pointer interaction enabled. On `pointerover`, a `sim:npc-hover` event is emitted to React with: id, name, role, x, y, sentiment, state. On `pointerout`, `sim:npc-hover-out` is emitted. During movement, position is re-emitted on each tween update if hovered.

---

## 4. Chat Bubble Rules

### DOM Overlays

Chat bubbles are React DOM elements (`<ChatBubble>`) rendered as absolutely-positioned overlays on top of the Phaser canvas. This makes them Playwright-testable (they have `data-testid="chat-bubble"`).

### Position Source

Bubbles only appear from real `sim:npc-position` events emitted by Phaser. There are no fallback or hardcoded positions. If no position event has been received for an NPC, no bubble appears.

### Real-Time Following

While an NPC has an active message, NPCManager emits position updates every 100ms via a Phaser timer. The bubble transitions smoothly to follow the NPC using CSS `transition: left, top` with `duration-100` and `ease-linear`.

### Speech Tail

Each bubble has a decorative speech tail pointing down to the NPC, constructed from CSS border triangles + a vertical stem line + a small dot at the bottom.

### Bubble Limits

Bubbles are keyed by NPC ID in a Map. When an NPC's message is cleared (no `message` field in the position event), the bubble is removed. Messages auto-clear after 5 seconds (set in NPCManager.showMessage). There is no explicit "max 4 bubbles" cap in code, but the 5-second timeout naturally limits concurrent bubbles.

### Text Truncation

Messages longer than 80 characters are truncated with `...`.

### Agent ID Mapping

Backend NPC IDs (`event.agentId`) are used directly as keys into the NPCManager. No ID translation is needed -- backend IDs match frontend NPC IDs.

---

## 5. Camera / Canvas Rules

### Scale Factor

`SCALE_FACTOR = 2`. The game runs at 1280x960 native pixels but the canvas container is sized at `GAME_WIDTH * SCALE_FACTOR + 4` x `GAME_HEIGHT * SCALE_FACTOR + 4` (2564 x 1924 px including border). Phaser uses `Phaser.Scale.FIT` with `CENTER_BOTH` to fill the container.

### Pan (Click + Drag)

Camera panning is handled in React via pointer events on the canvas container div:
1. `pointerdown` (button 0) starts drag, captures pointer.
2. `pointermove` computes delta, emits `sim:camera-pan` with `{ dx: -dx/SCALE_FACTOR, dy: -dy/SCALE_FACTOR }`.
3. Phaser's `onCameraPan` handler adds the delta to `cameras.main.scrollX/scrollY`.
4. `pointerup` ends drag, releases pointer capture.
5. Cursor changes between `grab` (idle) and `grabbing` (dragging).

### Zoom

Zoom is referenced in the design but not yet implemented in the current codebase. The planned behavior: scroll wheel emits `sim:camera-zoom`, clamped 0.5-3.0.

### Fullscreen

Uses the browser Fullscreen API on the canvas container div. A toggle button (`[X]` / `[ ]`) sits in the top-right corner of the canvas area. State is tracked via the `fullscreenchange` DOM event.

### Canvas Overflow

The canvas container has `overflow: hidden` (via the Tailwind class on the parent div). No scrollbars appear.

---

## 6. EventBridge Contract

EventBridge is a singleton custom event emitter (`EventBridge.getInstance()`) that bridges React and Phaser without requiring Phaser to be loaded during SSR.

### Events: React -> Phaser

| Event | Payload | Purpose |
|---|---|---|
| `sim:event` | `SimEvent` | Trigger game visual effects (protest, closure, price spike, chat bubbles) |
| `sim:phase-change` | `{ phase: number, month: number }` | Update world color overlay for current phase |
| `sim:camera-pan` | `{ dx: number, dy: number }` | Scroll camera by delta (in game pixels) |
| `sim:init-npcs` | `BackendNPC[]` | Create/replace all NPCs from backend data |
| `sim:npc-move` | `{ npcId: string, toX: number, toY: number }` | Step an NPC toward a target position |
| `sim:npc-mood` | `{ npcId: string, mood: string }` | Update an NPC's mood/sentiment |

### Events: Phaser -> React

| Event | Payload | Purpose |
|---|---|---|
| `sim:npc-position` | `NPCState` | Send NPC position + message for DOM chat bubble rendering |
| `sim:npc-hover` | `NPCHoverInfo` | NPC hovered -- show tooltip |
| `sim:npc-hover-out` | (none) | NPC unhovered -- hide tooltip |

### Key Type Shapes

```typescript
interface SimEvent {
  id: string;
  type: SimEventType; // "reaction" | "price_change" | "layoff" | "protest" | "closure" | "strike" | "policy_response" | "phase_change" | "mood_shift"
  agentId: string;
  agentName: string;
  message: string;
  phase: number;   // 1-3
  month: number;   // 1-9
  timestamp: number;
}

interface NPCState {
  id: string;
  name: string;
  x: number;       // pixel position
  y: number;
  direction: "up" | "down" | "left" | "right";
  state: "idle" | "walking" | "protesting";
  message?: string; // present = show bubble, absent = hide bubble
}

interface NPCHoverInfo {
  id: string;
  name: string;
  role: string;
  x: number;       // pixel position
  y: number;
  sentiment: "happy" | "neutral" | "worried" | "angry";
  state: "idle" | "walking" | "protesting";
}
```

---

## 7. Simulation Flow

### Data Pipeline

```
Backend WS -> useSimulation hook -> EventBridge -> Phaser (visual effects) + React (UI)
```

1. User enters policy text on the landing page; it is stored in `sessionStorage` under key `gemeindesim-policy`.
2. On the `/simulate` page, `useSimulation` reads the stored text and calls `startSimulation(text)` which POSTs to `http://localhost:8000/simulate`.
3. The backend returns a `simulation_id`. `connectWebSocket` opens `ws://localhost:8000/simulate/{id}/ws`.
4. WebSocket messages arrive as typed JSON: `policy_analysis`, `init`, `round`, `done`, `error`.

### Event Processing per Round

On each `round` message:
1. NPC lookup map is updated with latest NPC states.
2. Phase boundaries are detected (`roundToPhase` divides total rounds into 3 equal thirds). A `phase_change` event is injected at each boundary.
3. `move` and `mood_shift` events are forwarded directly to Phaser via EventBridge (not queued for the event feed).
4. All other events are adapted from backend format to frontend `SimEvent` format and queued.
5. Metrics are incrementally updated from the round's events and current NPC states.

### Event Queue Drain

Events are played back cinematically from the queue with variable delays:
- Phase change events: 2000ms delay
- All other events: 1200-1800ms delay (randomized)

Each dequeued event is emitted via `eventBridge.emitSimEvent()` (triggering Phaser effects) and appended to React state (triggering EventFeed update). The event feed is capped at 200 entries (oldest are dropped).

### Phase Progression

Phases map to simulated months:

| Phase | Label | Months | Visual Overlay |
|---|---|---|---|
| 1 | Announcement & Assessment | 1-3 | None (transparent) |
| 2 | Economic Ripple Effects | 4-6 | Warm orange, 8% alpha |
| 3 | Social Crisis & Reckoning | 7-9 | Red, 15% alpha |

The phase overlay is a full-screen `Phaser.GameObjects.Rectangle` at depth 5 (above buildings, below NPCs).

### Metric Updates per Event

Metrics are computed client-side from backend data using running accumulators:

| Metric | Source |
|---|---|
| Price Index | Accumulated % change from `price_change` events (`old_price` -> `new_price`) |
| Unemployment Rate | Base 4.2% + 0.4% per layoff event detected |
| Social Unrest | Fraction of NPCs with `angry` or `anxious` mood |
| Business Survival | Base 0.95 - 0.03 per closure event detected |
| Gov Approval | Average mood score across all NPCs |
| Interest Rate | Fixed at 5.25% |

Layoffs are detected by regex on chat messages: `/layoff|fired|let\s+go|cut.*jobs|furlough/i`.
Closures are detected by regex: `/clos(e|ing|ed)|shut.*down|going out of business|bankrupt/i`.

### Building Event Types and Visual Effects

| Event Type | Trigger | Visual Effect |
|---|---|---|
| `protest` | Backend protest event | Up to 5 angry/worried NPCs cluster in front of government building. Floating "PROTEST!" text bobs and fades over 4s. NPCs release after 8s. |
| `strike` | Protest event from a worker NPC at a factory location | Up to 3 worker NPCs sent to first factory position. Release after 8s. |
| `closure` | Chat message matching closure regex from business_owner/shopkeeper | Dark overlay (50% black) fades onto a random shop building. "CLOSED" text appears. Permanent. |
| `price_change` | Backend price_change event | Floating price label (e.g. "+15%") rises from a random shop and fades over 2.5s. |
| `reaction` | Chat from non-politicians, mood_shift, default | Chat bubble shown above NPC. If two NPCs react within 5s, they walk toward each other for a conversation meetup. |
| `policy_response` | Chat from a politician NPC | Chat bubble shown (same as reaction, distinguished in EventFeed by icon/color). |

---

## 8. UI Layout Rules

### Overall Structure

```
+-------------------------------------------------------+
| Phase Bar (h-10, full width)                          |
+----------+---------------------------+--------+
| EventFeed | GameCanvas (center, flex) | Dashboard |
| w-64      | (fills remaining)        | w-56      |
+----------+---------------------------+--------+
```

- Root container: `h-screen`, `overflow-hidden`, `bg-[#1a1510]`
- Phase bar: fixed height `h-10`, `rpg-panel` styled, no rounded top/side borders
- Main content: `flex flex-1 gap-2 p-2 overflow-hidden`

### Sidebar Widths

- **EventFeed:** `w-64` (256px), left side, `shrink-0`
- **Dashboard:** `w-56` (224px), right side, `shrink-0`
- **GameCanvas:** center, `flex-1 min-w-0`, takes remaining space

### Dark RPG Theme Colors

Defined as CSS custom properties in `globals.css`:

| Variable | Hex | Usage |
|---|---|---|
| `--background` | `#1a1510` | Page background |
| `--foreground` | `#f0e6d2` | Primary text |
| `--accent` | `#e8a43a` | Gold accent (headers, highlights) |
| `--surface` | `#2a2218` | Elevated surface |
| `--border` | `#4a3c2a` | Panel borders |
| `--panel-bg` | `#251e15` | Panel backgrounds |
| `--muted` | `#8a7a62` | Secondary/muted text |

Additional inline colors used in components:
- **Good/happy:** `#5ab85a` (green)
- **Warning/worried:** `#e8a43a` (amber)
- **Bad/angry:** `#d45050` (red)
- **Critical/closure:** `#c43030` (dark red)

### RPG Panel Style

The `.rpg-panel` class provides the signature panel look:
- Background: `--panel-bg`
- Border: 2px solid `--border`
- Border radius: 4px
- Box shadow: inner highlight (top-left white 5%), inner shadow (bottom-right black 30%), outer drop shadow (black 40%)

### Phase Bar

Three phase segments displayed as `h-2 w-12` colored bars:
- Phase 1: `bg-[#5ab85a]` (green)
- Phase 2: `bg-[#e8a43a]` (amber)
- Phase 3: `bg-[#d45050]` (red)
- Inactive: `bg-[#251e15]` (dark)

Phase label text appears to the right of the bars when a phase is active.

### Typography

All text uses monospace font (`font-mono`). Sizes range from `text-[9px]` (smallest labels) to `text-[10px]` (standard) to `text-xs` (metric values). Headers use `font-bold uppercase tracking-widest`.

### Pixel-Crisp Rendering

The `.pixel-crisp` class on the game canvas div sets `image-rendering: pixelated` and `crisp-edges` to prevent blurring of scaled pixel art.
