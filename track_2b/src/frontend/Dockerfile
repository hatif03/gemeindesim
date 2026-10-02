# ── deps ──────────────────────────────────────────────────────────────
FROM oven/bun:1.2 AS deps

WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

# ── dev ───────────────────────────────────────────────────────────────
FROM deps AS dev

COPY . .
EXPOSE 3000
CMD ["bun", "dev"]

# ── builder ───────────────────────────────────────────────────────────
FROM deps AS builder

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NODE_ENV=production

RUN bun run build

# ── prod ──────────────────────────────────────────────────────────────
FROM oven/bun:1.2-slim AS prod

WORKDIR /app
ENV NODE_ENV=production

# standalone output includes only what's needed
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
