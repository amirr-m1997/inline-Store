import type { Config } from "tailwindcss";
const config: Config = { darkMode: "class", content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"], theme: { extend: { colors: { brand: { red: "#c62b35", blue: "#1e63a8", surface: "#f6f8fb" } }, boxShadow: { card: "0 6px 18px rgba(26, 43, 64, 0.08)" } } }, plugins: [] };
export default config;
