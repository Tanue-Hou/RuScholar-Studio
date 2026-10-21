import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

// 与后端读取同一份项目根目录 .env（RS-0002）：已设置的环境变量优先，未设置时默认 8000。
const projectRoot = fileURLToPath(new URL('..', import.meta.url))

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const fileEnv = loadEnv(mode, projectRoot, 'RUSCHOLAR_')
  const port = process.env.RUSCHOLAR_PORT || fileEnv.RUSCHOLAR_PORT || '8000'
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: `http://localhost:${port}`,
          changeOrigin: true,
        },
      },
    },
  }
})
