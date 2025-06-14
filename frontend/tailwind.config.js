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
        // New Brand Colors (from design spec)
        primary: {
          DEFAULT: '#FF9966',  // --brand-start
          hover: '#FF8F43',    // --brand-end
        },
        mint: {
          DEFAULT: '#C6F6D5',  // --mint for confidence bars
          dark: '#9AE6B4',
        },
        
        // Dark Mode Colors (Updated)
        dark: {
          base: '#1C1C1E',     // --bg-dark-start
          surface: '#2A2A2D',  // --bg-dark-end
          contrast: '#3A3A3D',
        },
        
        // Light Mode Colors
        light: {
          base: '#FFFFFF',     // --bg-light
          surface: '#F8F9FA',
          contrast: '#E5E5E5',
        },
        
        // Text Colors
        text: {
          main: '#F0F0F0',     // --text-main (dark mode)
          secondary: '#A0A0A0', // --text-secondary
          light: '#1A1A1A',    // --text-light (light mode)
          muted: '#888888',    // --gray-muted
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
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'hero': ['3.5rem', { lineHeight: '1.1', fontWeight: '700' }],
        'hero-lg': ['4rem', { lineHeight: '1.1', fontWeight: '700' }],
      },
      borderRadius: {
        lg: '0.5rem',
        md: '0.375rem', 
        sm: '0.25rem',
        xl: '0.75rem',
        '2xl': '1rem',
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #FF9966 0%, #FF8F43 100%)',
        'gradient-brand-hover': 'linear-gradient(135deg, #FF8F43 0%, #FF7A2A 100%)',
        'gradient-confidence': 'linear-gradient(90deg, #C6F6D5 0%, #9AE6B4 100%)',
        'gradient-dark': 'linear-gradient(145deg, #1C1C1E 0%, #2A2A2D 100%)',
        'gradient-light': 'linear-gradient(145deg, #FFFFFF 0%, #F8F9FA 100%)',
      },
      animation: {
        'scale-in': 'scaleIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-out-right': 'slideOutRight 0.3s ease-in',
      },
      keyframes: {
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        slideOutRight: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      maxWidth: {
        '8xl': '90rem',
      },
    },
  },
  plugins: [],
}