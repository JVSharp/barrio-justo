/** @type {import('tailwindcss').Config} */
// Sistema visual: beige cálido (clean-minimal-beige-light-mode) + un solo
// acento ámbar, el "sol" del proyecto (orange-clean-paper-saas). El ámbar se
// usa como señal (acción principal, estado activo, calce), no como fondo.
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        arena: {
          50: '#FDFBF7', // superficie de tarjetas
          100: '#F8F4ED', // interior del marco
          200: '#F1EBE1', // fondo de página
          300: '#E6DED1', // bordes suaves
          400: '#D3C8B7',
        },
        sol: {
          50: '#FEF6EC',
          100: '#FDEBD3',
          200: '#FAD3A5',
          300: '#F5B26B',
          400: '#EE913B',
          500: '#E0761D',
          600: '#C45F14', // acción principal (contraste AA con blanco)
          700: '#9F4A13', // texto de acento sobre claro
          800: '#7F3C16',
          900: '#673315',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        // beautiful-shadows: capas neutras, sin tinte de color
        suave:
          '0px 2px 3px -1px rgba(0,0,0,0.1), 0px 1px 0px 0px rgba(25,28,33,0.02), 0px 0px 0px 1px rgba(25,28,33,0.08)',
        panel:
          '0px 0px 0px 1px rgba(0,0,0,0.06), 0px 1px 1px -0.5px rgba(0,0,0,0.06), 0px 3px 3px -1.5px rgba(0,0,0,0.06), 0px 6px 6px -3px rgba(0,0,0,0.06), 0px 12px 12px -6px rgba(0,0,0,0.06), 0px 24px 24px -12px rgba(0,0,0,0.06)',
      },
    },
  },
  plugins: [],
};
