/**
 * Vercel Serverless Function — TTS 代理
 *
 * POST /api/tts
 * 将请求转发到 MiMo API，解决浏览器跨域和 API Key 暴露问题
 */

const MIMO_API_BASE_URL = process.env.MIMO_API_BASE_URL || 'https://token-plan-cn.xiaomimimo.com/v1'
const MIMO_API_KEY = process.env.MIMO_API_KEY

// 免费版 body 上限 4.5MB
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '4.5mb'
    }
  }
}

export default async function handler(req, res) {
  // 只允许 POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: { message: 'Method Not Allowed' } })
  }

  // 优先用页面传来的 key，其次用环境变量
  const pageKey = req.headers['x-api-key']
  const apiKey = pageKey || MIMO_API_KEY
  console.log(`[TTS] key来源: ${pageKey ? '页面' : '环境变量'}, 长度: ${apiKey?.length || 0}`)

  if (!apiKey || apiKey === 'your_api_key_here') {
    return res.status(400).json({
      error: { message: '请在页面中填写 API Key，或在环境变量中配置 MIMO_API_KEY' }
    })
  }

  try {
    const response = await fetch(`${MIMO_API_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(req.body)
    })

    const data = await response.json()

    if (!response.ok) {
      return res.status(response.status).json(data)
    }

    res.json(data)
  } catch (err) {
    console.error('[TTS Proxy] 请求失败:', err.message)
    res.status(500).json({
      error: { message: `代理请求失败: ${err.message}` }
    })
  }
}
