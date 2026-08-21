import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#06060a",
        surface: "#0f1117",
        "surface-elevated": "#161922",
        border: "#1e2130",
        "text-primary": "#e4e4e7",
        "text-secondary": "#71717a",
        "text-muted": "#3f3f46",
        estimated: "#3b82f6",
        truth: "#f59e0b",
        error: "#ef4444",
        confident: "#22c55e",
        uncertain: "#f97316",
        glow: "#60a5fa",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(59, 130, 246, 0.15)",
      },
    },
  },
  plugins: [],
};

export default config;
