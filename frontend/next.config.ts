import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* globe.gl is an ESM-only package that needs transpilation */
  transpilePackages: ["globe.gl", "three"],

  /* Suppress hydration warnings from globe.gl's dynamic DOM manipulation */
  reactStrictMode: false,
};

export default nextConfig;
