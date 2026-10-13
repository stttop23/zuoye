<template>
  <div class="leave">
    <!-- ==================== 页头 ==================== -->
    <div class="page-head">
      <div>
        <h2 class="page-title">{{ isAdmin ? '请假审批' : '请假申请' }}</h2>
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
import { computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserProfile } from '@/composables/userProfile'
import { leaveRecords, nextId } from '@/composables/appStore'
import { consumeCommand, pendingCommand } from '@/composables/aiAgent'
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

/**
 * 申请记录统一放在 @/composables/appStore —— 首页数字、通知中心、AI 助手
 * 读的都是同一份（以前本页内联一份、首页另数一份、后端又手抄一份，三方对不上）。
 * 顺带好处：appStore 会自动写 localStorage，刷新不再丢。
 */
const allRecords = leaveRecords

const records = computed(() =>
  isAdmin.value
    ? allRecords.value
    : allRecords.value.filter((record) => record.name === userName.value),
)

/** 表单校验通过后抛上来，插到记录最前面 */
function onSubmit(payload) {
  if (isAdmin.value) {
    ElMessage.error('管理员不能提交学生请假申请')
    return
  }
  allRecords.value.unshift({
    id: nextId(allRecords.value),
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
  // 自己不能审自己：管理员也是某个具体的人，「我批我自己的假」说不过去
  if (row.name === userName.value) {
    ElMessage.error('不能审批自己的申请')
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
          inputPlaceholder: '驳回原因',
          inputAttrs: { maxlength: '200' },
          inputValidator: (value) => value.trim().length >= 2 || '驳回理由至少填写 2 个字',
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

/*
 * ---- AI 助手：撤销自己的申请 / 审批别人的申请 ----
 * 这两个动作带有【确认弹窗】（撤销要确认、驳回要填理由），
 * 也就是 AI 只负责把弹窗推到你面前，最后一步永远由人点 —— 这就是设计里「只代笔不代签」。
 * immediate 是为了处理「AI 先跳页再操作」：跳过来时命令可能已经放好了。
 */
watch(
  pendingCommand,
  () => {
    const command = consumeCommand('leave')
    if (!command) return

    if (command.type === 'leave_cancel') {
      if (isAdmin.value) {
        ElMessage.warning('管理员没有自己的请假申请可撤销')
        return
      }
      // 只在【还没审批】的记录里找，已经批过的不能撤
      const mine = allRecords.value.filter(
        (item) =>
          item.status === '待审批' &&
          item.name === userName.value &&
          (!command.kind || item.type === command.kind),
      )
      if (!mine.length) {
        ElMessage.info('没有可撤销的申请（只限还没审批的）')
        return
      }
      cancelRecord(mine[mine.length - 1])
      return
    }

    if (command.type === 'leave_review') {
      if (!isAdmin.value) {
        ElMessage.warning('只有管理员能审批，先在顶栏切到管理员')
        return
      }
      const target = allRecords.value.find(
        (item) => item.status === '待审批' && item.name === command.name,
      )
      if (!target) {
        ElMessage.info(`没找到「${command.name}」待审批的申请`)
        return
      }
      reviewRecord(target, command.status)
    }
  },
  { immediate: true },
)
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

/* 表单和表格的样式已随子组件移走，见 ./components/ */
</style>
