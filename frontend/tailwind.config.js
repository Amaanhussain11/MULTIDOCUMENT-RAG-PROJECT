/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#09090B",
          secondary: "#0F1014",
          tertiary: "#14161B",
        },
        card: {
          DEFAULT: "#111318",
          hover: "#171A21",
          elevated: "#181B22",
        },
        border: {
          DEFAULT: "#272A33",
          subtle: "#1D2027",
          active: "#3A3F4B",
        },
        primary: {
          DEFAULT: "#6366F1",
          hover: "#818CF8",
          active: "#4F46E5",
        },
        text: {
          primary: "#F4F4F5",
          secondary: "#A1A1AA",
          muted: "#71717A",
          disabled: "#52525B",
        },
        status: {
          success: "#22C55E",
          warning: "#F59E0B",
          error: "#EF4444",
          info: "#38BDF8",
        },
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      maxWidth: {
        layout: "1400px",
        content: "1200px",
      },
    },
  },
  plugins: [],
};
