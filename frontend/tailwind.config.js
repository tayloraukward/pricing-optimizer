/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Linear/Modern Design System Colors
        'background-deep': '#020203',
        'background-base': '#050506',
        'background-elevated': '#0a0a0c',
        'surface': 'rgba(255,255,255,0.05)',
        'surface-hover': 'rgba(255,255,255,0.08)',
        'foreground': '#EDEDEF',
        'foreground-muted': '#8A8F98',
        'foreground-subtle': 'rgba(255,255,255,0.60)',
        'accent': '#5E6AD2',
        'accent-bright': '#6872D9',
        'accent-glow': 'rgba(94,106,210,0.3)',
        'border-default': 'rgba(255,255,255,0.06)',
        'border-hover': 'rgba(255,255,255,0.10)',
        'border-accent': 'rgba(94,106,210,0.30)',
      },
      fontFamily: {
        sans: ['Inter', 'Geist Sans', 'system-ui', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(ellipse_at_top,#0a0a0f_0%,#050506_50%,#020203_100%)',
        'gradient-text': 'linear-gradient(to bottom, #ffffff, #ffffff/95, #ffffff/70)',
        'gradient-accent': 'linear-gradient(to right, #5E6AD2, #818cf8, #5E6AD2)',
        'surface-gradient': 'linear-gradient(to bottom, rgba(255,255,255,0.08), rgba(255,255,255,0.02))',
      },
      boxShadow: {
        'card': '0 0 0 1px rgba(255,255,255,0.06), 0 2px 20px rgba(0,0,0,0.4), 0 0 40px rgba(0,0,0,0.2)',
        'card-hover': '0 0 0 1px rgba(255,255,255,0.1), 0 8px 40px rgba(0,0,0,0.5), 0 0 80px rgba(94,106,210,0.1)',
        'accent-glow': '0 0 0 1px rgba(94,106,210,0.5), 0 4px 12px rgba(94,106,210,0.3), inset 0 1px 0 0 rgba(255,255,255,0.2)',
        'inner-highlight': 'inset 0 1px 0 0 rgba(255,255,255,0.1)',
      },
      animation: {
        'float': 'float 8s ease-in-out infinite',
        'shimmer': 'shimmer 3s ease-in-out infinite',
        'fade-up': 'fadeUp 0.6s ease-out',
        'scale-in': 'scaleIn 0.6s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
          '50%': { transform: 'translateY(-20px) rotate(1deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
      },
      backdropBlur: {
        'xs': '2px',
      },
      transitionTimingFunction: {
        'expo-out': '[0.16, 1, 0.3, 1]',
      },
      transitionDuration: {
        '250': '250ms',
      },
    },
  },
  plugins: [],
}
