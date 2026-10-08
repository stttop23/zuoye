<template>
  <section class="summary-grid" aria-label="待办统计">
    <div class="summary-item">
      <span class="summary-label">全部事项</span>
      <strong class="summary-value">{{ stats.total }}</strong>
    </div>
    <div class="summary-item">
      <span class="summary-label">待办</span>
      <strong class="summary-value summary-value--info">{{ stats.pending }}</strong>
    </div>
    <div class="summary-item">
      <span class="summary-label">进行中</span>
      <strong class="summary-value summary-value--warning">{{ stats.ongoing }}</strong>
    </div>
    <div class="summary-item">
      <span class="summary-label">已完成</span>
      <strong class="summary-value summary-value--success">{{ stats.completed }}</strong>
    </div>
  </section>
</template>

<script setup>
/**
 * 待办统计条：纯展示，数字由父级算好后传进来。
 * stats 结构：{ total, pending, ongoing, completed }
 */
defineProps({
  stats: { type: Object, required: true },
})
</script>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--st-gap-base);
}

.summary-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  padding: 0 var(--st-gap-base);
  border: 1px solid var(--st-border-color-light);
  border-radius: var(--st-radius-base);
  background: var(--st-bg-card);
}

.summary-label {
  color: var(--st-text-secondary);
  font-size: 14px;
}

.summary-value {
  color: var(--st-text-primary);
  font-size: 24px;
  line-height: 1;
}

.summary-value--info {
  color: var(--st-info);
}

.summary-value--warning {
  color: var(--st-warning);
}

.summary-value--success {
  color: var(--st-success);
}

@media (max-width: 760px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--st-gap-sm);
  }

  .summary-item {
    min-height: 64px;
    padding: 0 12px;
  }
}
</style>
