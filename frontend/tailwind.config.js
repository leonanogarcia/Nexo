/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Segoe UI"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        nexo: {
          orange: '#F28C28',
          orangeHover: '#BA5200',
          orangeLight: '#F6A45A',
          brown: '#693A16',
          navy: '#111C30',
          textDark: '#18223A',
          muted: '#687796',
          line: '#DDE5F2',
          bgLight: '#F4F7FC',
          bgDark: '#081226',
          panelDark: '#111F3B',
          fieldDark: '#0E1B35',
        }
      }
    },
  },
  plugins: [],
}
