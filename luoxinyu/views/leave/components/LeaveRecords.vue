<template>
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
          <el-button v-if="row.status === '待审批'" type="danger" link @click="emit('cancel', row)">
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
</template>

<script setup>
/**
 * 申请记录表格：纯展示 + 抛事件。
 * 只有「待审批」的行才显示撤销按钮，确认逻辑由父级处理。
 */
defineProps({
  records: { type: Array, required: true },
})

const emit = defineEmits(['cancel'])

const typeTagMap = { 事假: 'primary', 病假: 'warning', 年假: 'success' }
const statusTagMap = { 待审批: 'warning', 已通过: 'success', 已驳回: 'danger' }
</script>

<style scoped>
.section {
  border: none;
}

.section__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.leave__muted {
  color: var(--st-text-placeholder);
}
</style>
