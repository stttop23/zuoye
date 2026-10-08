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
  border: none;
}

.section__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}
</style>
