import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  server: {
    port: 5173,
    proxy: {
      '/executions': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/voice': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8765',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
