<template>
  <el-card shadow="never" class="section">
    <template #header>
      <span class="section__title">快捷入口</span>
    </template>

    <div class="quick">
      <button
        v-for="action in actions"
        :key="action.path"
        type="button"
        class="quick__item"
        :style="{ '--tile-tint': action.tint, '--tile-bg': action.bg }"
        @click="emit('navigate', action.path)"
      >
        <span class="quick__icon">
          <el-icon :size="20"><component :is="action.icon" /></el-icon>
        </span>
        <span class="quick__label">{{ action.label }}</span>
      </button>

      <button type="button" class="quick__item quick__item--ghost" @click="emit('refresh')">
        <span class="quick__icon">
          <el-icon :size="20"><Refresh /></el-icon>
        </span>
        <span class="quick__label">刷新数据</span>
      </button>
    </div>
  </el-card>
</template>

<script setup>
/**
 * 快捷入口。
 *
 * 原来是一排 Element Plus 按钮，四个灰边圆角框排在一起挺单调的。
 * 改成「磁贴」：左边一块带底色的圆角图标 + 右边文字，
 *   1) 四块颜色不同，整排有了节奏；
 *   2) 点击热区大很多，手机上也好按；
 *   3) 用原生 <button>，键盘 Tab 和回车照样能用。
 */
import { Bell, Document, List, Refresh } from '@element-plus/icons-vue'

const emit = defineEmits(['navigate', 'refresh'])

const actions = [
  {
    path: '/notice',
    label: '查看公告',
    icon: Bell,
    tint: 'var(--st-primary)',
    bg: 'var(--st-primary-light)',
  },
  {
    path: '/todo',
    label: '我的待办',
    icon: List,
    tint: 'var(--st-success)',
    bg: 'var(--st-success-light)',
  },
  {
    path: '/leave',
    label: '发起请假',
    icon: Document,
    tint: 'var(--st-warning)',
    bg: 'var(--st-warning-light)',
  },
]
</script>

<style scoped>
.section {
  border: 1px solid var(--st-border-color-hair);
  box-shadow: var(--st-shadow-card);
}

.section__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}

/* 快捷入口的按钮做得比普通按钮「胖」一点，点着踏实 */
/* 快捷入口的磁贴 */
.quick {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.quick__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  font: inherit;
  color: var(--st-text-primary);
  text-align: left;
  appearance: none;
  cursor: pointer;
  background: linear-gradient(135deg, #ffffff 40%, var(--tile-bg, #fff) 100%);
  border: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-base);
  transition:
    transform var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease),
    border-color var(--st-duration-base) var(--st-ease);
}

.quick__item:hover {
  transform: translateY(-3px);
  border-color: var(--tile-tint, var(--st-primary));
  box-shadow: var(--st-shadow-hover);
}

.quick__item:active {
  transform: translateY(-1px) scale(0.99);
}

.quick__icon {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--tile-tint, var(--st-text-regular));
  background: var(--tile-bg, var(--st-bg-page));
  border-radius: var(--st-radius-sm);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.quick__item:hover .quick__icon {
  transform: scale(1.1) rotate(-6deg);
}

.quick__label {
  font-size: 14px;
  font-weight: 500;
}

/* 「刷新数据」没什么好配色，做成灰的，不要抢前三个的戏 */
.quick__item--ghost {
  --tile-tint: var(--st-text-secondary);
  --tile-bg: var(--st-bg-page);
}

/* 手机上四列放不下，两列 */
@media (max-width: 768px) {
  .quick {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .quick__label {
    font-size: 13px;
  }
}
</style>
