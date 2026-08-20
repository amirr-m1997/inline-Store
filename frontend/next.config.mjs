/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Keep the deterministic Playwright server isolated from a developer's running .next instance.
  distDir: process.env.NEXT_TEST_DIST_DIR || ".next",
  // Preserve DRF's slash-terminated routes before they reach the local proxy handler.
  skipTrailingSlashRedirect: true,
  // `next dev` blocks cross-origin requests to dev-only assets by default.
  // Allow access from other devices on the local network (LAN IP) so the
  // static JS chunks hydrate and the theme toggle/interactive UI works there.
  allowedDevOrigins: (process.env.ALLOWED_DEV_ORIGINS || "192.168.3.140").split(",").map((item) => item.trim()).filter(Boolean),
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost", port: "8000", pathname: "/media/**" },
      { protocol: "http", hostname: "127.0.0.1", port: "8000", pathname: "/media/**" },
      { protocol: "http", hostname: "192.168.3.140", port: "8000", pathname: "/media/**" },
    ],
  },
};
export default nextConfig;
