<template>
  <div class="leave">
    <!-- ==================== 页头 ==================== -->
    <div class="page-head">
      <h2 class="page-title">请假申请</h2>
    </div>

    <!-- ==================== 填写申请（子组件） ==================== -->
    <LeaveForm @submit="onSubmit" />

    <!-- ==================== 申请记录（子组件） ==================== -->
    <LeaveRecords :records="records" @cancel="cancelRecord" />
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
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import LeaveForm from './components/LeaveForm.vue'
import LeaveRecords from './components/LeaveRecords.vue'

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

/** 表单校验通过后抛上来，插到记录最前面 */
function onSubmit(payload) {
  records.value.unshift({
    id: Date.now(),
    ...payload,
    status: '待审批',
    applyTime: formatNow(),
  })
}

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

/* 表单和表格的样式已随子组件移走，见 ./components/ */
</style>
