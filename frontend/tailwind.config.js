/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F5F1E8",
        foreground: "#1A1A14",
        primary: {
          DEFAULT: "#0F3D2E",
          foreground: "#FAFAF8",
          light: "#DFF2E8",
        },
        secondary: {
          DEFAULT: "#EDE9E0",
          foreground: "#3D3D30",
        },
        muted: {
          DEFAULT: "#E8E4DA",
          foreground: "#6B6B55",
        },
        accent: {
          DEFAULT: "#DFF2E8",
          foreground: "#0F3D2E",
        },
        gold: {
          DEFAULT: "#C8A96B",
          light: "#F0E4C4",
          dark: "#A8893B",
          foreground: "#3D2A00",
        },
        border: "#E0DAD0",
        card: "#FFFFFF",
        success: {
          DEFAULT: "#2E7D5E",
          light: "#DFF2E8",
          foreground: "#FFFFFF",
        },
        destructive: {
          DEFAULT: "#C43A2A",
          foreground: "#FFFFFF",
          light: "#FDE8E5",
        },
        warning: {
          DEFAULT: "#D97706",
          light: "#FEF3C7",
          foreground: "#FFFFFF",
        },
      },
      fontFamily: {
        sans: [
          "var(--font-jakarta)",
          "var(--font-inter)",
          "-apple-system",
          "BlinkMacSystemFont",
          "sans-serif",
        ],
        mono: ["var(--font-inter)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "0.375rem",
        DEFAULT: "0.625rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.25rem",
        "2xl": "1.5rem",
        "3xl": "2rem",
        "4xl": "3rem",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(15 61 46 / 0.06), 0 1px 2px -1px rgb(15 61 46 / 0.04)",
        "card-md": "0 4px 6px -1px rgb(15 61 46 / 0.08), 0 2px 4px -2px rgb(15 61 46 / 0.04)",
        "card-lg": "0 10px 15px -3px rgb(15 61 46 / 0.08), 0 4px 6px -4px rgb(15 61 46 / 0.04)",
        float: "0 20px 25px -5px rgb(15 61 46 / 0.12), 0 8px 10px -6px rgb(15 61 46 / 0.08)",
        glow: "0 0 0 3px rgb(15 61 46 / 0.15)",
        "glow-gold": "0 0 0 3px rgb(200 169 107 / 0.25)",
        "inner-sm": "inset 0 1px 2px 0 rgb(0 0 0 / 0.06)",
      },
      backgroundImage: {
        "primary-gradient": "linear-gradient(135deg, #0F3D2E 0%, #1A6647 100%)",
        "gold-gradient": "linear-gradient(135deg, #C8A96B 0%, #E8C98A 100%)",
        "hero-pattern": "radial-gradient(ellipse at top, #1A6647 0%, #0F3D2E 65%)",
        "card-shine": "linear-gradient(135deg, rgb(255 255 255 / 0.12) 0%, transparent 50%)",
      },
      animation: {
        "slide-up": "slide-up 0.3s cubic-bezier(0.32, 0.72, 0, 1) both",
        "slide-down": "slide-down 0.25s cubic-bezier(0.32, 0.72, 0, 1) both",
        "fade-in": "fade-in 0.2s ease-out both",
        "scale-in": "scale-in 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) both",
        shimmer: "shimmer 1.6s infinite",
      },
      keyframes: {
        "slide-up": {
          from: { transform: "translateY(100%)" },
          to: { transform: "translateY(0)" },
        },
        "slide-down": {
          from: { transform: "translateY(-100%)" },
          to: { transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "scale-in": {
          from: { transform: "scale(0.94)", opacity: "0" },
          to: { transform: "scale(1)", opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};

module.exports = config;
