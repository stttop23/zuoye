<template>
  <div class="todo-page">
    <header class="page-head">
      <div>
        <h2 class="page-title">待办事项</h2>
        <p class="page-desc">统一安排、跟进和完成学生工作任务</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建待办
      </el-button>
    </header>

    <!-- ==================== 统计条（子组件） ==================== -->
    <TodoStats :stats="stats" />

    <el-card shadow="never" class="section calendar-section">
      <div class="calendar-layout">
        <div class="calendar">
          <header class="calendar-header">
            <div>
              <h3 class="calendar-title">日程日历</h3>
              <p class="calendar-caption">点击日期查看当天安排</p>
            </div>
            <div class="calendar-controls">
              <el-button circle aria-label="上个月" @click="changeCalendarMonth(-1)">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <strong class="calendar-month">{{ calendarMonthLabel }}</strong>
              <el-button circle aria-label="下个月" @click="changeCalendarMonth(1)">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
              <el-button class="today-button" @click="goToToday">今天</el-button>
            </div>
          </header>

          <div class="calendar-grid" role="grid" aria-label="月历">
            <div v-for="weekday in weekdays" :key="weekday" class="calendar-weekday" role="columnheader">
              {{ weekday }}
            </div>
            <button
              v-for="day in calendarDays"
              :key="day.dateKey"
              type="button"
              :class="[
                'calendar-day',
                {
                  'calendar-day--outside': !day.inCurrentMonth,
                  'calendar-day--selected': day.dateKey === selectedCalendarDate,
                  'calendar-day--today': day.isToday,
                },
              ]"
              :aria-label="`${day.dateKey}，${day.todos.length} 项安排`"
              :aria-pressed="day.dateKey === selectedCalendarDate"
              role="gridcell"
              @click="selectCalendarDate(day)"
            >
              <span class="calendar-day__number">{{ day.day }}</span>
              <span v-if="day.todos.length" class="calendar-day__events">
                <i
                  v-for="todo in day.todos.slice(0, 3)"
                  :key="todo.id"
                  :class="['calendar-dot', `calendar-dot--${todo.status === '已完成' ? 'done' : todo.status === '进行中' ? 'active' : 'pending'}`]"
                />
                <small v-if="day.todos.length > 3">+{{ day.todos.length - 3 }}</small>
              </span>
            </button>
          </div>
          <div class="calendar-legend" aria-label="日程状态图例">
            <span><i class="calendar-dot calendar-dot--pending" />待办</span>
            <span><i class="calendar-dot calendar-dot--active" />进行中</span>
            <span><i class="calendar-dot calendar-dot--done" />已完成</span>
          </div>
        </div>

        <aside class="day-schedule">
          <div class="day-schedule__header">
            <div>
              <h3 class="day-schedule__title">{{ selectedDateLabel }}</h3>
              <p class="day-schedule__count">
                {{ selectedDayTodos.length ? `共 ${selectedDayTodos.length} 项安排` : '暂无安排' }}
              </p>
            </div>
            <el-button
              circle
              type="primary"
              plain
              aria-label="为所选日期新建待办"
              @click="openCreateForSelectedDate"
            >
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>

          <div v-if="selectedDayTodos.length" class="schedule-list">
            <button
              v-for="todo in selectedDayTodos"
              :key="todo.id"
              type="button"
              class="schedule-item"
              @click="openEdit(todo)"
            >
              <span :class="['schedule-item__marker', `schedule-item__marker--${todo.status === '已完成' ? 'done' : todo.status === '进行中' ? 'active' : 'pending'}`]" />
              <span class="schedule-item__content">
                <strong :class="{ 'schedule-item__title--done': todo.status === '已完成' }">
                  {{ todo.title }}
                </strong>
                <small>{{ todo.category }} · {{ todo.assignee }}</small>
                <span v-if="todo.description" class="schedule-item__description">
                  {{ todo.description }}
                </span>
              </span>
              <el-tag :type="statusTagMap[todo.status]" size="small">{{ todo.status }}</el-tag>
            </button>
          </div>
          <el-empty v-else :image-size="64" description="这一天还没有安排">
            <el-button type="primary" link @click="openCreateForSelectedDate">添加当天待办</el-button>
          </el-empty>
        </aside>
      </div>
    </el-card>

    <el-card shadow="never" class="section">
      <!-- ==================== 筛选栏（子组件） ==================== -->
      <TodoToolbar
        v-model:keyword="keyword"
        v-model:statusFilter="statusFilter"
        v-model:priorityFilter="priorityFilter"
        v-model:categoryFilter="categoryFilter"
        :categories="categories"
      />

      <el-table :data="pagedTodos" stripe style="width: 100%">
        <el-table-column label="任务" min-width="250">
          <template #default="{ row }">
            <div :class="['task-title', { 'task-title--done': row.status === '已完成' }]">
              {{ row.title }}
            </div>
            <div v-if="row.description" class="task-description">
              {{ row.description }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100" align="center" />
        <el-table-column label="优先级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="priorityTagMap[row.priority]" size="small" effect="plain">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="负责人" width="100" align="center" />
        <el-table-column label="截止日期" width="130" align="center">
          <template #default="{ row }">
            <span :class="{ 'due-date--late': isOverdue(row) }">{{ row.dueDate }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status]" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="190" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status !== '已完成'"
              type="success"
              link
              @click="toggleComplete(row)"
            >
              完成
            </el-button>
            <el-button v-else type="info" link @click="toggleComplete(row)">
              重新打开
            </el-button>
            <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="deleteTodo(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="没有符合条件的待办事项" />
        </template>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
          :total="filteredTodos.length"
          layout="total, sizes, prev, pager, next"
          background
        />
      </div>
    </el-card>

    <!-- ==================== 新建 / 编辑弹窗（子组件） ==================== -->
    <TodoDialog
      v-model="dialogVisible"
      :mode="dialogMode"
      :categories="categories"
      :assignees="assignees"
      :editable-statuses="editableStatuses"
      :initial="dialogInitial"
      @save="onSave"
    />
  </div>
</template>

<script setup>
/**
 * ⚠️ 说明：本页数据为「假数据」，目的是让前端页面先跑起来。
 * 后端接口就绪后，把 todos 换成接口请求即可。
 * 分页是前端分页（先过滤再切片），数据量大时要改成后端分页。
 *
 * 本页已拆成三个子组件，都在 ./components/ 下：
 * TodoStats（统计条）、TodoToolbar（筛选栏）、TodoDialog（新建/编辑弹窗）
 */
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import TodoStats from './components/TodoStats.vue'
import TodoToolbar from './components/TodoToolbar.vue'
import TodoDialog from './components/TodoDialog.vue'

const categories = ['工作', '活动', '学习', '文档', '其他']
const editableStatuses = ['待办', '进行中', '已完成']
const priorityTagMap = { 高: 'danger', 中: 'warning', 低: 'info' }
const statusTagMap = { 待办: 'info', 进行中: 'warning', 已完成: 'success' }
const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const today = new Date()
const calendarMonth = ref(new Date(today.getFullYear(), today.getMonth(), 1))
const selectedCalendarDate = ref(toDateKey(today))

const { userName } = useUserProfile()

// 负责人下拉：当前的显示名称 + 其他组员，去重
const assignees = computed(() => [...new Set([userName.value, '张晶', '罗欣雨'])])

const todos = ref([
  {
    id: 1,
    title: '整理期末学生工作总结',
    description: '汇总各部门工作成果、存在问题和下学期计划。',
    category: '文档',
    priority: '高',
    assignee: userName.value,
    dueDate: '2026-10-15',
    status: '待办',
  },
  {
    id: 2,
    title: '核对校园文化活动报名名单',
    description: '确认各班级报名信息并反馈缺漏。',
    category: '活动',
    priority: '高',
    assignee: '张晶',
    dueDate: '2026-10-10',
    status: '进行中',
  },
  {
    id: 3,
    title: '更新国庆假期值班安排',
    description: '核对值班人员和联系方式。',
    category: '工作',
    priority: '中',
    assignee: '罗欣雨',
    dueDate: '2026-10-08',
    status: '待办',
  },
  {
    id: 4,
    title: '汇总志愿服务时长',
    description: '整理本月志愿服务签到记录。',
    category: '文档',
    priority: '低',
    assignee: '张晶',
    dueDate: '2026-10-05',
    status: '已完成',
  },
  {
    id: 5,
    title: '准备学生会周例会材料',
    description: '收集本周各部门进展，整理议题。',
    category: '工作',
    priority: '中',
    assignee: userName.value,
    dueDate: '2026-10-09',
    status: '进行中',
  },
  {
    id: 6,
    title: '完成新学期活动复盘',
    description: '归档活动照片、预算和反馈问卷。',
    category: '活动',
    priority: '低',
    assignee: '罗欣雨',
    dueDate: '2026-10-20',
    status: '待办',
  },
])

/** ---------- 筛选 + 分页 ---------- */
const keyword = ref('')
const statusFilter = ref('全部')
const priorityFilter = ref('')
const categoryFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(5)

const stats = computed(() => ({
  total: todos.value.length,
  pending: todos.value.filter((item) => item.status === '待办').length,
  ongoing: todos.value.filter((item) => item.status === '进行中').length,
  completed: todos.value.filter((item) => item.status === '已完成').length,
}))

const calendarMonthLabel = computed(() =>
  calendarMonth.value.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' }),
)

const calendarDays = computed(() => {
  const year = calendarMonth.value.getFullYear()
  const month = calendarMonth.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const offset = (firstDay.getDay() + 6) % 7
  const dayCount = new Date(year, month + 1, 0).getDate()
  const cellCount = Math.ceil((offset + dayCount) / 7) * 7
  const todayKey = toDateKey(new Date())

  return Array.from({ length: cellCount }, (_, index) => {
    const date = new Date(year, month, index - offset + 1)
    const dateKey = toDateKey(date)
    return {
      date,
      dateKey,
      day: date.getDate(),
      inCurrentMonth: date.getMonth() === month,
      isToday: dateKey === todayKey,
      todos: todos.value.filter((todo) => todo.dueDate === dateKey),
    }
  })
})

const selectedDayTodos = computed(() =>
  todos.value.filter((todo) => todo.dueDate === selectedCalendarDate.value),
)

const selectedDateLabel = computed(() => {
  const date = parseDateKey(selectedCalendarDate.value)
  return date.toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })
})

