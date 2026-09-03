import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#07080b",
        surface: "#0b0d12",
        "surface-elevated": "#10131a",
        "surface-raised": "#151923",
        border: "#1c2130",
        "border-strong": "#2a3145",
        "text-primary": "#e6e8ee",
        "text-secondary": "#8b93a7",
        "text-muted": "#4a5064",
        estimated: "#4c8dff",
        truth: "#f5a524",
        error: "#f04747",
        confident: "#3fb950",
        uncertain: "#f0883e",
        accent: "#22d3ee",
        glow: "#4c8dff",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(76, 141, 255, 0.35), 0 0 24px rgba(76, 141, 255, 0.12)",
        panel: "inset 0 1px 0 rgba(255, 255, 255, 0.03)",
      },
      letterSpacing: {
        wider: "0.08em",
        widest: "0.18em",
      },
    },
  },
  plugins: [],
};

export default config;
