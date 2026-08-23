import type { Config } from "tailwindcss";

// Palette is fixed by docs/COLOR_THEME.md. Healthcare + Pakistan + trust.
// Roughly 70-80% white/light neutral: do not fill the UI with dark green.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#017A3A",
          hover: "#015F2D",
          soft: "#EAF6EF",
        },
        page: "#F7FAF8",
        surface: "#FFFFFF",
        ink: "#111827",
        muted: "#667085",
        line: "#DDE7E1",
        info: "#2563EB",
        ok: "#16A34A",
        warn: "#F59E0B",
        danger: "#DC2626",
        camera: "#101828",
      },
      borderRadius: {
        card: "14px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)",
        lift: "0 4px 12px rgba(16,24,40,0.08)",
      },
      fontFamily: {
        sans: ["var(--font-ui)", "system-ui", "sans-serif"],
        urdu: ["var(--font-urdu)", "var(--font-ui)", "sans-serif"],
      },
      fontSize: {
        // Scale from docs/DESIGN_SYSTEM.md
        hero: ["2.25rem", { lineHeight: "1.6" }],
        concept: ["1.6rem", { lineHeight: "1.6" }],
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
      },
      animation: {
        // Subtle state transitions only — no bouncing, glowing or cinematics.
        "fade-up": "fade-up 180ms ease-out",
        "pulse-soft": "pulseSoft 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