const filteredTodos = computed(() => {
  const search = keyword.value.trim().toLocaleLowerCase()
  return todos.value.filter((item) => {
    const matchesKeyword =
      !search ||
      [item.title, item.description, item.assignee, item.category]
        .join(' ')
        .toLocaleLowerCase()
        .includes(search)
    const matchesStatus = statusFilter.value === '全部' || item.status === statusFilter.value
    const matchesPriority = !priorityFilter.value || item.priority === priorityFilter.value
    const matchesCategory = !categoryFilter.value || item.category === categoryFilter.value
    return matchesKeyword && matchesStatus && matchesPriority && matchesCategory
  })
})

const pagedTodos = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTodos.value.slice(start, start + pageSize.value)
})

watch([keyword, statusFilter, priorityFilter, categoryFilter], () => {
  currentPage.value = 1
})

// 顶栏改了显示名称后，把原本挂在自己名下的任务一起改过来
watch(userName, (name, previousName) => {
  todos.value.forEach((todo) => {
    if (todo.assignee === previousName) todo.assignee = name
  })
})

function isOverdue(todo) {
  return todo.status !== '已完成' && todo.dueDate < new Date().toLocaleDateString('en-CA')
}

function toDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseDateKey(dateKey) {
  const [year, month, day] = dateKey.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function selectCalendarDate(day) {
  selectedCalendarDate.value = day.dateKey
  if (!day.inCurrentMonth) {
    calendarMonth.value = new Date(day.date.getFullYear(), day.date.getMonth(), 1)
  }
}

function changeCalendarMonth(offset) {
  const selected = parseDateKey(selectedCalendarDate.value)
  const nextMonth = new Date(calendarMonth.value.getFullYear(), calendarMonth.value.getMonth() + offset, 1)
  const lastDay = new Date(nextMonth.getFullYear(), nextMonth.getMonth() + 1, 0).getDate()
  calendarMonth.value = nextMonth
  selectedCalendarDate.value = toDateKey(
    new Date(nextMonth.getFullYear(), nextMonth.getMonth(), Math.min(selected.getDate(), lastDay)),
  )
}

function goToToday() {
  const now = new Date()
  calendarMonth.value = new Date(now.getFullYear(), now.getMonth(), 1)
  selectedCalendarDate.value = toDateKey(now)
}

function openCreateForSelectedDate() {
  openCreate()
  dialogInitial.value = { dueDate: selectedCalendarDate.value }
}

/** ---------- 新建 / 编辑 ---------- */
const dialogVisible = ref(false)
const dialogMode = ref('create')
const dialogInitial = ref(null)
const editingId = ref(null)

function openCreate() {
  dialogMode.value = 'create'
  editingId.value = null
  dialogInitial.value = null
  dialogVisible.value = true
}

function openEdit(todo) {
  dialogMode.value = 'edit'
  editingId.value = todo.id
  dialogInitial.value = { ...todo }
  dialogVisible.value = true
}

/** 弹窗校验通过后抛上来，这里只负责写进列表 */
function onSave(payload) {
  if (dialogMode.value === 'edit') {
    const index = todos.value.findIndex((item) => item.id === editingId.value)
    if (index !== -1) todos.value[index] = { ...todos.value[index], ...payload }
    ElMessage.success('待办已更新')
  } else {
    todos.value.unshift({ id: Date.now(), ...payload })
    ElMessage.success('待办已创建')
  }
  selectedCalendarDate.value = payload.dueDate
  const dueDate = parseDateKey(payload.dueDate)
  calendarMonth.value = new Date(dueDate.getFullYear(), dueDate.getMonth(), 1)
  currentPage.value = 1
}

function toggleComplete(todo) {
  todo.status = todo.status === '已完成' ? '待办' : '已完成'
  ElMessage.success(todo.status === '已完成' ? '任务已完成' : '任务已重新打开')
}

async function deleteTodo(todo) {
  try {
    await ElMessageBox.confirm(`确定删除「${todo.title}」吗？`, '删除待办', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  todos.value = todos.value.filter((item) => item.id !== todo.id)
  ElMessage.success('待办已删除')
}
</script>

<style scoped>
.todo-page {
  display: flex;
  flex-direction: column;
  gap: var(--st-gap-base);
  min-width: 0;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--st-gap-base);
}

.page-title {
  margin: 0;
  color: var(--st-text-primary);
  font-size: 20px;
  font-weight: 600;
}

.page-desc {
  margin: 6px 0 0;
  color: var(--st-text-secondary);
  font-size: 13px;
}

.section {
  border: none;
}

.calendar-section {
  overflow: hidden;
}

.calendar-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.9fr);
  gap: 28px;
}

