/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './public/index.html',
  ],
  theme: {
    extend: {
      colors: {
        // Custom getgingee colors
        background: {
          DEFAULT: '#2C2C2E',  // Dark background
          light: '#FFFFFF',    // Light background
        },
        foreground: {
          DEFAULT: '#FFF8F0',  // Dark mode text
          light: '#1A1A1A',    // Light mode text
        },
        primary: {
          DEFAULT: '#FF9966',
          hover: '#FF8A4D',
          light: '#FFB380',
        },
        accent: {
          DEFAULT: '#C6F6D5',
          hover: '#9AE6B4',
        },
        muted: {
          DEFAULT: '#3A3A3C',
          foreground: '#A1A1AA',
        },
        border: {
          DEFAULT: '#3A3A3C',
          light: '#E5E5E5',
        },
        input: {
          DEFAULT: '#3A3A3C',
          light: '#F5F5F5',
        },
        card: {
          DEFAULT: '#1C1C1E',
          light: '#FFFFFF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem',
        sm: '0.25rem',
      },
    },
  },
  plugins: [],
}