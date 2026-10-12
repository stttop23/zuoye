/**
 * AI 助手：对话状态 + 动作总线
 * ============================
 * 和 userProfile.js 一个套路 —— 状态放在模块顶层，谁 import 都是同一份，
 * 所以关掉聊天窗再打开，对话还在。
 *
 * 三个角色分工：
 *   后端（server/app.py）  负责「听懂人话」，产出 actions
 *   本文件                 负责「执行 actions」，并处理降级
 *   页面（LeaveForm 等）   只负责接草稿，不关心话是谁说的
 */
import { ref } from 'vue'
import router from '@/router'
import { chatWithAgent } from '@/api/ai'

/** 对话记录；meta: true 的条目只是提示，不会发给模型 */
export const agentMessages = ref([
  {
    role: 'assistant',
    content: '我是 AI 助手。试试「下周三到周五请病假，感冒发烧」。',
    meta: true,
  },
])

/** 是否正在等后端回复 */
export const agentSending = ref(false)

/*
 * 抽屉开关为什么放在组件里、而不是这里？
 * 试过把 `export const agentOpen = ref(false)` 共享给组件用，结果 el-drawer
 * 拿到的 `modelValue` 和这个 ref 不是一回事：点 X、按 Esc、点遮罩都关不掉，
 * 代码里 `agentOpen.value = false` 也无效。
 * 所以抽屉开关由 AiAssistant.vue 自己持有，这里只提供「帮我关一下」的回调。
 */
let closeHandler = null

/** 组件挂载时把自己的关闭方法注册进来 */
export function onAgentCloseRequest(handler) {
  closeHandler = handler
}

/** 想收起抽屉时调它（填完表自动收起） */
function requestAgentClose() {
  if (closeHandler) closeHandler()
}

/**
 * 页面「待接收」的填表草稿，形如
 *   { target: 'leave', fields: { type: '病假', startTime: '2026-10-14' } }
 * 这是智能体和页面之间唯一的暗号：谁的名字对得上，谁就去接。
 */
export const pendingDraft = ref(null)

/** 页面拿走属于自己的草稿（拿走即清空，避免同一个草稿被填两次） */
export function consumeDraft(target) {
  if (pendingDraft.value?.target !== target) return null
  const { fields } = pendingDraft.value
  pendingDraft.value = null
  return fields
}

/**
 * 发一句话给智能体。
 * @param {string} text 用户输入
 * @param {{ page?: string, userName?: string }} context 当前页面 / 当前用户，帮模型判断上下文
 */
export async function sendAgentMessage(text, { page, userName } = {}) {
  const content = text.trim()
  if (!content || agentSending.value) return

  agentMessages.value.push({ role: 'user', content })
  agentSending.value = true

  // 只带最近 8 条有效对话，省 token 也省得模型被老话题带偏
  const history = agentMessages.value
    .filter((message) => !message.meta)
    .slice(-8)
    .map((message) => ({ role: message.role, content: message.content }))

  try {
    const data = await chatWithAgent({ messages: history, page, user: userName })
    pushReply(data.reply, data.source)
    runActions(data.actions)
  } catch {
    // 后端起不来（没启动 / 断网 / 没配 key 又崩了）：前端最后兜一层
    const fallback = localFallback(content, page)
    pushReply(fallback.reply, 'local')
    runActions(fallback.actions)
  } finally {
    agentSending.value = false
  }
}

/** 清空对话 */
export function resetAgent() {
  agentMessages.value = agentMessages.value.filter((message) => message.meta)
}

function pushReply(content, source) {
  agentMessages.value.push({ role: 'assistant', content: content || '我这边没生成出内容，再试一次？', source })
}

/**
 * 执行动作清单。
 * 注意：这里【只会】填表 / 跳页，永远不会替用户点提交。
 */
function runActions(actions = []) {
  if (!Array.isArray(actions) || !actions.length) return

  let shouldClose = false
  actions.forEach((action) => {
    if (action.type === 'navigate' && action.path) {
      router.push(action.path)
    } else if (action.type === 'fill' && action.target && action.fields) {
      pendingDraft.value = { target: action.target, fields: action.fields }
      shouldClose = true
    }
  })

  // 填完表把抽屉收起来，让用户直接看到填好的表单
  if (shouldClose) requestAgentClose()
}

/* ==================================================================
 * 前端最后一道兜底：后端彻底挂掉时，用最简单的规则顶一下。
 * 只覆盖最常用的说法，解析不了就老实告诉用户。
 * ================================================================== */
const DATE_PATTERN =
  /(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})|(\d{1,2}\s*月\s*\d{1,2}\s*[日号]?)|(大后天|后天|明天|今天)|(下下周[一二三四五六日天]|下周[一二三四五六日天]|本周[一二三四五六日天]|这周[一二三四五六日天]|周[一二三四五六日天])|(\d+\s*天后)/g

