/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Keep the deterministic Playwright server isolated from a developer's running .next instance.
  distDir: process.env.NEXT_TEST_DIST_DIR || ".next",
  // Preserve DRF's slash-terminated routes before they reach the local proxy handler.
  skipTrailingSlashRedirect: true,
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" },
      { protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" },
    ],
  },
};
export default nextConfig;
