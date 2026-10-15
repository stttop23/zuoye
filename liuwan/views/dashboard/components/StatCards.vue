<template>
  <el-row :gutter="16" class="stat-row">
    <el-col v-for="(item, index) in stats" :key="item.label" :xs="12" :sm="12" :md="6">
      <el-card shadow="never" class="stat-card st-fade-up" :class="`st-delay-${index + 1}`">
        <div class="stat-card__inner">
          <div class="stat-card__icon">
            <el-icon :size="20"><component :is="item.icon" /></el-icon>
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
 * item 结构：{ label, value, icon }
 *
 * 视觉规矩（整站统一，改的时候别破）：
 *   - 卡身【纯白】，不铺渐变 —— 渐变只在两个地方：顶部那条 4px 细条 + 图标底
 *   - 四张卡颜色【完全一致】，靠图标和数字区分；每张一个颜色就会像仪表盘
 *
 * 动效全在这里、不需要父级配合：
 *   - 数字从 0 滚上来（CountUp）
 *   - 卡片悬停抬升 + 阴影变深 + 图标轻转
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
  background: var(--st-bg-card);
  border: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-card);
  box-shadow: var(--st-shadow-soft);
  transition:
    transform var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease),
    border-color var(--st-duration-base) var(--st-ease);
}

/*
 * 顶部一条通宽的渐变细条（4px）。
 * 整排四张卡因此像用同一道光“开”了一下 —— 比原来那种
 * 「每张卡一个颜色的小横条」干净得多，也不会视觉过载。
 */
.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  background: var(--grad-blue);
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--st-primary-glow);
  box-shadow: var(--st-shadow-hover);
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

/*
 * 图标：「渐变底 + 白色图标」。
 * ⚠️ 想要「图标图形本身被渐变填充」，得用 SVG 的 mask 或给每个 SVG 加一个
 *    gradient defs —— 图标是 Element Plus 的组件、形状各不相同，做不通用。
 *    渐变底白图标在观感上等价，而且能跟着主色变量一起换。
 */
.stat-card__icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: #fff;
  background: var(--grad-blue);
  border-radius: var(--st-radius-base);
  box-shadow: var(--st-shadow-grad);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

/* 卡片悬停时图标也放大一点，视线自然会跟过去 */
.stat-card:hover .stat-card__icon {
  transform: scale(1.08) rotate(-6deg);
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
