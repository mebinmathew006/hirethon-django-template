import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: '/',
  plugins: [tailwindcss()],
  server: {
    host: '127.0.0.1',       // 🔓 Allow access from Docker host
    port: 5173,            // 📦 Match Docker port
    watch: {
      usePolling: true,    // 🔁 Enable polling to detect file changes
    },
  },
})
