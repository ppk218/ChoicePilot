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
        // Primary Brand Colors
        primary: {
          DEFAULT: '#FF9966',
          hover: '#FF8F43',
        },
        accent: {
          DEFAULT: '#C6F6D5',
          hover: '#9AE6B4',
        },
        
        // Dark Mode Colors (Updated)
        dark: {
          base: '#1C1C1E',
          surface: '#2A2A2D', 
          contrast: '#393A3D',
        },
        
        // Light Mode Colors (Updated)
        light: {
          base: '#FCFCFD',
          surface: '#F2F2F5',
          contrast: '#E4E4EA',
        },
        
        // Secondary Colors
        secondary: {
          purple: '#7A5FFF',
          teal: '#2EC4B6',
          yellow: '#FFC75F',
          coral: '#EF476F',
        },
        
        // Dynamic theme colors
        background: {
          DEFAULT: 'var(--background)',
        },
        foreground: {
          DEFAULT: 'var(--foreground)',
        },
        card: {
          DEFAULT: 'var(--card)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        border: {
          DEFAULT: 'var(--border)',
        },
        input: {
          DEFAULT: 'var(--input)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem', 
        sm: '0.25rem',
        xl: '0.75rem', // Added for modern buttons
      },
      backgroundImage: {
        'gradient-dark': 'linear-gradient(145deg, #1C1C1E, #252528, #2A2A2D)',
        'gradient-cta': 'linear-gradient(135deg, #FF9966, #FF8F43)',
        'gradient-confidence': 'linear-gradient(90deg, #C6F6D5, #2EC4B6)',
        'gradient-light': 'linear-gradient(135deg, #FFFFFF 0%, #F4F4F7 100%)',
      },
      animation: {
        'pulse-soft': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}