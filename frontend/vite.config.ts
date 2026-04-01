import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  console.log('API URL:', env.VITE_GLOB_API_URL)

  return ({
  plugins: [
    vue(),
    command === 'serve' ? vueDevTools() : undefined,
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  esbuild: {
    drop: ['console', 'debugger'],
  },
  server: {
    host: '0.0.0.0',
    port: 5001,
    cors: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: env.VITE_GLOB_API_URL,
        //target: 'http://127.0.0.1:5000',
        changeOrigin: true,
        secure: false,
        //rewrite: (path) => path.replace(/^\/api/, '') // 去掉/api前缀（按需）
      },
    },
  },
  })
})