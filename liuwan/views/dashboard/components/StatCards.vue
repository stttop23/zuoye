<template>
  <el-row :gutter="16" class="stat-row">
    <el-col v-for="(item, index) in stats" :key="item.label" :xs="12" :sm="12" :md="6">
      <el-card shadow="never" class="stat-card st-fade-up" :class="`st-delay-${index + 1}`">
        <div class="stat-card__inner">
          <div class="stat-card__icon" :style="{ background: item.bg, color: item.color }">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <div>
            <div class="stat-card__value">
              <CountUp :value="item.value" />
            </div>
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
 *
 * 动效全在这里、不需要父级配合：
 *   - 数字从 0 滚上来（CountUp）
 *   - 卡片悬停抬升 + 阴影变深
 *   - 四张卡错峰入场（.st-delay-N）
 */
import CountUp from '@/components/CountUp.vue'

defineProps({
  stats: { type: Array, required: true },
})
</script>

<style scoped>
.stat-row {
  margin-bottom: 0;
}

.stat-card {
  position: relative;
  overflow: hidden;
  margin-bottom: var(--st-gap-base);
  /* 从白渐变到各自的浅色底，四张卡颜色不一样，整排就不单调了 */
  background: linear-gradient(135deg, #ffffff 30%, var(--card-bg, #fff) 100%);
  /* 悬停时整张卡抬起 4px，像是在告诉你「可以点」 */
  transition:
    transform var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease),
    border-color var(--st-duration-base) var(--st-ease);
}

/* 左上角一根彩色小横条，四张卡一眼能分开 */
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 56px;
  height: 3px;
  background: var(--card-tint, var(--st-primary));
  border-radius: 0 var(--st-radius-pill) var(--st-radius-pill) 0;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--card-tint, var(--st-primary));
  box-shadow: var(--st-shadow-hover);
}

.stat-card__watermark {
  position: absolute;
  right: -14px;
  bottom: -26px;
  color: var(--card-tint, var(--st-primary));
  opacity: 0.09;
  pointer-events: none;
  transition: transform var(--st-duration-slow) var(--st-ease);
}

.stat-card:hover .stat-card__watermark {
  transform: scale(1.12) rotate(-6deg);
}

.stat-card__inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-card__text {
  min-width: 0;
}

.stat-card__icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: var(--card-tint, var(--st-primary));
  background: var(--card-bg, var(--st-primary-light));
  border-radius: var(--st-radius-base);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.7);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

/* 卡片悬停时图标也放大一点，视线自然会跟过去 */
.stat-card:hover .stat-card__icon {
  transform: scale(1.1) rotate(-6deg);
}

.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--st-text-primary);
  /* 数字宽度固定，滚动时旁边文字不会跟着抖 */
  font-variant-numeric: tabular-nums;
}

.stat-card__label {
  margin-top: 2px;
  font-size: 13px;
  color: var(--st-text-secondary);
}
</style>
