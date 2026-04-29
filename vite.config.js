import { readFileSync } from 'fs'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 本地开发加载 .env 到 process.env（线上由 Vercel 注入）
try {
  const env = readFileSync('.env', 'utf-8')
  for (const line of env.split('\n')) {
    const match = line.match(/^\s*([\w]+)\s*=\s*(.*?)\s*$/)
    if (match) process.env[match[1]] = match[2]
  }
} catch {}

// 包装 Node 原生 res，补充 Vercel 风格的 res.json() / res.status()
function wrapRes(res) {
  const wrapped = Object.create(res)
  wrapped.status = (code) => {
    res.statusCode = code
    return wrapped
  }
  wrapped.json = (data) => {
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(data))
  }
  return wrapped
}

// 本地开发：将 /api 请求代理到 api/ 下的 Serverless Functions
function apiPlugin() {
  return {
    name: 'api-middleware',
    configureServer(server) {
      server.middlewares.use('/api/tts', async (req, res) => {
        const { default: handler } = await import('./api/tts.js')
        req.body = await new Promise((resolve) => {
          let data = ''
          req.on('data', (chunk) => (data += chunk))
          req.on('end', () => resolve(JSON.parse(data)))
        })
        await handler(req, wrapRes(res))
      })
      server.middlewares.use('/api/health', async (req, res) => {
        const { default: handler } = await import('./api/health.js')
        await handler(req, wrapRes(res))
      })
    }
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), apiPlugin()]
})
