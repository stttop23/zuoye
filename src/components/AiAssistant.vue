<template>
  <!-- 右下角悬浮按钮，全站常驻 -->
  <div class="ai-fab">
    <el-tooltip content="AI 助手" placement="left">
      <el-button type="primary" circle size="large" @click="drawerVisible = true">
        <el-icon :size="22"><ChatDotRound /></el-icon>
      </el-button>
    </el-tooltip>
  </div>

  <el-drawer v-model="drawerVisible" title="AI 助手" direction="rtl" size="380px" class="ai-drawer">
    <div class="ai-chat">
      <div ref="listRef" class="ai-chat__list">
        <div
          v-for="(message, index) in agentMessages"
          :key="index"
          :class="['ai-msg', `ai-msg--${message.role}`]"
        >
          <div class="ai-msg__bubble">{{ message.content }}</div>
          <span v-if="message.source" class="ai-msg__source">
            {{ sourceLabels[message.source] ?? message.source }}
          </span>
        </div>

        <div v-if="agentSending" class="ai-msg ai-msg--assistant">
          <div class="ai-msg__bubble ai-msg__bubble--typing">思考中…</div>
        </div>
      </div>

      <div class="ai-chat__chips">
        <el-tag
          v-for="item in suggestions"
          :key="item"
          size="small"
          effect="plain"
          class="ai-chat__chip"
          @click="useSuggestion(item)"
        >
          {{ item }}
        </el-tag>
      </div>

      <div class="ai-chat__input">
        <el-input
          v-model="draft"
          type="textarea"
          :rows="2"
          resize="none"
          :placeholder="listening ? '正在听……说完点「停止」' : '说一句话，比如：下周三到周五请病假'"
          @keydown.enter.exact.prevent="submit"
        />
        <div class="ai-chat__actions">
          <div class="ai-chat__actions-left">
            <el-tooltip :content="voiceTip" placement="top">
              <el-button
                link
                :type="listening ? 'danger' : undefined"
                :disabled="!voiceSupported"
                @click="toggleVoice"
              >
                <el-icon class="ai-chat__mic" :class="{ 'is-listening': listening }">
                  <Microphone />
                </el-icon>
                {{ listening ? '停止' : '语音' }}
              </el-button>
            </el-tooltip>
            <el-button link @click="resetAgent">清空</el-button>
          </div>
          <el-button type="primary" size="small" :loading="agentSending" @click="submit">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
/**
 * 右下角 AI 助手。
 * 它只做三件事：把话发给 composable、把回答渲染出来、让用户点。
 * 「听懂」由后端负责，「填表」由页面负责，这里不掺和。
 */
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Microphone } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import { useSpeechInput } from '@/composables/useSpeechInput'
import {
  agentMessages,
  agentSending,
  onAgentCloseRequest,
  resetAgent,
  sendAgentMessage,
} from '@/composables/aiAgent'

const route = useRoute()
const { userName } = useUserProfile()

/**
 * 抽屉开关【必须】是本组件自己的 ref。
 * 曾经把它放在 aiAgent.js 里共享，结果 el-drawer 的写回到不了那个 ref，
 * 表现是「点 X / 按 Esc / 点遮罩都关不掉」。自己的 ref 没这个问题。
 */
const drawerVisible = ref(false)

const draft = ref('')
const listRef = ref()

/* ---------- 语音输入 ---------- */
// ⚠️ 用的是浏览器自带能力：只有 Chrome / Edge 有，而且【需要联网】
// （音频会发到微软 / Google 的服务器，不是本机识别——详见 useSpeechInput.js 顶部说明）
const {
  supported: voiceSupported,
  listening,
  toggle: toggleVoiceRaw,
  stop: stopVoice,
} = useSpeechInput({
  onText: (text) => {
    draft.value = text
  },
  onError: (message) => ElMessage.warning(message),
})

const voiceTip = computed(() => {
  if (!voiceSupported.value) return '当前浏览器不支持语音输入，换 Chrome 或 Edge'
  return listening.value ? '点一下停止' : '点一下开始说话'
})

function toggleVoice() {
  // 把输入框里已有的内容传进去，识别结果会接在它后面，不会覆盖
  toggleVoiceRaw(draft.value)
}

// AI 填完表要自动收起抽屉：composable 发「关闭请求」过来，这里接住
onAgentCloseRequest(() => {
  drawerVisible.value = false
})

/** 气泡下面那行小字：告诉用户这次是「谁」答的 */
const sourceLabels = {
  ai: 'AI',
  ollama: '本机模型',
  local: '本地规则',
}

const suggestions = [
  '下周三到周五请病假，感冒发烧',
  '打开待办事项',
  '新建待办：整理周例会材料，周五截止',
]

watch(drawerVisible, (open) => {
  if (open) scrollToBottom()
  else stopVoice() // 抽屉关掉就把麦克风也放掉
})
watch(agentMessages, scrollToBottom, { deep: true })
watch(agentSending, scrollToBottom)

function scrollToBottom() {
  nextTick(() => {
    const list = listRef.value
    if (list) list.scrollTop = list.scrollHeight
  })
}

function submit() {
  const content = draft.value.trim()
  if (!content || agentSending.value) return
  stopVoice() // 还在说话就点了发送，先把麦克风关了
  draft.value = ''
  sendAgentMessage(content, { page: route.path, userName: userName.value })
}

function useSuggestion(content) {
  draft.value = content
  submit()
}
</script>

<style scoped>
/* ---------- 悬浮按钮 ---------- */
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

/* ---------- 聊天区 ---------- */
.ai-drawer :deep(.el-drawer__body) {
  padding: 0;
}

.ai-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.ai-chat__list {
  flex: 1;
  overflow-y: auto;
  padding: var(--st-gap-base);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-msg {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 88%;
}

.ai-msg--user {
  align-self: flex-end;
  align-items: flex-end;
}

.ai-msg__bubble {
  padding: 9px 12px;
  border-radius: var(--st-radius-base);
  background: var(--st-bg-page);
  color: var(--st-text-primary);
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.ai-msg--user .ai-msg__bubble {
  background: var(--st-primary);
  color: var(--st-bg-card);
}

.ai-msg__bubble--typing {
  color: var(--st-text-secondary);
}

.ai-msg__source {
  margin-top: 4px;
  color: var(--st-text-placeholder);
  font-size: 11px;
}

/* ---------- 快捷短语 ---------- */
.ai-chat__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--st-gap-sm);
  padding: 0 var(--st-gap-base) var(--st-gap-sm);
}

.ai-chat__chip {
  cursor: pointer;
}

/* ---------- 输入区 ---------- */
.ai-chat__input {
  display: flex;
  flex-direction: column;
  gap: var(--st-gap-sm);
  padding: var(--st-gap-base);
  border-top: 1px solid var(--st-border-color-light);
}

.ai-chat__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ai-chat__actions-left {
  display: flex;
  align-items: center;
  gap: var(--st-gap-sm);
}

/* 正在听的时候让麦克风「呼吸」一下，答辩演示时一眼能看出来 */
.ai-chat__mic.is-listening {
  animation: ai-mic-pulse 1s ease-in-out infinite;
}

@keyframes ai-mic-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
