<template>
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
        :placeholder="listening ? '正在听……' : '说一句话'"
        @keydown.enter.exact.prevent="submit"
      />
      <div class="ai-chat__actions">
        <div class="ai-chat__actions-left">
          <el-tooltip :content="voiceTip" :disabled="voiceSupported" placement="top">
            <!--
              外面必须套一层 span：
              【禁用】的按钮不触发鼠标事件，直接写在里面的话 tooltip 永远弹不出来 ——
              而「浏览器不支持」恰恰是最需要解释一句的时候（比如 iPhone 上的 Safari）。
            -->
            <span class="ai-chat__voice-wrap">
              <el-button
                link
                class="ai-chat__voice"
                :type="listening ? 'danger' : undefined"
                :disabled="!voiceSupported"
                @click="toggleVoice(draft)"
              >
                <el-icon class="ai-chat__mic" :class="{ 'is-listening': listening }">
                  <Microphone />
                </el-icon>
                {{ listening ? '停止' : '说话' }}
              </el-button>
            </span>
          </el-tooltip>
          <el-button link @click="resetAgent">清空</el-button>
        </div>
        <el-button type="primary" size="small" :loading="agentSending" @click="submit">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * AI 聊天的「本体」：消息列表 + 快捷短语 + 输入区（含语音）。
 *
 * 两个地方共用它，所以对话是同一份（状态在 composables/aiAgent.js 里）：
 *   - 右下角悬浮抽屉：src/components/AiAssistant.vue
 *   - 独立页面：      liuwan/views/assistant/index.vue
 *
 * 它只做三件事：把话发给 composable、把回答渲染出来、让用户点。
 * 「听懂」由后端负责，「填表」由页面负责，这里不掺和。
 * 填完表要把用户带去哪个页面，也由 aiAgent.js 的 runActions 决定。
 */
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Microphone } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import { useSpeechInput } from '@/composables/useSpeechInput'
import { agentMessages, agentSending, resetAgent, sendAgentMessage } from '@/composables/aiAgent'

const route = useRoute()
const { userName } = useUserProfile()

const draft = ref('')
const listRef = ref()

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

/* ---------- 语音输入 ---------- */
/*
 * ⚠️ 用的是浏览器自带能力：只有 Chrome / Edge 有，而且【需要联网】
 *（音频会发到微软 / Google 的服务器，不是本机识别——详见 useSpeechInput.js 顶部说明）。
 *
 * 「点一下开始、再点一下停」，刻意【不用】「按住说话」：
 * 长按会被【系统级】的「选择 / 复制」手势打断 —— 鼠标按住时稍有移动就开始拖选文字，
 * 触摸屏上长按会弹系统菜单，按住的过程被切断，用户看到的就是「按着按着就没了」。
 * 这些靠 touch-action / preventDefault 挡不干净。点击没这个问题，按钮本身也有按下反馈。
 *（识别的文字会先落在输入框里、随时能改，所以本来就不需要用户一直按着。）
 */
const {
  supported: voiceSupported,
  listening,
  stop: stopVoice,
  toggle: toggleVoice,
} = useSpeechInput({
  onText: (text) => {
    draft.value = text
  },
  onError: (message) => ElMessage.warning(message),
})

const voiceTip = computed(() => {
  // 只在不支持的时候提示一句（按钮也置灰了，用户得知道为什么）
  if (!voiceSupported.value)
    return '这个浏览器没有语音识别（只有 Chrome / Edge 有，Safari 和 Firefox 没有）'
  return ''
})

/* ---------- 滚动到底 ---------- */
onMounted(scrollToBottom) // 从抽屉切到页面时，先看到最新一条
watch(agentMessages, scrollToBottom, { deep: true })
watch(agentSending, scrollToBottom)

function scrollToBottom() {
  nextTick(() => {
    const list = listRef.value
    if (list) list.scrollTop = list.scrollHeight
  })
}

/* ---------- 发送 ---------- */
function submit() {
  const content = draft.value.trim()
  if (!content) return
  // 上一条还在路上时按回车：别默默吞掉，给个提示（文字留在输入框里）
  if (agentSending.value) {
    ElMessage.warning('等上一条答完')
    return
  }
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

/*
 * 语音按钮是「点击说话」。
 * 只保留 user-select / touch-callout 的屏蔽：免得双击按钮时把「说话」两个字选中，
 * 也不至于长按时弹系统菜单。注意【没有】touch-action: none ——
 * 那会阻止从按钮上开始的页面滚动，而按钮现在不需要按住，没必要付这个代价。
 */
.ai-chat__voice {
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
}

/* tooltip 的挂载点（禁用状态下也要能弹）。inline-flex 是为了不改变原有排版 */
.ai-chat__voice-wrap {
  display: inline-flex;
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
