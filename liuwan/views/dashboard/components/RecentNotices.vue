<template>
  <el-card shadow="never" class="section">
    <template #header>
      <div class="flex-between">
        <span class="section__title">最新公告</span>
        <el-link type="primary" underline="never" @click="emit('view-all')">查看全部</el-link>
      </div>
    </template>

    <el-table :data="notices" stripe style="width: 100%">
      <el-table-column prop="title" label="公告标题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="publishTime" label="发布时间" width="180" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.top ? 'danger' : 'info'" size="small" effect="light">
            {{ row.top ? '置顶' : '普通' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
/**
 * 最新公告列表：纯展示组件，「查看全部」抛给父级处理。
 */
defineProps({
  notices: { type: Array, required: true },
})

const emit = defineEmits(['view-all'])
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
</style>
