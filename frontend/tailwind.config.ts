import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#fff8f4",
        "paper-sheet": "#fffdf9",
        manila: "#fcebdd",
        "manila-high": "#f6e5d7",
        "manila-low": "#fff1e6",
        ink: "#221a12",
        "ink-muted": "#58413c",
        "ink-outline": "#8c716b",
        "ink-light": "#e0bfb9",
        terracotta: "#c84b31",
        "terracotta-dark": "#a6331b",
        "fountain-teal": "#286864",
        "teal-light": "#afeee9",
        "vintage-gold": "#d99b26",
        "vintage-gold-dark": "#7c5400",
        "gold-light": "#ffdeae",
      },
      fontFamily: {
        headline: ["Newsreader", "Georgia", "serif"],
        body: ["'Source Serif 4'", "Georgia", "serif"],
        typewriter: ["'Courier Prime'", "Courier", "monospace"],
      },
      boxShadow: {
        stamp: "1px 1px 0px #221a12",
        press: "2px 2px 0px #221a12",
        "press-md": "3px 3px 0px #221a12",
        "press-lg": "4px 4px 0px #221a12",
        dossier: "6px 6px 0px #221a12",
      },
    },
  },
  plugins: [],
};
export default config;
