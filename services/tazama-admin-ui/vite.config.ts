import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/v1/admin': {
        target: 'http://localhost:3100',
        changeOrigin: true,
      }
    }
  }
})
