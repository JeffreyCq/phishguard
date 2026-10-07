/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        heading: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        // "Bitcoin DeFi" tokens
        void:    '#030304',
        matter:  '#0F1115',
        stardust:'#94A3B8',
        btc:     '#F7931A',
        burnt:   '#EA580C',
        gold:    '#FFD600',

        // Remap legacy palettes so every existing component inherits the theme.
        slate: {
          950: '#030304',
          900: '#0F1115',
          800: '#1E293B',
        },
        indigo: {
          200: '#FFE0B0',
          300: '#FFB347',
          400: '#F7931A',
          500: '#F7931A',
          600: '#EA580C',
        },
        violet: {
          300: '#FFE566',
          400: '#FFD600',
          500: '#FFD600',
        },
      },
      boxShadow: {
        glow:       '0 0 20px -5px rgba(234,88,12,0.5)',
        'glow-lg':  '0 0 30px -5px rgba(247,147,26,0.6)',
        'glow-gold':'0 0 20px rgba(255,214,0,0.3)',
        'glow-soft':'0 0 50px -10px rgba(247,147,26,0.1)',
        'glow-card':'0 0 30px -10px rgba(247,147,26,0.2)',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-12px)' },
        },
      },
      animation: {
        float: 'float 8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
