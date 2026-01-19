import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const API_TARGET = import.meta.env.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
})
