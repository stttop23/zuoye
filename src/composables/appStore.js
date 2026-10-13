/**
 * 全站业务数据的唯一源头（+ 本地持久化）
 * =====================================
 * 这里解决两个同源的问题，都和「一份数据有几个副本」有关：
 *
 *   1) 同一个东西散在好几处
 *      以前：`src/mock/index.js` 写一份，`zhangjing/views/todo/index.vue` 内联一份，
 *      `luoxinyu/views/leave/index.vue` 内联一份，后端 `server/mock_data.py` 还手抄一份。
 *      改一处忘一处，首页数字、页面表格、AI 说的话就互相打架 ——
 *      数字对不上比缺功能更丢人。
 *      → 现在 todos / notices / leaveRecords 只在这里一份，页面 import 着用。
 *
 *   2) 业务数据只保存在浏览器
 *      SQLite 后端现为权威数据源，本地存档只用于后端暂时不可用时展示缓存。
 */
import { ElMessage } from 'element-plus'
import { ref, watch, nextTick } from 'vue'
import { LEAVE_RECORDS, MEMBERS, NOTICES, TODOS } from '@/mock'
import { getWorkspaceSnapshot, saveWorkspaceSnapshot } from '@/api/workspace'

const DATA_KEY = 'student-work-data'
const CHECKIN_KEY = 'student-work-checkin'

/** 深拷贝一份，免得改动污染 `@/mock` 里的原始种子数据 */
function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function readData() {
  try {
    const raw = localStorage.getItem(DATA_KEY)
    const parsed = raw ? JSON.parse(raw) : null
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

/** 存档只在「确实是个数组」时才用，格式坏了就退回种子，别把页面搞崩 */
function pick(saved, key, seed) {
  return Array.isArray(saved[key]) ? saved[key] : clone(seed)
}

const saved = readData()

/** ---------- 待办 ---------- */
export const todos = ref(pick(saved, 'todos', TODOS))

/** ---------- 公告 ---------- */
export const notices = ref(pick(saved, 'notices', NOTICES))

/** ---------- 请假记录 ---------- */
export const leaveRecords = ref(pick(saved, 'leaveRecords', LEAVE_RECORDS))
export const databaseConnected = ref(false)

/** ---------- 打卡 ---------- */
function readCheckin() {
  const empty = { lastDate: '', lastTime: '', streak: 0, place: null }
  try {
    const raw = localStorage.getItem(CHECKIN_KEY)
    return raw ? { ...empty, ...JSON.parse(raw) } : empty
  } catch {
    return empty
  }
}

export const checkin = ref(readCheckin())

/* ------------------------------------------------------------------
 * 持久化：下面几个 ref 一变就写盘。
 * deep 是必须的 —— 页面里大多是 `todo.status = '已完成'` 这种改字段的写法，
 * 不 deep 的话监听不到。
 * ------------------------------------------------------------------ */
let skipNextStoreSync = false
let syncTimer
let saveQueue = Promise.resolve()

watch(
  [todos, notices, leaveRecords],
  () => {
    try {
      localStorage.setItem(
        DATA_KEY,
        JSON.stringify({
          todos: todos.value,
          notices: notices.value,
          leaveRecords: leaveRecords.value,
        }),
      )
    } catch {
      // 浏览器禁用本地存储也不影响这一次使用
    }

    if (!databaseConnected.value || skipNextStoreSync) return
    clearTimeout(syncTimer)
    syncTimer = setTimeout(() => {
      const snapshot = {
        todos: clone(todos.value),
        notices: clone(notices.value),
        leaveRecords: clone(leaveRecords.value),
      }
      saveQueue = saveQueue
        .then(() => saveWorkspaceSnapshot(snapshot))
        .catch((error) => {
          databaseConnected.value = false
          console.error('SQLite 同步失败', error)
          ElMessage.error(`数据库同步失败：${error.message}。刷新页面可重新连接。`)
        })
    }, 300)
  },
  { deep: true },
)

export async function initializeWorkspace() {
  const { data, initialized } = await getWorkspaceSnapshot()
  if (
    !data ||
    !Array.isArray(data.todos) ||
    !Array.isArray(data.notices) ||
    !Array.isArray(data.leaveRecords)
  ) {
    throw new Error('数据库返回的数据格式无效')
  }

  const hasLocalSnapshot = ['todos', 'notices', 'leaveRecords'].every((key) =>
    Array.isArray(saved[key]),
  )
  const initialData =
    !initialized && hasLocalSnapshot
      ? {
          todos: saved.todos,
          notices: saved.notices,
          leaveRecords: saved.leaveRecords,
        }
      : data
  if (!initialized) await saveWorkspaceSnapshot(initialData)

  skipNextStoreSync = true
  todos.value = initialData.todos
  notices.value = initialData.notices
  leaveRecords.value = initialData.leaveRecords
  await nextTick()
  skipNextStoreSync = false
  databaseConnected.value = true
}

watch(
  checkin,
  (value) => {
    try {
      localStorage.setItem(CHECKIN_KEY, JSON.stringify(value))
    } catch {
      // 同上
    }
  },
  { deep: true },
)

/* ------------------------------------------------------------------
 * 从同一份数据里【数】出来的派生值。
 * 首页那四个数字、最新公告都从这里拿 —— 想对不上都不可能。
 * ------------------------------------------------------------------ */
export function dashboardSummary() {
  return {
    todo: todos.value.length,
    leave: leaveRecords.value.length,
    notice: notices.value.length,
    member: MEMBERS.length,
  }
}

/** 最新公告：置顶优先，然后按 id 从大到小（和公告页排法一致） */
export function latestNotices(limit = 3) {
  return [...notices.value]
    .sort((a, b) => Number(b.top) - Number(a.top) || b.id - a.id)
    .slice(0, limit)
}

/** 给新公告 / 新记录算一个不重复的 id */
export function nextId(list) {
  return list.reduce((max, item) => Math.max(max, Number(item.id) || 0), 0) + 1
}

/** 全部恢复成初始假数据（演示想重来一遍时用） */
export function resetDemoData() {
  todos.value = clone(TODOS)
  notices.value = clone(NOTICES)
  leaveRecords.value = clone(LEAVE_RECORDS)
  checkin.value = { lastDate: '', lastTime: '', streak: 0, place: null }
}

/**
 * 交给 AI 助手看的「现场快照」。
 *
 * 为什么需要它：AI 的只读工具（「我有哪些待办」「我的请假批了吗」）
 * 以前读的是后端 `server/mock_data.py` 里手抄的一份，而你在页面上新填的东西
 * 那边根本不知道 —— 于是 AI 会一本正经地告诉你一条你已经做完的待办「还是待办」。
 *
 * 现在每次发消息都把这份快照一起带上，后端优先用快照，读到的永远是你眼前这一份。
 * 打比方：以前是让保安看一段录像回放，现在是让他看监控现场。
 */
export function agentSnapshot() {
  return {
    todos: clone(todos.value),
    notices: clone(notices.value),
    leaveRecords: clone(leaveRecords.value),
    checkin: clone(checkin.value),
  }
}