.calendar {
  min-width: 0;
}

.calendar-header,
.calendar-controls,
.day-schedule__header {
  display: flex;
  align-items: center;
}

.calendar-header,
.day-schedule__header {
  justify-content: space-between;
  gap: var(--st-gap-base);
}

.calendar-title,
.day-schedule__title {
  margin: 0;
  color: var(--st-text-primary);
  font-size: 16px;
  font-weight: 600;
}

.calendar-caption,
.day-schedule__count {
  margin: 5px 0 0;
  color: var(--st-text-secondary);
  font-size: 12px;
}

.calendar-controls {
  gap: 8px;
}

.calendar-month {
  min-width: 92px;
  color: var(--st-text-primary);
  text-align: center;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  margin-top: 20px;
  border-top: 1px solid var(--st-border-color-light);
  border-left: 1px solid var(--st-border-color-light);
}

.calendar-weekday {
  padding: 10px 0;
  color: var(--st-text-secondary);
  font-size: 12px;
  text-align: center;
}

.calendar-day {
  display: flex;
  min-width: 0;
  min-height: 68px;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 8px 3px;
  border: 0;
  border-right: 1px solid var(--st-border-color-light);
  border-bottom: 1px solid var(--st-border-color-light);
  background: var(--st-bg-card);
  color: var(--st-text-primary);
  cursor: pointer;
  font: inherit;
  transition: background-color 0.15s ease;
}

