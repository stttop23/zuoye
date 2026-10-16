<template>
  <el-row :gutter="16" class="stat-row">
    <el-col v-for="(item, index) in stats" :key="item.label" :xs="12" :sm="12" :md="6">
      <el-card
        shadow="never"
        class="stat-card st-fade-up"
        :class="[`st-delay-${index + 1}`, `tone--${item.tone}`]"
      >
        <div class="stat-card__top">
          <span class="stat-card__label">{{ item.label }}</span>
          <span class="stat-card__icon">
            <el-icon :size="18"><component :is="item.icon" /></el-icon>
          </span>
        </div>

        <div class="stat-card__value">
          <CountUp :value="item.value" />
        </div>

        <div class="stat-card__sub">{{ item.sub }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
/**
 * 数据卡片：纯展示组件，数据由父级传入。
 * item 结构：{ label, value, icon, tone, sub }
 *
 * 版式（就是主流后台模板那一套，很好用）：
 *   第一行：小字标签（左） + 软底图标（右）
 *   第二行：大号数字
 *   第三行：一行真实的小字（分隔线上方）
 * 比“图标在左、数字在右”更透气，数字也更突出 —— 看板本来就是看数字的。
 *
 * tone = 卡片色相。三档各自的活儿：
 *   --card-wash  图标底（很浅）
 *   --card-ink   图标颜色（深）
 *   --card-line  悬停时的边框色（中等）
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
  /* 卡片内边距比 EP 默认的 20px 略收，四张卡并排才不显得胖 */
  --el-card-padding: 18px 20px;
  transition:
    transform var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease),
    border-color var(--st-duration-base) var(--st-ease);
}

/* 每张卡自己的三档色（模板里挂的 tone--xxx） */
.stat-card.tone--teal {
  --card-wash: var(--tone-teal-fade);
  --card-ink: var(--tone-teal-deep);
  --card-line: var(--tone-teal-soft);
}

.stat-card.tone--indigo {
  --card-wash: var(--tone-indigo-fade);
  --card-ink: var(--tone-indigo-deep);
  --card-line: var(--tone-indigo-soft);
}

.stat-card.tone--violet {
  --card-wash: var(--tone-violet-fade);
  --card-ink: var(--tone-violet-deep);
  --card-line: var(--tone-violet-soft);
}

.stat-card.tone--pink {
  --card-wash: var(--tone-pink-fade);
  --card-ink: var(--tone-pink-deep);
  --card-line: var(--tone-pink-soft);
}

.stat-card:hover {
  transform: translateY(-3px);
  border-color: var(--card-line, var(--st-primary-glow));
  box-shadow: var(--st-shadow-hover);
}

/* 第一行：标签在左、图标在右 */
.stat-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.stat-card__label {
  padding-top: 6px;
  font-size: 13px;
  color: var(--st-text-secondary);
}

/*
 * 图标：浅底 + 同色深图标。
 * ⚠️ 想要「图标图形本身被渐变填充」，得用 SVG 的 mask 或给每个 SVG 加一个
 *    gradient defs —— Element Plus 的图标形状各不相同，做不通用。
 *    浅底深图标在模板里就是这个做法，观感稳，也不会把卡片弄得太吵。
 */
.stat-card__icon {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  color: var(--card-ink, var(--st-primary));
  background: var(--card-wash, var(--st-primary-light));
  border-radius: 10px;
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

/* 卡片悬停时图标轻转一下，视线自然会跟过去 */
.stat-card:hover .stat-card__icon {
  transform: scale(1.08) rotate(-6deg);
}

.stat-card__value {
  margin-top: 4px;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.15;
  color: var(--st-text-primary);
  /* 数字宽度固定，滚动时旁边文字不会跟着抖 */
  font-variant-numeric: tabular-nums;
}

/* 底下那行真数字：一条细分割线隔开，当“脚注”用 */
.stat-card__sub {
  margin-top: 12px;
  padding-top: 10px;
  font-size: 12px;
  color: var(--st-text-secondary);
  border-top: 1px solid var(--st-border-color-hair);
}
</style>
