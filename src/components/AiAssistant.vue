<template>
  <!-- 右下角悬浮入口，全站常驻 -->
  <div class="ai-fab">
    <el-tooltip content="AI 助手" placement="left">
      <el-button type="primary" circle size="large" @click="drawerVisible = true">
        <el-icon :size="22"><ChatDotRound /></el-icon>
      </el-button>
    </el-tooltip>
  </div>

  <el-drawer v-model="drawerVisible" title="AI 助手" direction="rtl" size="380px" class="ai-drawer">
    <AiChatPanel />
  </el-drawer>
</template>

<script setup>
/**
 * 右下角悬浮入口（抽屉壳 + 悬浮按钮）。
 *
 * 聊天的本体在 AiChatPanel.vue，跟「AI 助手」独立页面共用同一份——
 * 对话状态存在 composables/aiAgent.js，所以抽屉里聊到一半切到页面，记录还在。
 */
import { ref } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import AiChatPanel from '@/components/AiChatPanel.vue'
import { onAgentCloseRequest } from '@/composables/aiAgent'

/**
 * 抽屉开关【必须】是本组件自己的 ref。
 * 曾经把它放在 aiAgent.js 里共享，结果 el-drawer 的写回到不了那个 ref，
 * 表现是「点 X / 按 Esc / 点遮罩都关不掉」。自己的 ref 没这个问题。
 */
const drawerVisible = ref(false)

// AI 填完表要自动收起抽屉：composable 发「关闭请求」过来，这里接住
onAgentCloseRequest(() => {
  drawerVisible.value = false
})
</script>

<style scoped>
.ai-fab {
  position: fixed;
  right: 32px;
  bottom: 32px;
  z-index: 1500;
}

.ai-fab :deep(.el-button) {
  width: 52px;
  height: 52px;
  box-shadow: 0 6px 18px rgba(64, 158, 255, 0.35);
}

/* 抽屉内容由 AiChatPanel 自己排版，这里把内边距清掉 */
.ai-drawer :deep(.el-drawer__body) {
  padding: 0;
}
</style>
