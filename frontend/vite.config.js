import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// Builds into ../static so FastAPI serves it; Render needs no Node (built files are committed).
export default defineConfig({ plugins: [react()], base: '/static/',
  build: { outDir: '../static', emptyOutDir: true },
  server: { proxy: { '/api': 'http://localhost:8000' } } })