const WEEKDAYS = { 一: 0, 二: 1, 三: 2, 四: 3, 五: 4, 六: 5, 日: 6, 天: 6 }

function toISODate(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function mondayOf(date) {
  const copy = new Date(date)
  const offset = (copy.getDay() + 6) % 7 // 周一 = 0
  copy.setDate(copy.getDate() - offset)
  return copy
}

function addDays(date, days) {
  const copy = new Date(date)
  copy.setDate(copy.getDate() + days)
  return copy
}

/** 把一个日期片段翻译成真正的日期 */
function parseDateToken(token, today) {
  if (/^\d{4}/.test(token)) return new Date(token.replace(/[/.]/g, '-'))
  if (/月/.test(token)) {
    const [month, day] = token.match(/\d+/g).map(Number)
    return new Date(today.getFullYear(), month - 1, day)
  }
  const relative = { 今天: 0, 明天: 1, 后天: 2, 大后天: 3 }[token]
  if (relative !== undefined) return addDays(today, relative)
  if (/天后/.test(token)) return addDays(today, Number(token.match(/\d+/)[0]))

  const target = WEEKDAYS[token.slice(-1)]
  if (token.startsWith('下下周')) return addDays(mondayOf(today), 14 + target)
  if (token.startsWith('下周')) return addDays(mondayOf(today), 7 + target)
  if (token.startsWith('本周') || token.startsWith('这周')) return addDays(mondayOf(today), target)

  const todayIndex = (today.getDay() + 6) % 7 // 周一 = 0
  return addDays(today, (target - todayIndex + 7) % 7)
}

function findDates(text, today) {
  const dates = []
  let weekMonday = null // 最近一次「下周 / 本周」所在的周一

  for (const match of text.matchAll(DATE_PATTERN)) {
    const token = match[0]

    if (/周[一二三四五六日天]$/.test(token)) {
      if (token.startsWith('下下周')) {
        weekMonday = addDays(mondayOf(today), 14)
      } else if (token.startsWith('下周')) {
        weekMonday = addDays(mondayOf(today), 7)
      } else if (token.startsWith('本周') || token.startsWith('这周')) {
        weekMonday = mondayOf(today)
      } else if (weekMonday) {
        // 裸「周X」跟在「下周X」后面 → 算同一周，不然区间会反
        dates.push(addDays(weekMonday, WEEKDAYS[token.slice(-1)]))
        continue
      }
    }

    const value = parseDateToken(token, today)
    if (value instanceof Date && !Number.isNaN(value.getTime())) dates.push(value)
  }

  return dates
}

function localFallback(text, page) {
  const today = new Date()

  if (/请假|病假|事假|年假|休假/.test(text)) {
    const dates = findDates(text, today)
    if (!dates.length) {
      return { reply: '没听出是哪几天，换个说法？（比如：下周三到周五）', actions: [] }
    }

    const start = dates[0]
    let end = dates[1]
    if (!end) {
      const duration = text.match(/(\d+|[一二两三四五六七八九十]+)\s*天/)
      end = duration ? addDays(start, Number(duration[1]) - 1) : start
    }
    if (end < start) end = start

    const type = /病|发烧|感冒|头疼|不舒服|医院/.test(text)
      ? '病假'
      : /年假|调休/.test(text)
        ? '年假'
        : '事假'

    const reason = text
      .replace(DATE_PATTERN, '')
      .replace(/请假|请个假|我想|我要|帮我|申请|的|了|，|。|、/g, '')
      .trim()

    const fields = { type, startTime: toISODate(start), endTime: toISODate(end) }
    if (reason.length >= 5) fields.reason = reason

    return {
      reply: `【本地兜底】认成 ${type} ${fields.startTime} ~ ${fields.endTime}，已填进表单，确认后再提交。`,
      actions: [{ type: 'fill', target: 'leave', fields }],
    }
  }

  if (/待办|任务/.test(text)) {
    const title = text.replace(/^(帮我|我要|我想|新建|添加|加个|建个)+/, '').trim().slice(0, 40)
    return {
      reply: '【本地兜底】已把标题预填进新建弹窗，确认后保存。',
      actions: [{ type: 'fill', target: 'todo', fields: { title } }],
    }
  }

  for (const [path, name] of Object.entries({
    '/dashboard': '工作台',
    '/notice': '公告通知',
    '/leave': '请假申请',
    '/todo': '待办事项',
  })) {
    if (text.includes(name)) {
      return { reply: `【本地兜底】带你到「${name}」。`, actions: [{ type: 'navigate', path }] }
    }
  }

  return { reply: '后端没连上，本地兜底也认不出这句。先把 server/app.py 跑起来试试。', actions: [] }
}
