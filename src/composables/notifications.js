/**
 * 顶栏通知中心
 * ============
 * 解决的问题：请假被驳回 / 通过了，申请人怎么知道？总不能让老师打电话。
 *
 * ⚠️ 通知内容不是手写死的是从 @/composables/appStore 的实时数据【推】出来的：
 *    请假记录、公告、逾期待办一变，铃铛立刻跟着变（审批完不会没动静）。
 *    只有「谁审批的」这件事得后端存下来才算数，前端先不做。
 *
 * 接后端之后要改三处：
 *   1. 拉列表：GET  /api/notifications
 *   2. 标已读：POST /api/notifications/read
 *   3. 有新通知时推过来（WebSocket，或每 30 秒轮询一次）
 *
 * 给队友留的钩子：想在自己页面里塞一条通知，调 pushNotification() 就行。
 */
import { computed, ref } from 'vue'
import { leaveRecords, notices as allNotices, todos } from '@/composables/appStore'

/** 已读状态存本地：只存"读过哪些 id"，通知本身还是代码里的，刷新后能对上 */
const READ_KEY = 'student-work-read-notifications'

/** 假的初始通知。id 要唯一，重复点开同一个 id 只会标一次已读 */

/** 本地日期，别用 toISOString（它按 UTC 算，会差一天） */
function todayStr() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/**
 * 初始通知：全部从 @/mock 的真实数据【推】出来，不另手写。
 *
 * ⚠️ 以前这里是手写的四条，结果条条和页面对不上：
 *    「病假 09-15 ~ 09-16 已通过 · 审批人：王老师」——“王老师”凭空造出来的，
 *      而且 09-15 那条记录是张晶的，刘皖自己那条还在待审批
 *    「事假 09-05 被驳回 · 原因：与学生会例会冲突」——09-05 那条其实是**年假**，
 *      原因也不是“例会冲突”，是“参加校外竞赛”
 *    「新公告…发布人：学工处」——实际发布人是张晶
 *    「待办已逾期：提交团支书工作总结」——根本没有这条待办，
 *      真正逾期的是「准备学生会周例会材料」
 * 老师把铃铛和请假页/待办页一对，就穿了。
 *
 * 现在由数据推出来，类型、日期、原因、发布人全部照抄，想对不上都难。
 */
function buildInitialNotifications() {
  const items = []

  const LEAVE_TITLE = {
    待审批: '请假申请已提交',
    已通过: '请假申请已通过',
    已驳回: '请假申请被驳回',
  }

  for (const record of leaveRecords.value) {
    const span = `${record.type} ${record.startDate.slice(5)} ~ ${record.endDate.slice(5)}`
    const extra =
      record.status === '已驳回' && record.rejectionReason ? ` · ${record.rejectionReason}` : ''
    items.push({
      /*
       * id 里带上状态：审批把「待审批」改成「已通过」时，id 跟着变，
       * 就成了一条【新】通知，铃铛的红点会重新亮起来。
       * 以前 id 只带记录 id，审批完通知内容变了但 id 没变 →
       * 之前已读过的还是已读，铃铛一点动静都没有。
       */
      id: `leave-${record.id}-${record.status}`,
      type: 'leave',
      title: LEAVE_TITLE[record.status] || '请假状态有更新',
      content: `${record.name} · ${span}${extra}`,
      time: (record.applyTime || '').slice(5),
      path: '/leave',
    })
  }

  // 公告只给置顶的那几条，不然一屏全是公告
  for (const notice of allNotices.value.filter((item) => item.top)) {
    items.push({
      id: `notice-${notice.id}`,
      type: 'notice',
      title: `新公告：${notice.title}`,
      content: `发布人：${notice.author}`,
      time: notice.publishTime.slice(5),
      path: '/notice',
    })
  }

  // 待办：只报已逾期的（过了截止日又还没做完）。
  // 逾期的最多留 2 条 —— 现在有 3 条逾期，全塞进去会把「请假被驳回」那种挤掉，
  // 通知列表本来就该是各种事件混着，不然演示时看着像待办页的复制品。
  const today = todayStr()
  const overdue = todos.value
    .filter((todo) => todo.dueDate < today && todo.status !== '已完成')
    .sort((a, b) => b.dueDate.localeCompare(a.dueDate))
    .slice(0, 2)

  for (const todo of overdue) {
    items.push({
      id: `todo-${todo.id}`,
      type: 'todo',
      title: '待办已逾期',
      content: `${todo.title} · 截止 ${todo.dueDate.slice(5)}`,
      // 逾期这个事件发生在截止日结束的那一刻
      time: `${todo.dueDate.slice(5)} 23:59`,
      path: '/todo',
    })
  }

  // 新的在上面，最多留 8 条
  return items.sort((a, b) => b.time.localeCompare(a.time)).slice(0, 8)
}

const derivedNotifications = computed(() => buildInitialNotifications())

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

/** 通知列表：运行时 push 的 + 从数据推出来的 */
export const notifications = computed(() => [...pushedItems.value, ...derivedNotifications.value])

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
