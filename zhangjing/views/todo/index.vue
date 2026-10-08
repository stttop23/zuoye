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
import { useUserProfile } from '@/composables/userProfile'
import TodoStats from './components/TodoStats.vue'
import TodoToolbar from './components/TodoToolbar.vue'
import TodoDialog from './components/TodoDialog.vue'

const categories = ['工作', '活动', '学习', '文档', '其他']
const editableStatuses = ['待办', '进行中', '已完成']
const priorityTagMap = { 高: 'danger', 中: 'warning', 低: 'info' }
const statusTagMap = { 待办: 'info', 进行中: 'warning', 已完成: 'success' }

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
  .page-head {
    align-items: flex-start;
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
