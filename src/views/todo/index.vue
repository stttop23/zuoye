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

    <section class="summary-grid" aria-label="待办统计">
      <div class="summary-item">
        <span class="summary-label">全部事项</span>
        <strong class="summary-value">{{ stats.total }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">待办</span>
        <strong class="summary-value summary-value--info">{{ stats.pending }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">进行中</span>
        <strong class="summary-value summary-value--warning">{{ stats.ongoing }}</strong>
      </div>
      <div class="summary-item">
        <span class="summary-label">已完成</span>
        <strong class="summary-value summary-value--success">{{ stats.completed }}</strong>
      </div>
    </section>

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
      <div class="filter-toolbar">
        <el-input
          v-model="keyword"
          clearable
          placeholder="搜索任务、负责人或描述"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="priorityFilter" clearable placeholder="全部优先级" class="filter-select">
          <el-option label="高优先级" value="高" />
          <el-option label="中优先级" value="中" />
          <el-option label="低优先级" value="低" />
        </el-select>
        <el-select v-model="categoryFilter" clearable placeholder="全部分类" class="filter-select">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </div>

      <el-radio-group v-model="statusFilter" class="status-tabs">
        <el-radio-button v-for="item in statusFilters" :key="item" :value="item">
          {{ item }}
        </el-radio-button>
      </el-radio-group>

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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建待办' : '编辑待办'"
      width="520px"
      class="todo-dialog"
      @closed="clearForm"
    >
      <el-form ref="formRef" :model="todoForm" :rules="rules" label-width="84px">
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="todoForm.title" maxlength="40" show-word-limit placeholder="填写任务名称" />
        </el-form-item>
        <el-form-item label="任务描述" prop="description">
          <el-input
            v-model="todoForm.description"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="补充任务说明"
          />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="todoForm.category" placeholder="选择分类" class="full-width">
            <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="todoForm.priority" placeholder="选择优先级" class="full-width">
            <el-option label="高" value="高" />
            <el-option label="中" value="中" />
            <el-option label="低" value="低" />
          </el-select>
        </el-form-item>
        <el-form-item label="负责人" prop="assignee">
          <el-select v-model="todoForm.assignee" placeholder="选择负责人" class="full-width">
            <el-option v-for="item in assignees" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="截止日期" prop="dueDate">
          <el-date-picker
            v-model="todoForm.dueDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择截止日期"
            class="full-width"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="todoForm.status" class="full-width">
            <el-option v-for="item in editableStatuses" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTodo">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Plus } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'

const categories = ['工作', '活动', '学习', '文档', '其他']
const { userName } = useUserProfile()
const assignees = computed(() => [...new Set([userName.value, '张晶', '罗欣雨'])])
const editableStatuses = ['待办', '进行中', '已完成']
const statusFilters = ['全部', ...editableStatuses]
const priorityTagMap = { 高: 'danger', 中: 'warning', 低: 'info' }
const statusTagMap = { 待办: 'info', 进行中: 'warning', 已完成: 'success' }
const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const today = new Date()
const calendarMonth = ref(new Date(today.getFullYear(), today.getMonth(), 1))
const selectedCalendarDate = ref(toDateKey(today))

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

const keyword = ref('')
const statusFilter = ref('全部')
const priorityFilter = ref('')
const categoryFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(5)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const saving = ref(false)
const formRef = ref()
const editingId = ref(null)

const createEmptyForm = () => ({
  title: '',
  description: '',
  category: '',
  priority: '中',
  assignee: userName.value,
  dueDate: '',
  status: '待办',
})

const todoForm = reactive(createEmptyForm())

watch(userName, (name, previousName) => {
  todos.value.forEach((todo) => {
    if (todo.assignee === previousName) todo.assignee = name
  })
  if (todoForm.assignee === previousName) todoForm.assignee = name
})

const rules = {
  title: [
    { required: true, message: '请填写任务名称', trigger: 'blur' },
    { min: 2, max: 40, message: '任务名称需为 2 到 40 个字', trigger: 'blur' },
  ],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  assignee: [{ required: true, message: '请选择负责人', trigger: 'change' }],
  dueDate: [{ required: true, message: '请选择截止日期', trigger: 'change' }],
}

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
  todoForm.dueDate = selectedCalendarDate.value
}

function openCreate() {
  dialogMode.value = 'create'
  editingId.value = null
  Object.assign(todoForm, createEmptyForm())
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

function openEdit(todo) {
  dialogMode.value = 'edit'
  editingId.value = todo.id
  Object.assign(todoForm, { ...todo })
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

function clearForm() {
  formRef.value?.clearValidate()
  Object.assign(todoForm, createEmptyForm())
}

async function saveTodo() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  const savedTodo = { ...todoForm }
  if (dialogMode.value === 'edit') {
    const index = todos.value.findIndex((item) => item.id === editingId.value)
    if (index !== -1) todos.value[index] = { ...todos.value[index], ...savedTodo }
    ElMessage.success('待办已更新')
  } else {
    todos.value.unshift({ id: Date.now(), ...savedTodo })
    ElMessage.success('待办已创建')
  }
  selectedCalendarDate.value = savedTodo.dueDate
  const dueDate = parseDateKey(savedTodo.dueDate)
  calendarMonth.value = new Date(dueDate.getFullYear(), dueDate.getMonth(), 1)
  saving.value = false
  dialogVisible.value = false
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--st-gap-base);
}

.summary-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  padding: 0 var(--st-gap-base);
  border: 1px solid var(--st-border-color-light);
  border-radius: var(--st-radius-base);
  background: var(--st-bg-card);
}

.summary-label {
  color: var(--st-text-secondary);
  font-size: 14px;
}

.summary-value {
  color: var(--st-text-primary);
  font-size: 24px;
  line-height: 1;
}

.summary-value--info {
  color: var(--st-info);
}

.summary-value--warning {
  color: var(--st-warning);
}

.summary-value--success {
  color: var(--st-success);
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

.full-width {
  width: 100%;
}

.todo-dialog {
  max-width: 92vw;
}

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

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--st-gap-sm);
  }

  .summary-item {
    min-height: 64px;
    padding: 0 12px;
  }

  .search-input,
  .filter-select {
    width: 100%;
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
