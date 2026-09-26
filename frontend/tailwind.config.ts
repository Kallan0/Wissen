import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "rgb(var(--paper) / <alpha-value>)",
        "paper-sheet": "rgb(var(--paper-sheet) / <alpha-value>)",
        manila: "rgb(var(--manila) / <alpha-value>)",
        "manila-high": "rgb(var(--manila-high) / <alpha-value>)",
        "manila-low": "rgb(var(--manila-low) / <alpha-value>)",
        ink: "rgb(var(--ink) / <alpha-value>)",
        "ink-muted": "rgb(var(--ink-muted) / <alpha-value>)",
        "ink-outline": "rgb(var(--ink-outline) / <alpha-value>)",
        "ink-light": "rgb(var(--ink-light) / <alpha-value>)",
        terracotta: "rgb(var(--terracotta) / <alpha-value>)",
        "terracotta-dark": "rgb(var(--terracotta-dark) / <alpha-value>)",
        "fountain-teal": "rgb(var(--fountain-teal) / <alpha-value>)",
        "teal-light": "rgb(var(--teal-light) / <alpha-value>)",
        "vintage-gold": "rgb(var(--vintage-gold) / <alpha-value>)",
        "vintage-gold-dark": "rgb(var(--vintage-gold-dark) / <alpha-value>)",
        "gold-light": "rgb(var(--gold-light) / <alpha-value>)",
      },
      fontFamily: {
        headline: ["Newsreader", "Georgia", "serif"],
        body: ["'Source Serif 4'", "Georgia", "serif"],
        typewriter: ["'Courier Prime'", "Courier", "monospace"],
      },
      boxShadow: {
        stamp: "1px 1px 0px rgb(var(--shadow-ink))",
        press: "2px 2px 0px rgb(var(--shadow-ink))",
        "press-md": "3px 3px 0px rgb(var(--shadow-ink))",
        "press-lg": "4px 4px 0px rgb(var(--shadow-ink))",
        dossier: "6px 6px 0px rgb(var(--shadow-ink))",
      },
    },
  },
  plugins: [],
};
export default config;
