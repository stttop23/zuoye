<template>
  <div class="assistant-page">
    <header class="page-head">
      <h2 class="page-title">AI 助手</h2>
    </header>

    <el-card shadow="never" class="assistant-card">
      <AiChatPanel />
    </el-card>
  </div>
</template>

<script setup>
/**
 * AI 助手独立页面。
 *
 * 聊天本体复用 src/components/AiChatPanel.vue —— 跟右下角那个悬浮抽屉
 * 是同一份对话（状态在 composables/aiAgent.js 里），所以两边可以随便切。
 *
 * 填完表会自动跳到对应页面（比如「请病假」→ 请假页），
 * 这是 aiAgent.js 里 runActions 的行为，两个入口都一样。
 */
import AiChatPanel from '@/components/AiChatPanel.vue'
</script>

<style scoped>
.assistant-page {
  display: flex;
  flex-direction: column;
  gap: var(--st-page-gap);
  /* 撑满内容区，聊天区才能自己滚动，而不是整页滚 */
  height: 100%;
}

/* 标题的字号/字重/颜色全在 global.css 的 .page-title 里，这里不再重复一遍
   （重复写的话，以后全局改标题样式，这一页会顽固地不跟着变） */

.assistant-card {
  flex: 1;
  min-height: 0;
  border: none;
}

/* 让卡片内部撑满，AiChatPanel 的 height: 100% 才有参照 */
.assistant-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
}
</style>
