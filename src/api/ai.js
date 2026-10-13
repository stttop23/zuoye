/**
 * AI 助手接口层（唯一跟「后端怎么实现」有关的地方）
 * =================================================
 * 只认下面这一份契约：
 *
 *   请求  POST /api/ai/chat
 *         { messages: [{role, content}], page: '/leave', user: '刘皖', data: {...} }
 *
 *        data 是「现场快照」（待办 / 公告 / 请假记录 / 打卡状态），
 *        由 src/composables/appStore.js 的 agentSnapshot() 提供。
 *        后端的只读工具（查待办、查请假……）优先用它，读到的就是页面上那一份。
 *
 *   响应  { ok: true, source: 'ai' | 'local', reply: '...', actions: [...] }
 *
 * 契约不变，换模型 / 换后端语言 / 换服务器，前端一行都不用改。
 *
 * 开发时请求走 vite 代理（/api → http://127.0.0.1:5000），所以这里写相对路径就行。
 * `preview` 也是同样的代理（实测过）；本项目不做线上部署，故 VITE_AI_BASE_URL 留空，
 * 只有将来真的前后端分域部署了，才需要把它指到代理地址。
 */
const BASE_URL = import.meta.env.VITE_AI_BASE_URL || '/api'

export async function chatWithAgent({ messages, page, user, snapshot }) {
  const response = await fetch(`${BASE_URL}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, page, user, data: snapshot }),
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
