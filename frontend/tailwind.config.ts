import type { Config } from "tailwindcss";

// `<alpha-value>` is required for opacity modifiers such as bg-primary/10 to work with CSS-variable colors.
const c = (name: string) => `hsl(var(--${name}) / <alpha-value>)`;

const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: c("background"),
        foreground: c("foreground"),
        card: c("card"),
        muted: { DEFAULT: c("muted"), foreground: c("muted-foreground") },
        border: c("border"),
        primary: { DEFAULT: c("primary"), foreground: c("primary-foreground") },
        danger: c("danger"),
        success: c("success"),
        warning: c("warning"),
      },
      fontFamily: {
        sans: ["Vazirmatn", "Vazir", "Segoe UI", "Tahoma", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Cascadia Code", "Consolas", "Menlo", "monospace"],
      },
      borderRadius: { lg: "0.75rem", md: "0.5rem" },
    },
  },
  plugins: [],
};

export default config;
