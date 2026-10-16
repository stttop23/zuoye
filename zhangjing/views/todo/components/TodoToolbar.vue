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
  gap: var(--st-gap-md);
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

/* 状态切换：选中项走品牌浅底 + 主色字，不再靠 EP 默认那层灰 */
.status-tabs :deep(.el-radio-button__inner) {
  font-size: 13px;
  white-space: nowrap;
  transition:
    background-color var(--st-duration-fast) var(--st-ease),
    color var(--st-duration-fast) var(--st-ease),
    box-shadow var(--st-duration-fast) var(--st-ease);
}

/* 状态切换：选中项走【本模块色】的渐变底 + 白字。
   其它页面都有一块大面积的模块色（表头/卡片底）当「本页签名」，
   待办页全是白卡 + 表格里没有表头，就靠这颗胶囊认领它的葡萄紫。
   白字压在深紫上对比度 6.3:1，过了 AA。

   ⚠️ 选择器必须带 .is-active：Element Plus 自己的选中样式写的是
   `.el-radio-button.is-active .el-radio-button__original-radio:not(:disabled) + .el-radio-button__inner`（权重 0,5,0），
   只写 `:checked` 权重同样是 0,5,0，谁后注入谁赢 —— 在 Vite 下不稳定。
   带上 .is-active 后是 0,6,0，能稳定压过 EP。 */
.status-tabs
  :deep(.el-radio-button.is-active .el-radio-button__original-radio + .el-radio-button__inner) {
  background: var(--module-grad, var(--st-primary));
  /* 万一上面的渐变算不出值，还有一层纯色兜底，不会变成透明 */
  background-color: var(--module-ink, var(--st-primary));
  border-color: var(--module-ink, var(--st-primary));
  color: var(--st-text-inverse);
  box-shadow: none;
}

.status-tabs :deep(.el-radio-button__original-radio:focus-visible + .el-radio-button__inner) {
  box-shadow: var(--st-shadow-glow);
}

@media (max-width: 768px) {
  .search-input,
  .filter-select {
    width: 100%;
  }

  /* 触摸目标不小于 44px */
  .filter-toolbar :deep(.el-input__wrapper),
  .filter-toolbar :deep(.el-select__wrapper),
  .status-tabs :deep(.el-radio-button__inner) {
    min-height: 44px;
  }
}
</style>
