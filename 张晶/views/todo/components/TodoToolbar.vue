<template>
  <div class="todo-toolbar">
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
  </div>
</template>

<script setup>
/**
 * 筛选栏：关键词搜索 + 优先级/分类下拉 + 状态切换。
 * 四个筛选条件都用 v-model 双向绑定出去，过滤逻辑由父级负责。
 */
import { Search } from '@element-plus/icons-vue'

defineProps({
  categories: { type: Array, required: true },
})

const statusFilters = ['全部', '待办', '进行中', '已完成']

const keyword = defineModel('keyword', { type: String, default: '' })
const statusFilter = defineModel('statusFilter', { type: String, default: '全部' })
const priorityFilter = defineModel('priorityFilter', { type: String, default: '' })
const categoryFilter = defineModel('categoryFilter', { type: String, default: '' })
</script>

<style scoped>
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

@media (max-width: 760px) {
  .search-input,
  .filter-select {
    width: 100%;
  }
}
</style>
