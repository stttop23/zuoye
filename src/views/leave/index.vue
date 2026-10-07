<template>
  <div class="leave">
    <!-- ==================== 页头 ==================== -->
    <div class="page-head">
      <h2 class="page-title">请假申请</h2>
    </div>

    <!-- ==================== 填写申请 ==================== -->
    <el-card shadow="never" class="section">
      <el-form
        ref="formRef"
        :model="leaveForm"
        :rules="rules"
        label-width="90px"
        class="leave__form"
        @submit.prevent
      >
        <el-form-item label="申请人">
          <el-input v-model="leaveForm.name" disabled />
        </el-form-item>

        <el-form-item label="请假类型" prop="type">
          <el-select v-model="leaveForm.type" placeholder="请选择" style="width: 100%">
            <el-option label="事假" value="事假" />
            <el-option label="病假" value="病假" />
            <el-option label="年假" value="年假" />
          </el-select>
        </el-form-item>

        <el-form-item label="开始时间" prop="startTime">
          <el-date-picker
            v-model="leaveForm.startTime"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="onStartChange"
          />
        </el-form-item>

        <el-form-item label="结束时间" prop="endTime">
          <el-date-picker
            v-model="leaveForm.endTime"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledEndDate"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item v-if="days > 0" label="合计天数">
          <el-tag type="primary" effect="plain">{{ days }} 天</el-tag>
        </el-form-item>

        <el-form-item label="请假原因" prop="reason">
          <el-input
            v-model="leaveForm.reason"
            type="textarea"
            :rows="4"
            maxlength="200"
            show-word-limit
            placeholder="填写请假原因"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="submitForm">
            <el-icon><Check /></el-icon>
            提交申请
          </el-button>
          <el-button @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ==================== 申请记录 ==================== -->
    <el-card shadow="never" class="section">
      <template #header>
        <span class="section__title">申请记录</span>
      </template>

      <el-table :data="records" stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="type" label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.type]" size="small" effect="plain">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="请假时间" width="210" align="center">
          <template #default="{ row }">{{ row.startDate }} 至 {{ row.endDate }}</template>
        </el-table-column>
        <el-table-column prop="days" label="天数" width="80" align="center" />
        <el-table-column prop="reason" label="原因" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status]" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="applyTime" label="提交时间" width="170" align="center" />
        <el-table-column label="操作" width="90" align="center" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === '待审批'" type="danger" link @click="cancelRecord(row)">
              撤销
            </el-button>
            <span v-else class="leave__muted">—</span>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="还没有请假记录" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
/**
 * ⚠️ 说明：本页数据为「假数据」，目的是让前端页面先跑起来。
 * 后端接口就绪后，把 records 换成接口请求、提交改成调接口即可。
 */
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Refresh } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'

const { userName } = useUserProfile()

const typeTagMap = { 事假: 'primary', 病假: 'warning', 年假: 'success' }
const statusTagMap = { 待审批: 'warning', 已通过: 'success', 已驳回: 'danger' }

/** ---------- 表单 ---------- */
const formRef = ref()
const submitting = ref(false)

const createEmptyForm = () => ({
  name: userName.value,
  type: '',
  startTime: '',
  endTime: '',
  reason: '',
})

const leaveForm = reactive(createEmptyForm())

watch(userName, (name) => {
  leaveForm.name = name
})

/** 结束时间不能早于开始时间 */
function validateEndTime(rule, value, callback) {
  if (!value || !leaveForm.startTime) return callback()
  if (value < leaveForm.startTime) {
    callback(new Error('结束时间不能早于开始时间'))
  } else {
    callback()
  }
}

const rules = {
  type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    { validator: validateEndTime, trigger: 'change' },
  ],
  reason: [
    { required: true, message: '请填写请假原因', trigger: 'blur' },
    { min: 5, max: 200, message: '请假原因 5 - 200 个字', trigger: 'blur' },
  ],
}

/** 转成本地日期字符串（YYYY-MM-DD），避免时区把日期算偏 */
function toDateStr(date) {
  const p = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`
}

/** 开始时间往后调时，清掉已经非法的结束时间 */
function onStartChange() {
  if (leaveForm.endTime && leaveForm.endTime < leaveForm.startTime) {
    leaveForm.endTime = ''
  }
  // validateField 校验不通过时会 reject，这里必须接住，否则控制台报未捕获错误
  // 错误提示由表单自己渲染，所以直接忽略即可
  formRef.value?.validateField('endTime').catch(() => {})
}

/** 结束时间选择器里，禁掉开始时间之前的日期 */
function disabledEndDate(date) {
  return leaveForm.startTime ? toDateStr(date) < leaveForm.startTime : false
}

/** 请假天数（含首尾两天） */
const days = computed(() => {
  if (!leaveForm.startTime || !leaveForm.endTime) return 0
  const diff = new Date(leaveForm.endTime) - new Date(leaveForm.startTime)
  return diff < 0 ? 0 : diff / 86400000 + 1
})

function formatNow() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${toDateStr(d)} ${p(d.getHours())}:${p(d.getMinutes())}`
}

async function submitForm() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  // 模拟网络请求，让 loading 有效果（答辩演示更好看）
  setTimeout(() => {
    records.value.unshift({
      id: Date.now(),
      type: leaveForm.type,
      startDate: leaveForm.startTime,
      endDate: leaveForm.endTime,
      days: days.value,
      reason: leaveForm.reason,
      status: '待审批',
      applyTime: formatNow(),
    })
    submitting.value = false
    resetForm()
    ElMessage.success('提交成功，等待审批')
  }, 400)
}

function resetForm() {
  formRef.value?.resetFields()
  Object.assign(leaveForm, createEmptyForm())
}

/** ---------- 假数据：申请记录 ---------- */
const records = ref([
  {
    id: 3,
    type: '事假',
    startDate: '2026-09-28',
    endDate: '2026-09-28',
    days: 1,
    reason: '家中有事，需要回家处理',
    status: '已通过',
    applyTime: '2026-09-26 20:12',
  },
  {
    id: 2,
    type: '病假',
    startDate: '2026-09-15',
    endDate: '2026-09-16',
    days: 2,
    reason: '感冒发烧，校医院建议休息两天',
    status: '已通过',
    applyTime: '2026-09-14 08:30',
  },
  {
    id: 1,
    type: '年假',
    startDate: '2026-09-05',
    endDate: '2026-09-05',
    days: 1,
    reason: '参加校外竞赛，需要请假一天',
    status: '已驳回',
    applyTime: '2026-09-03 19:05',
  },
])

/** ---------- 撤销 ---------- */
async function cancelRecord(row) {
  try {
    await ElMessageBox.confirm(`确定撤销这条「${row.type}」申请吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  records.value = records.value.filter((item) => item.id !== row.id)
  ElMessage.success('已撤销')
}
</script>

<style scoped>
.leave {
  display: flex;
  flex-direction: column;
  gap: var(--st-gap-base);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.section {
  border: none;
}

.section__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.leave__form {
  max-width: 560px;
}

.leave__muted {
  color: var(--st-text-placeholder);
}
</style>
