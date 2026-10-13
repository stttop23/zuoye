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

/**
 * 对话记录，一开始是空的：
 * 输入框上方那三个快捷短语已经把「能说什么」讲清楚了，再放一句欢迎语只是占地方。
 * （meta: true 的条目只当提示、不会发给模型，这个开关留着给以后用。）
 */
export const agentMessages = ref([])

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
 * 和 pendingDraft 同一套思路，但装的是【命令】而不是表单草稿。
 * 形如 { target: 'todo', type: 'todo_action', action: 'complete', title: '…' }。
 *
 * 为什么分开两个 ref：填表要把值填进表单、等用户点提交；
 * 命令是「直接做掉」的（打卡、完成待办、撤销申请）。混在一起容易误处理。
 */
export const pendingCommand = ref(null)

/** 页面拿走属于自己的命令（拿走即清空，避免重复执行） */
export function consumeCommand(target) {
  if (pendingCommand.value?.target !== target) return null
  const command = pendingCommand.value
  pendingCommand.value = null
  return command
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
  agentMessages.value = []
}

function pushReply(content, source) {
  agentMessages.value.push({
    role: 'assistant',
    content: content || '我这边没生成出内容，再试一次？',
    source,
  })
}

/**
 * 每个「填表目标」对应的页面。
 * 填完必须把用户带过去——否则他停在别的页面上，什么都看不见，
 * 只会觉得「AI 什么都没干」。
 */
const FILL_TARGET_PAGES = {
  leave: '/leave',
  todo: '/todo',
}

/**
 * 命令类动作 → 交给哪个页面、要不要先跳页。
 * ⚠️ 目标页面和归属不是一回事：
 *   target 是谁来接这份命令（页面里 watch pendingCommand 的那个人）；
 *   page   是执行前要不要先跳过去（system 类不用跳，侧边栏本来就常驻）。
 * ⚠️ 忘了在这张表里登记的动作，runActions 里会直接报 ReferenceError ——
 *    而且异常会被 sendAgentMessage 的 catch 吞掉，界面表现成「后端没连上」。
 */
const COMMAND_ROUTES = {
  checkin: { target: 'checkin', page: '/dashboard' },
  checkin_undo: { target: 'checkin', page: '/dashboard' },
  todo_action: { target: 'todo', page: '/todo' },
  leave_cancel: { target: 'leave', page: '/leave' },
  leave_review: { target: 'leave', page: '/leave' },
  notice_open: { target: 'notice', page: '/notice' },
  switch_role: { target: 'system', page: null },
  rename_user: { target: 'system', page: null },
  toggle_setting: { target: 'system', page: null },
}

/**
 * 执行动作清单。
 * 注意：这里【只会】填表和跳页，永远不会替用户点提交——跳过去就是为了让他确认。
 */
function runActions(actions = []) {
  if (!Array.isArray(actions) || !actions.length) return

  let shouldClose = false
  const jumped = new Set()

  // 同一个页面只跳一次：模型可能既给 navigate 又给 fill，别跳两遍
  function goTo(path) {
    if (!path || jumped.has(path)) return
    jumped.add(path)
    if (router.currentRoute.value.path !== path) router.push(path)
  }

  actions.forEach((action) => {
    /*
     * 每个动作单独 try：一个动作出错不该把整次对话变成「后端没连上」。
     * （踩过：COMMAND_ROUTES 漏登记时 runActions 抛 ReferenceError，
     *   异常被外面 sendAgentMessage 的 catch 吞掉，界面显示成网络故障，
     *   实际后端好得很 —— 这种假象最难查。）
     */
    try {
      if (action.type === 'navigate' && action.path) {
        goTo(action.path)
      } else if (action.type === 'fill' && action.target && action.fields) {
        // 先放草稿、再跳页：
        // 目标页面是挂载时才注册 watch（带 immediate），挂载时正好接住这份草稿
        pendingDraft.value = { target: action.target, fields: action.fields }
        shouldClose = true
        goTo(FILL_TARGET_PAGES[action.target])
      } else if (COMMAND_ROUTES[action.type]) {
        /*
         * 操作类动作（打卡、完成待办、撤销申请……）。
         * 做法和填表完全一样：先放暗号、再跳页 ——
         * 目标页面是挂载时才注册 watch（带 immediate），挂载时正好接住。
         * 为什么不像填表那样直接在这里动手？因为这些操作都依赖页面自己的状态
         * （待办列表、请假记录都在各自页面里），在外面动不了。
         */
        const route = COMMAND_ROUTES[action.type]
        pendingCommand.value = { ...action, target: route.target }
        shouldClose = true
        if (route.page) goTo(route.page)
      }
    } catch (error) {
      // 不往外抛：抛出去会被 sendAgentMessage 的 catch 当成「后端没连上」
      console.error('[aiAgent] 动作执行失败：', action, error)
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
    const title = text
      .replace(/^(帮我|我要|我想|新建|添加|加个|建个)+/, '')
      .trim()
      .slice(0, 40)
    return {
      reply: '【本地兜底】已把标题预填进新建弹窗，确认后保存。',
      actions: [{ type: 'fill', target: 'todo', fields: { title } }],
    }
  }

  // 打卡（后端挂了也能用）
  if (/打卡|签到/.test(text)) {
    return { reply: '【本地兜底】正在帮你打卡。', actions: [{ type: 'checkin' }] }
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
