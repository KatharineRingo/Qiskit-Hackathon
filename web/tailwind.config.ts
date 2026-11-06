import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: { ink: "#05060a", paper: "#f0efeb", dmg: "#ff6a1f", water: "#4b93ff", today: "#a78bfa" },
      fontFamily: { sans: ["var(--font-inter-tight)", "system-ui", "sans-serif"], mono: ["var(--font-mono)", "monospace"] },
    },
  },
  plugins: [],
};
export default config;
