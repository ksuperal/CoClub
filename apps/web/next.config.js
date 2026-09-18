/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Pruned, self-contained build output for the Docker image (Dockerfile copies
  // just .next/standalone instead of shipping full node_modules).
  output: "standalone",
};

module.exports = nextConfig;
