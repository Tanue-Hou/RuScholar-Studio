import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

// 端口来源与后端（services/config.py）完全一致（RS-0002）：
// 只读项目根目录的 .env（不读 .env.local、.env.<mode>），已设置的环境变量优先，空值或缺省时为 8000。
// 解析规则同 Python：忽略注释与空行，支持 export 前缀、成对引号、行尾 " #" 注释，重复的键以第一次出现为准。
function readProjectEnv(file: string): Record<string, string> {
  let text: string
  try {
    text = readFileSync(file, 'utf-8')
  } catch {
    return {}
  }
  const out: Record<string, string> = {}
  for (const raw of text.split(/\r?\n/)) {
    let line = raw.trim()
    if (!line || line.startsWith('#') || !line.includes('=')) continue
    if (line.startsWith('export ')) line = line.slice('export '.length).trim()
    const i = line.indexOf('=')
    const key = line.slice(0, i).trim()
    let value = line.slice(i + 1).trim()
    if (value.length >= 2 && value[0] === value[value.length - 1] && (value[0] === '"' || value[0] === "'")) {
      value = value.slice(1, -1)
    } else if (value.includes(' #')) {
      value = value.split(' #')[0].trimEnd()
    }
    if (key && !(key in out)) out[key] = value
  }
  return out
}

const envFile = fileURLToPath(new URL('../.env', import.meta.url))

// https://vite.dev/config/
export default defineConfig(() => {
  const configured = process.env.RUSCHOLAR_PORT !== undefined
    ? process.env.RUSCHOLAR_PORT
    : readProjectEnv(envFile).RUSCHOLAR_PORT
  const port = configured || '8000'
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: `http://127.0.0.1:${port}`,
          changeOrigin: true,
        },
      },
    },
  }
})