.calendar-day:hover {
  background: var(--st-primary-light);
}

.calendar-day--outside {
  color: var(--st-text-placeholder);
  background: var(--st-bg-page);
}

.calendar-day--selected,
.calendar-day--selected:hover {
  background: var(--st-primary-light);
}

.calendar-day--selected .calendar-day__number {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border-radius: 50%;
  background: var(--st-primary);
  color: var(--st-bg-card);
}

.calendar-day--today:not(.calendar-day--selected) .calendar-day__number {
  color: var(--st-primary);
  font-weight: 700;
}

.calendar-day__number {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border-radius: 50%;
  font-size: 13px;
}

.calendar-day__events {
  display: flex;
  min-height: 8px;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.calendar-day__events small {
  color: var(--st-text-secondary);
  font-size: 10px;
}

.calendar-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
}

.calendar-dot--pending,
.schedule-item__marker--pending {
  background: var(--st-info);
}

.calendar-dot--active,
.schedule-item__marker--active {
  background: var(--st-warning);
}

.calendar-dot--done,
.schedule-item__marker--done {
  background: var(--st-success);
}

.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding-top: 14px;
  color: var(--st-text-secondary);
  font-size: 12px;
}

.calendar-legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.day-schedule {
  min-width: 0;
  padding: 18px;
  border-radius: var(--st-radius-base);
  background: var(--st-bg-page);
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 18px;
}

