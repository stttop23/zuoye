<template>
  <div class="leave">
    <!-- ==================== 页头 ==================== -->
    <div class="page-head">
      <div>
        <h2 class="page-title">{{ isAdmin ? '请假审批' : '请假申请' }}</h2>
        <p class="page-desc">
          {{ isAdmin ? '查看所有学生的请假申请，并进行审批' : '提交请假申请，并查看自己的申请记录' }}
        </p>
      </div>
    </div>

    <!-- ==================== 填写申请（子组件） ==================== -->
    <LeaveForm v-if="!isAdmin" @submit="onSubmit" />

    <!-- ==================== 申请记录（子组件） ==================== -->
    <LeaveRecords
      :key="isAdmin ? 'admin-leave-records' : 'student-leave-records'"
      :records="records"
      :is-admin="isAdmin"
      @cancel="cancelRecord"
      @review="reviewRecord"
    />
  </div>
</template>

<script setup>
/**
 * ⚠️ 说明：本页数据为「假数据」，目的是让前端页面先跑起来。
 * 后端接口就绪后，把 records 换成接口请求、提交改成调接口即可。
 *
 * 本页已拆成两个子组件，都在 ./components/ 下：
 * LeaveForm（申请表单，自带校验）、LeaveRecords（申请记录表格）
 */
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserProfile } from '@/composables/userProfile'
import LeaveForm from './components/LeaveForm.vue'
import LeaveRecords from './components/LeaveRecords.vue'

const { userName, isAdmin } = useUserProfile()

/** 转成本地日期字符串（YYYY-MM-DD），避免时区把日期算偏 */
function toDateStr(date) {
  const p = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`
}

function formatNow() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${toDateStr(d)} ${p(d.getHours())}:${p(d.getMinutes())}`
}

/** ---------- 假数据：申请记录 ---------- */
const allRecords = ref([
  {
    id: 3,
    name: '刘皖',
    type: '事假',
    startDate: '2026-09-28',
    endDate: '2026-09-28',
    days: 1,
    reason: '家中有事，需要回家处理',
    status: '待审批',
    applyTime: '2026-09-26 20:12',
  },
  {
    id: 2,
    name: '张晶',
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
    name: '罗欣雨',
    type: '年假',
    startDate: '2026-09-05',
    endDate: '2026-09-05',
    days: 1,
    reason: '参加校外竞赛，需要请假一天',
    status: '已驳回',
    rejectionReason: '请补充指导老师同意证明后重新提交。',
    applyTime: '2026-09-03 19:05',
  },
])

const records = computed(() =>
  isAdmin.value ? allRecords.value : allRecords.value.filter((record) => record.name === userName.value),
)

/** 表单校验通过后抛上来，插到记录最前面 */
function onSubmit(payload) {
  if (isAdmin.value) {
    ElMessage.error('管理员不能提交学生请假申请')
    return
  }
  allRecords.value.unshift({
    id: Date.now(),
    ...payload,
    name: userName.value,
    status: '待审批',
    applyTime: formatNow(),
  })
}

/** ---------- 撤销 ---------- */
async function cancelRecord(row) {
  if (isAdmin.value || row.name !== userName.value) {
    ElMessage.error('只能撤销自己的请假申请')
    return
  }
  try {
    await ElMessageBox.confirm(`确定撤销这条「${row.type}」申请吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  allRecords.value = allRecords.value.filter((item) => item.id !== row.id)
  ElMessage.success('已撤销')
}

async function reviewRecord(row, status) {
  if (!isAdmin.value) {
    ElMessage.error('只有管理员可以审批请假申请')
    return
  }

  const action = status === '已通过' ? '通过' : '驳回'
  let rejectionReason = ''
  try {
    if (status === '已驳回') {
      const result = await ElMessageBox.prompt(
        `请填写驳回「${row.name}」的${row.type}申请的理由。`,
        '驳回申请',
        {
          confirmButtonText: '确认驳回',
          cancelButtonText: '取消',
          inputType: 'textarea',
          inputPlaceholder: '说明驳回原因，便于申请人修改后重新提交',
          inputAttrs: { maxlength: '200' },
          inputValidator: (value) =>
            value.trim().length >= 2 || '驳回理由至少填写 2 个字',
          inputErrorMessage: '驳回理由至少填写 2 个字',
          inputValue: '',
        },
      )
      rejectionReason = result.value.trim()
    } else {
      await ElMessageBox.confirm(`确定通过「${row.name}」的${row.type}申请吗？`, '请假审批', {
        type: 'success',
        confirmButtonText: '通过',
        cancelButtonText: '取消',
      })
    }
  } catch {
    return
  }

  const record = allRecords.value.find((item) => item.id === row.id)
  if (!record || record.status !== '待审批') {
    ElMessage.warning('该申请已处理或不存在')
    return
  }
  record.status = status
  record.rejectionReason = status === '已驳回' ? rejectionReason : ''
  ElMessage.success(`申请已${action}`)
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

.page-desc {
  margin: 6px 0 0;
  color: var(--st-text-secondary);
  font-size: 13px;
}

/* 表单和表格的样式已随子组件移走，见 ./components/ */
</style>
