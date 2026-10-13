<template>
  <el-card shadow="never" class="section">
    <template #header>
      <span class="section__title">快捷入口</span>
    </template>

    <el-space wrap :size="12">
      <el-button type="primary" @click="emit('navigate', '/notice')">
        <el-icon><Bell /></el-icon>
        查看公告
      </el-button>
      <el-button type="success" @click="emit('navigate', '/todo')">
        <el-icon><List /></el-icon>
        我的待办
      </el-button>
      <el-button type="warning" @click="emit('navigate', '/leave')">
        <el-icon><Document /></el-icon>
        发起请假
      </el-button>
      <el-button plain @click="emit('refresh')">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </el-space>
  </el-card>
</template>

<script setup>
/**
 * 快捷入口：只负责「点哪个按钮」，跳转和刷新交给父级。
 */
import { Bell, Document, List, Refresh } from '@element-plus/icons-vue'

const emit = defineEmits(['navigate', 'refresh'])
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
.section :deep(.el-button) {
  height: 40px;
  padding: 0 18px;
  border-radius: var(--st-radius-base);
}

/* 悬停时抬起来 + 图标往里滑一下，暗示「要跳走了」 */
.section :deep(.el-button:not(.is-plain)):hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 18px rgba(16, 42, 82, 0.14);
}

.section :deep(.el-button .el-icon) {
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.section :deep(.el-button:hover .el-icon) {
  transform: translateX(2px) scale(1.12);
}
</style>
