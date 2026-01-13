/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff', 100: '#e0f2fe', 200: '#bae6fd', 300: '#7dd3fc', 400: '#38bdf8',
          500: '#0ea5e9', 600: '#0284c7', 700: '#0369a1', 800: '#075985', 900: '#0c4a6e',
        },
        surface: {
          light: '#ffffff',
          dark: '#0b0b0c',
          cardLight: '#ffffffcc',
          cardDark: '#111827cc',
          borderLight: '#e5e7eb',
          borderDark: '#374151',
        },
      },
      fontFamily: { sans: ['DM Sans','system-ui','sans-serif'] },
      boxShadow: {
        'glass': '0 1px 2px 0 rgba(0,0,0,.06), 0 6px 20px rgba(0,0,0,.08)'
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        slideUp: { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        bounceIn: { '0%': { transform: 'scale(.3)', opacity: '0' }, '50%': { transform: 'scale(1.05)' }, '70%': { transform: 'scale(.9)' }, '100%': { transform: 'scale(1)', opacity: '1' } },
      },
      animation: {
        'fade-in': 'fadeIn .35s ease-in-out',
        'slide-up': 'slideUp .25s ease-out',
        'bounce-in': 'bounceIn .6s ease-out',
      },
    },
    screens: {
      xs: '320px',
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1536px',
    },
  },
  plugins: [],
}

