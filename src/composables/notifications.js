/**
 * 顶栏通知中心
 * ============
 * 解决的问题：请假被驳回 / 通过了，申请人怎么知道？总不能让老师打电话。
 *
 * ⚠️ 现在通知内容是**假数据**（写在 MOCK_NOTIFICATIONS 里），因为「谁审批、审批结果」
 *    这件事得后端存下来才算数。前端只是把「通知长什么样、怎么看」先做出来。
 *
 * 接后端之后要改三处：
 *   1. 拉列表：GET  /api/notifications
 *   2. 标已读：POST /api/notifications/read
 *   3. 有新通知时推过来（WebSocket，或每 30 秒轮询一次）
 *   4. MOCK_NOTIFICATIONS 整个删掉
 *
 * 给队友留的钩子：想在自己页面里塞一条通知，调 pushNotification() 就行。
 */
import { computed, ref } from 'vue'

/** 已读状态存本地：只存"读过哪些 id"，通知本身还是代码里的，刷新后能对上 */
const READ_KEY = 'student-work-read-notifications'

/** 假的初始通知。id 要唯一，重复点开同一个 id 只会标一次已读 */
const MOCK_NOTIFICATIONS = [
  {
    id: 'leave-202609-1',
    type: 'leave',
    title: '请假申请已通过',
    content: '病假 09-15 ~ 09-16 · 审批人：王老师',
    time: '09-14 09:00',
    path: '/leave',
  },
  {
    id: 'leave-202609-2',
    type: 'leave',
    title: '请假申请被驳回',
    content: '事假 09-05 · 原因：与学生会例会冲突',
    time: '09-03 19:30',
    path: '/leave',
  },
  {
    id: 'notice-202610-1',
    type: 'notice',
    title: '新公告：关于期末学生工作总结的通知',
    content: '发布人：学工处',
    time: '10-02 09:15',
    path: '/notice',
  },
  {
    id: 'todo-202610-1',
    type: 'todo',
    title: '待办已逾期',
    content: '提交团支书工作总结 · 截止 10-10',
    time: '10-11 08:00',
    path: '/todo',
  },
]

function readReadIds() {
  try {
    const raw = localStorage.getItem(READ_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const readIds = ref(readReadIds())

/** 运行时 push 进来的（排在假数据前面，新的在上面） */
const pushedItems = ref([])

/** 通知列表：运行时加的 + 假的 */
export const notifications = computed(() => [...pushedItems.value, ...MOCK_NOTIFICATIONS])

/** 未读数，给小红点用 */
export const unreadCount = computed(
  () => notifications.value.filter((item) => !readIds.value.includes(item.id)).length,
)

export function isNotificationRead(id) {
  return readIds.value.includes(id)
}

export function markNotificationRead(id) {
  if (readIds.value.includes(id)) return
  readIds.value = [...readIds.value, id]
  persist()
}

export function markAllNotificationsRead() {
  readIds.value = notifications.value.map((item) => item.id)
  persist()
}

/**
 * 塞一条新通知。示例：
 *   pushNotification({ type: 'leave', title: '请假申请已提交', content: '等待审批', path: '/leave' })
 */
export function pushNotification({ type = 'info', title, content = '', path = '', time = '' }) {
  pushedItems.value = [
    {
      id: `push-${Date.now()}-${pushedItems.value.length}`,
      type,
      title,
      content,
      path,
      time: time || nowText(),
    },
    ...pushedItems.value,
  ]
}

function nowText() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function persist() {
  try {
    localStorage.setItem(READ_KEY, JSON.stringify(readIds.value))
  } catch {
    /* 存不进去就算了，不影响用 */
  }
}
