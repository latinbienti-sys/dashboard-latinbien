import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow pdf-parse to work in API routes
  serverExternalPackages: ["pdf-parse"],
};

export default nextConfig;
