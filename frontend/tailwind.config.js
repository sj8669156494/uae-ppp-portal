/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#1a5276',
          light: '#2980b9',
          dark: '#0d2e47',
        },
        gold: '#c9a227',
      },
    },
  },
  plugins: [],
}
