import path from "node:path";
import { fileURLToPath } from "node:url";
import type { NextConfig } from "next";

const dir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  reactCompiler: true,
  reactStrictMode: false,
  output: process.env.NODE_ENV === "production" ? "standalone" : undefined,
  turbopack: {
    root: dir,
  },
};

export default nextConfig;
