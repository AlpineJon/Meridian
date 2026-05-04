import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
      colors: {
        // Neutral data palette (for raw numbers, charts, structure)
        ink: {
          50: "#f7f8fa",
          100: "#eef0f4",
          200: "#dde1e8",
          300: "#bbc2cd",
          400: "#8a93a3",
          500: "#5d6675",
          600: "#3f4754",
          700: "#2a313c",
          800: "#1c2129",
          900: "#11141a",
          950: "#0a0c10",
        },
        accent: {
          DEFAULT: "#3b82f6",
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        // Reserved for directional credit signals only
        signal: {
          good: "#16a34a",
          goodBg: "#dcfce7",
          warn: "#d97706",
          warnBg: "#fef3c7",
          bad: "#dc2626",
          badBg: "#fee2e2",
        },
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "0.875rem" }],
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
    },
  },
  plugins: [],
};

export default config;
