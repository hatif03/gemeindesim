# Node (not Bun) builds the frontend, and dependencies are resolved on Linux from package.json alone.
# Why: both committed lockfiles (bun.lock, package-lock.json) were produced on Windows and contain no Linux native
# packages (lightningcss, tailwind oxide, swc). `bun install --frozen-lockfile`, `npm ci` and `npm install` with the
# lockfile all left them out, and `make run` failed on a clean checkout with
# "Cannot find module '../lightningcss.linux-x64-gnu.node'". Trade-off: versions follow the ranges in package.json
# rather than the lock. `--legacy-peer-deps` avoids an npm arborist crash ("reading edgesOut") on this dependency set.

# ── deps ──────────────────────────────────────────────────────────────
FROM node:22-slim AS deps

WORKDIR /app
COPY package.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund

# ── dev ───────────────────────────────────────────────────────────────
FROM deps AS dev

COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ── builder ───────────────────────────────────────────────────────────
FROM deps AS builder

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ── prod ──────────────────────────────────────────────────────────────
FROM node:22-slim AS prod

WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# standalone output includes only what's needed
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
