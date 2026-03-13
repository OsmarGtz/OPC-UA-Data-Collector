import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// When running inside Docker, the FastAPI service is reachable at http://api:8000.
// When running locally (npm run dev on the host), it's http://localhost:8000.
const apiTarget = process.env.VITE_API_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,      // bind to 0.0.0.0 so Docker port mapping works
    port: 5173,
    watch: { usePolling: true },   // needed on Windows Docker volumes
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
      '/auth': { target: apiTarget, changeOrigin: true },
    },
  },
})
