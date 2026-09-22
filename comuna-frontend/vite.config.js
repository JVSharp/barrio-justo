import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // En GitHub Pages el sitio vive en /barrio-justo/; en local, en la raíz.
  base: process.env.VITE_BASE || '/',
  build: {
    // Recharts pesa ~510 kB y el mapa (MapLibre + deck.gl) ~2 MB, pero el mapa se
    // carga solo al abrir su pestaña (React.lazy), no en la carga inicial.
    chunkSizeWarningLimit: 2200,
    rollupOptions: {
      // Recharts pesa más que toda la app: en su propio chunk se cachea aparte.
      output: { manualChunks: { recharts: ['recharts'] } },
    },
  },
})
