import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: { colors: { ink: '#17323A', paper: '#F7F6F1', teal: '#0E8175', mist: '#E7F0ED', amber: '#B66A16', coral: '#C4463D', slate: '#64757A' }, fontFamily: { display: ['Plus Jakarta Sans', 'ui-sans-serif', 'system-ui'], sans: ['Inter', 'ui-sans-serif', 'system-ui'] }, boxShadow: { soft: '0 10px 30px rgba(23,50,58,.08)' } } },
  plugins: []
} satisfies Config
