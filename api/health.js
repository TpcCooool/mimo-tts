/**
 * Vercel Serverless Function — 健康检查
 *
 * GET /api/health
 */

const MIMO_API_KEY = process.env.MIMO_API_KEY
const MIMO_API_BASE_URL = process.env.MIMO_API_BASE_URL || 'https://token-plan-cn.xiaomimimo.com/v1'

export default function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: { message: 'Method Not Allowed' } })
  }

  res.json({
    status: 'ok',
    apiKeyConfigured: !!MIMO_API_KEY && MIMO_API_KEY !== 'your_api_key_here',
    apiBaseUrl: MIMO_API_BASE_URL
  })
}
