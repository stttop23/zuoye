<template>
  <el-row :gutter="16" class="stat-row">
    <el-col v-for="item in stats" :key="item.label" :xs="12" :sm="12" :md="6">
      <el-card shadow="hover" class="stat-card">
        <div class="stat-card__inner">
          <div class="stat-card__icon" :style="{ background: item.bg, color: item.color }">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <div>
            <div class="stat-card__value">{{ item.value }}</div>
            <div class="stat-card__label">{{ item.label }}</div>
          </div>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
/**
 * 数据卡片：纯展示组件，数据由父级传入。
 * item 结构：{ label, value, icon, color, bg }
 */
defineProps({
  stats: { type: Array, required: true },
})
</script>

<style scoped>
.stat-row {
  margin-bottom: 0;
}

.stat-card {
  margin-bottom: var(--st-gap-base);
}

.stat-card__inner {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--st-radius-base);
}

.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--st-text-primary);
}

.stat-card__label {
  margin-top: 2px;
  font-size: 13px;
  color: var(--st-text-secondary);
}
</style>
