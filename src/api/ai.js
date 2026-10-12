/**
 * AI 助手接口层（唯一跟「后端怎么实现」有关的地方）
 * =================================================
 * 只认下面这一份契约：
 *
 *   请求  POST /api/ai/chat
 *         { messages: [{role, content}], page: '/leave', user: '刘皖' }
 *
 *   响应  { ok: true, source: 'ai' | 'local', reply: '...', actions: [...] }
 *
 * 契约不变，换模型 / 换后端语言 / 换服务器，前端一行都不用改。
 *
 * 开发时请求走 vite 代理（/api → http://127.0.0.1:5000），所以这里写相对路径就行；
 * 上线后把 .env 里的 VITE_AI_BASE_URL 改成线上代理地址。
 */
const BASE_URL = import.meta.env.VITE_AI_BASE_URL || '/api'

export async function chatWithAgent({ messages, page, user }) {
  const response = await fetch(`${BASE_URL}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, page, user }),
  })

  // 后端没启动 / 500 / 502 → 抛出异常，由上层走本地兜底
  if (!response.ok) {
    throw new Error(`AI 代理返回 ${response.status}`)
  }

  const data = await response.json()
  if (!data.ok) {
    throw new Error(data.reply || 'AI 代理不可用')
  }

  return { actions: [], reply: '', source: 'ai', ...data }
}
