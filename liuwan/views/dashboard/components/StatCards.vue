<template>
  <el-row :gutter="16" class="stat-row">
    <el-col v-for="(item, index) in stats" :key="item.label" :xs="12" :sm="12" :md="6">
      <el-card
        shadow="never"
        class="stat-card st-fade-up"
        :class="[`st-delay-${index + 1}`, `tone--${item.tone}`]"
      >
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
 * item 结构：{ label, value, icon, tone }
 *
 * tone = 卡片色相（浅色彩虹：青→蓝紫→紫→粉）。
 *   卡身依然是【纯白】，只有两个地方上色：顶部那条 4px 细条 + 图标底。
 *   四张卡颜色不一样才有“彩虹”，但只给这一小块，大面积白留白才不吵。
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

/* 每张卡自己的渐变（模板里挂的 tone--xxx） */
.stat-card.tone--teal {
  --card-grad: var(--grad-teal);
}

.stat-card.tone--indigo {
  --card-grad: var(--grad-indigo);
}

.stat-card.tone--violet {
  --card-grad: var(--grad-violet);
}

.stat-card.tone--pink {
  --card-grad: var(--grad-pink);
}

/*
 * 顶部一条通宽的渐变细条（4px）。
 * 整排四张卡各一道不同颜色的光 —— 比原来那种「四张卡一个颜色」有精神，
 * 但又只占 4px，不会把页面打成花脸。
 */
.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 4px;
  background: var(--card-grad, var(--grad-blue));
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--card-grad, var(--st-primary-glow));
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
 *    渐变底白图标在观感上等价，而且能跟着色相变量一起换。
 */
.stat-card__icon {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  color: #fff;
  background: var(--card-grad, var(--grad-blue));
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
