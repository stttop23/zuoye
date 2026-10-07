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

const categories = ['工作', '活动', '学习', '文档', '其他']
const assignees = ['刘皖', '张晶', '罗欣雨']
const editableStatuses = ['待办', '进行中', '已完成']
const statusFilters = ['全部', ...editableStatuses]
const priorityTagMap = { 高: 'danger', 中: 'warning', 低: 'info' }
const statusTagMap = { 待办: 'info', 进行中: 'warning', 已完成: 'success' }

const todos = ref([
  {
    id: 1,
    title: '整理期末学生工作总结',
    description: '汇总各部门工作成果、存在问题和下学期计划。',
    category: '文档',
    priority: '高',
    assignee: '刘皖',
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
    assignee: '刘皖',
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
  assignee: '张晶',
  dueDate: '',
  status: '待办',
})

const todoForm = reactive(createEmptyForm())

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
  .page-head {
    flex-direction: column;
  }

  .page-head :deep(.el-button) {
    width: 100%;
  }
}
</style>