.schedule-item {
  display: flex;
  width: 100%;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--st-border-color-light);
  border-radius: var(--st-radius-base);
  background: var(--st-bg-card);
  cursor: pointer;
  text-align: left;
}

.schedule-item:hover {
  border-color: var(--st-primary);
}

.schedule-item__marker {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  margin-top: 6px;
  border-radius: 50%;
}

.schedule-item__content {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 5px;
}

.schedule-item__content strong {
  overflow: hidden;
  color: var(--st-text-primary);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-item__content .schedule-item__title--done {
  color: var(--st-text-secondary);
  text-decoration: line-through;
}

.schedule-item__content small,
.schedule-item__description {
  color: var(--st-text-secondary);
  font-size: 11px;
  line-height: 1.5;
}

.schedule-item__description {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.day-schedule :deep(.el-empty) {
  padding: 28px 0 12px;
}

.filter-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: var(--st-gap-base);
}

.search-input {
  width: min(320px, 100%);
}

.filter-select {
  width: 150px;
}

.status-tabs {
  margin-bottom: var(--st-gap-base);
}
.task-title {
  color: var(--st-text-primary);
  font-weight: 600;
}

.task-title--done {
  color: var(--st-text-secondary);
  text-decoration: line-through;
}

.task-description {
  overflow: hidden;
  margin-top: 4px;
  color: var(--st-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.due-date--late {
  color: var(--st-danger);
}

.pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: var(--st-gap-base);
}

/* 统计条、筛选栏、弹窗的样式已随子组件移走，见 ./components/ */

@media (max-width: 760px) {
  .calendar-layout {
    grid-template-columns: minmax(0, 1fr);
    gap: 22px;
  }

  .day-schedule {
    padding: 14px;
  }

  .page-head {
    align-items: flex-start;
  }

  .pagination {
    justify-content: center;
  }
}

@media (max-width: 460px) {
  .calendar-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .calendar-controls {
    width: 100%;
    justify-content: space-between;
  }

  .calendar-day {
    min-height: 56px;
    padding: 5px 2px;
  }

  .calendar-day__events {
    gap: 2px;
  }

  .page-head {
    flex-direction: column;
  }

  .page-head :deep(.el-button) {
    width: 100%;
  }
}
</style>
