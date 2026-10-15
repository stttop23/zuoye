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
        :class="`tone--${action.tone}`"
        @click="emit('navigate', action.path)"
      >
        <span class="quick__icon">
          <el-icon :size="20"><component :is="action.icon" /></el-icon>
        </span>
        <span class="quick__label">{{ action.label }}</span>
      </button>

      <button type="button" class="quick__item" @click="emit('refresh')">
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
 * 改成「磁贴」：左边一块圆角图标 + 右边文字，点击热区大、手机上也好按
 * （原生 <button>，键盘 Tab 和回车照样能用）。
 *
 * 配色规矩：**平时是单色灰，hover 才点亮成渐变**，而且用【目标模块的色相】——
 * 点「查看公告」亮的是公告页的紫，等于提前告诉你去哪儿。
 * 一上来就四个颜色都很艳，视线会被四块抢光，反而不知道先看哪。
 */
import { Bell, Document, List, Refresh } from '@element-plus/icons-vue'

const emit = defineEmits(['navigate', 'refresh'])

const actions = [
  { path: '/notice', label: '查看公告', icon: Bell, tone: 'indigo' },
  { path: '/todo', label: '我的待办', icon: List, tone: 'orchid' },
  { path: '/leave', label: '发起请假', icon: Document, tone: 'violet' },
]
</script>

<style scoped>
.section {
  border: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-card);
  box-shadow: var(--st-shadow-soft);
}

.section__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}

/* 快捷入口的磁贴：一行四个，手机上变两列（见文件末尾的媒体查询） */
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
  background: var(--st-bg-card);
  border: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-card);
  transition:
    transform var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease),
    border-color var(--st-duration-base) var(--st-ease);
}

.quick__item:hover {
  transform: translateY(-3px);
  border-color: var(--st-primary-glow);
  box-shadow: var(--st-shadow-hover);
}

.quick__item:active {
  transform: translateY(-1px) scale(0.99);
}

/* 图标默认单色灰 —— 一整排四块艳色会互相抢视线 */
.quick__icon {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--st-text-secondary);
  background: var(--st-bg-page);
  border-radius: var(--st-radius-sm);
  transition:
    transform var(--st-duration-base) var(--st-ease-back),
    color var(--st-duration-base) var(--st-ease),
    background-color var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease);
}

/* hover 才点亮：底色换成【目标模块的】那套 135° 渐变，图标翻白。
   没挂 tone 的（刷数据）自动回主色蓝 —— 「刷新」不属于任何模块。 */
.quick__item:hover .quick__icon {
  color: #fff;
  background: var(--tile-grad, var(--grad-blue));
  box-shadow: var(--st-shadow-grad);
  transform: scale(1.08);
}

.quick__item.tone--indigo {
  --tile-grad: var(--grad-indigo);
}

.quick__item.tone--violet {
  --tile-grad: var(--grad-violet);
}

.quick__item.tone--orchid {
  --tile-grad: var(--grad-orchid);
}

.quick__label {
  font-size: 14px;
  font-weight: 500;
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
