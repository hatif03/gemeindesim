# Next.js 16 — Breaking Changes

Before using any unfamiliar Next.js API, read the relevant guide in `node_modules/next/dist/docs/`.

## Commands
| Task | Command |
|------|---------|
| Dev | `bun dev` |
| Build | `bun build` |
| Lint | `bun lint` |
| Format | `bun format` |

## Key Conventions
- Phaser pages must be `"use client"` with `next/dynamic` + `ssr: false`
- Linter: Biome (`biome.json`) — not ESLint
- React Compiler is enabled — avoid manual `useMemo`/`useCallback` unless profiling shows a need
