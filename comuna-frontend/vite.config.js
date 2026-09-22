import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // En GitHub Pages el sitio vive en /comuna-dash/; en local, en la raíz.
  base: process.env.VITE_BASE || '/',
  build: {
    // Recharts solo ya pesa ~510 kB (150 kB gzip); el aviso por defecto es 500.
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      // Recharts pesa más que toda la app: en su propio chunk se cachea aparte.
      output: { manualChunks: { recharts: ['recharts'] } },
    },
  },
})
