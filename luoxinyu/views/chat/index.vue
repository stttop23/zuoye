<template>
  <div class="chat-view">
    <aside class="chat-sidebar">
      <div class="sidebar-heading">
        <div>
          <h2>我的群聊</h2>
          <p>和伙伴保持联系</p>
        </div>
        <el-button circle plain aria-label="新建群聊">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>

      <el-scrollbar class="group-scroll">
        <button
          v-for="group in sortedGroups"
          :key="group.id"
          type="button"
          class="group-item"
          :class="{ 'is-active': group.id === currentGroupId }"
          @click="selectGroup(group.id)"
        >
          <el-avatar :size="44" :class="['group-avatar', group.color]">
            {{ group.avatar }}
          </el-avatar>
          <span class="group-info">
            <span class="group-title-row">
              <strong>{{ group.name }}</strong>
              <time>{{ group.time }}</time>
            </span>
            <span class="group-preview">{{ group.preview }}</span>
          </span>
          <span v-if="group.unread" class="unread-dot"></span>
        </button>
      </el-scrollbar>
    </aside>

    <main class="chat-main">
      <header class="chat-header">
        <div class="chat-title">
          <h2>{{ currentGroup.name }}</h2>
          <span>{{ currentGroup.members.length }} 位成员</span>
        </div>
        <el-button circle plain aria-label="更多群聊选项">
          <el-icon><MoreFilled /></el-icon>
        </el-button>
      </header>

      <el-scrollbar ref="messageScrollbar" class="message-scroll">
        <!-- key 绑定当前群：切群时整块重建，消息的入场动画才会重播 -->
        <div :key="currentGroupId" class="message-list">
          <div class="date-divider"><span>今天</span></div>
          <div
            v-for="message in currentGroup.messages"
            :key="message.id"
            class="message-row"
            :class="{ 'is-self': message.userId === currentUser.id }"
          >
            <el-avatar
              v-if="message.userId !== currentUser.id"
              :size="38"
              :class="['message-avatar', message.color]"
            >
              {{ message.avatar }}
            </el-avatar>
            <div class="message-content">
              <div class="message-meta">
                <strong>
                  {{ message.userId === currentUser.id ? currentUser.name : message.name }}
                </strong>
                <time>{{ message.time }}</time>
              </div>
              <div class="message-bubble">{{ message.content }}</div>
            </div>
            <el-avatar
              v-if="message.userId === currentUser.id"
              :size="38"
              class="message-avatar self-avatar"
            >
              {{ currentUser.avatar }}
            </el-avatar>
          </div>
        </div>
      </el-scrollbar>

      <div class="composer">
        <div class="composer-tools">
          <el-popover
            v-model:visible="emojiPopoverVisible"
            trigger="click"
            placement="top-start"
            :width="280"
          >
            <template #reference>
              <el-button text aria-label="表情" :aria-expanded="emojiPopoverVisible">
                <el-icon><ElementPlus /></el-icon>
              </el-button>
            </template>
            <div class="emoji-picker" aria-label="选择表情">
              <button
                v-for="emoji in emojis"
                :key="emoji"
                type="button"
                class="emoji-option"
                :aria-label="`插入${emoji}表情`"
                @click="appendEmoji(emoji)"
              >
                {{ emoji }}
              </button>
            </div>
          </el-popover>
          <span>按 Enter 发送消息</span>
        </div>
        <el-input
          v-model="draftMessage"
          type="textarea"
          :rows="2"
          resize="none"
          placeholder="输入消息..."
          @keydown.enter.exact.prevent="sendMessage"
        />
        <div class="composer-footer">
          <span>友善沟通，让协作更高效</span>
          <el-button
            class="chat-send"
            type="primary"
            :disabled="!draftMessage.trim()"
            @click="sendMessage"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </main>

    <aside class="members-sidebar">
      <div class="members-heading">
        <h2>群成员</h2>
        <el-tag effect="light" type="primary" round>{{ currentGroup.members.length }} 人</el-tag>
      </div>
      <el-scrollbar class="members-scroll">
        <div class="member-list">
          <div v-for="member in currentGroup.members" :key="member.userId" class="member-item">
            <el-avatar :size="38" :class="['member-avatar', member.color]">
              {{ member.userId === currentUser.id ? currentUser.avatar : member.avatar }}
            </el-avatar>
            <div class="member-info">
              <strong>
                {{ member.userId === currentUser.id ? currentUser.name : member.name }}
              </strong>
              <span v-if="member.role" class="member-role">{{ member.role }}</span>
              <span v-else class="member-status">{{ member.online ? '在线' : '离线' }}</span>
            </div>
            <span v-if="member.online" class="online-dot"></span>
          </div>
        </div>
      </el-scrollbar>
      <div class="group-note">
        <el-icon><InfoFilled /></el-icon>
        <span>保持沟通，协作更顺畅</span>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ElementPlus, InfoFilled, MoreFilled, Plus, Promotion } from '@element-plus/icons-vue'
import { consumeCommand, pendingCommand } from '@/composables/aiAgent'

const currentGroupId = ref('dev')
const draftMessage = ref('')
const messageScrollbar = ref(null)
const replyTimers = new Set()
const currentUser = ref({ id: 1, name: '刘皖', avatar: '刘' })
const emojiPopoverVisible = ref(false)
const emojis = [
  '😀',
  '😁',
  '😂',
  '🤣',
  '😊',
  '😍',
  '🥰',
  '😘',
  '😎',
  '🤔',
  '😅',
  '😭',
  '😡',
  '👍',
  '👎',
  '👏',
  '🙏',
  '🎉',
  '❤️',
  '🔥',
  '✨',
  '💯',
  '👌',
  '🤝',
]

const groups = ref([
  {
    id: 'dev',
    name: '开发1群',
    avatar: '开',
    color: 'avatar-blue',
    time: '10:42',
    preview: '我在写代码，稍等。',
    unread: 2,
    messages: [
      {
        id: 1,
        userId: 2,
        name: '用户A',
        avatar: 'A',
        color: 'avatar-green',
        content: '大家今天打卡了吗？',
        time: '10:30',
      },
      {
        id: 2,
        userId: 3,
        name: '用户B',
        avatar: 'B',
        color: 'avatar-orange',
        content: '打卡了，今天有什么任务安排？',
        time: '10:34',
      },
      {
        id: 3,
        userId: 1,
        content: '我在写代码，稍等。',
        time: '10:42',
      },
    ],
    members: [
      { userId: 1, color: 'avatar-blue', role: '群主', online: true },
      { userId: 2, name: '用户A', avatar: 'A', color: 'avatar-green', online: true },
      { userId: 3, name: '用户B', avatar: 'B', color: 'avatar-orange', online: true },
      { userId: 4, name: '林晓', avatar: '林', color: 'avatar-purple', online: false },
      { userId: 5, name: '陈宇', avatar: '陈', color: 'avatar-teal', online: true },
    ],
  },
  {
    id: 'project',
    name: '项目讨论组',
    avatar: '项',
    color: 'avatar-purple',
    time: '昨天',
    preview: '周五我们一起确认方案吧。',
    unread: 0,
    messages: [
      {
        id: 4,
        userId: 4,
        name: '林晓',
        avatar: '林',
        color: 'avatar-purple',
        content: '周五我们一起确认方案吧。',
        time: '昨天 16:20',
      },
    ],
    members: [
      { userId: 1, color: 'avatar-blue', role: '群主', online: true },
      { userId: 4, name: '林晓', avatar: '林', color: 'avatar-purple', online: true },
      { userId: 5, name: '陈宇', avatar: '陈', color: 'avatar-teal', online: false },
    ],
  },
  {
    id: 'advisor',
    name: '辅导员群',
    avatar: '辅',
    color: 'avatar-orange',
    time: '周一',
    preview: '请大家及时查看本周安排。',
    unread: 1,
    messages: [
      {
        id: 5,
        userId: 6,
        name: '辅导员',
        avatar: '导',
        color: 'avatar-orange',
        content: '请大家及时查看本周安排。',
        time: '周一 09:15',
      },
    ],
    members: [
      {
        userId: 6,
        name: '辅导员',
        avatar: '导',
        color: 'avatar-orange',
        role: '群主',
        online: true,
      },
      { userId: 1, color: 'avatar-blue', online: true },
      { userId: 4, name: '林晓', avatar: '林', color: 'avatar-purple', online: false },
    ],
  },
])

const currentGroup = computed(
  () => groups.value.find((group) => group.id === currentGroupId.value) ?? groups.value[0],
)

/**
 * 会话列表的显示顺序：**有未读的排到最上面**。
 *
 * ⚠️ 两个坑（都试过）：
 *   1. 不能直接 sort —— groups 里的 time 是「10:42 / 昨天 / 周一」这种展示文案，
 *      字符串排不了序。数据本身就是按时间倒序摆的，所以只做「稳定分区」：
 *      未读的一段 + 已读的一段，各自保持原相对顺序。
 *   2. 光按 unread 排会「一跳」：点开一个群就把它标已读（selectGroup），
 *      它立刻掉到下面去 —— 你正看着的那个会话突然跑了。
 *      所以把「当前选中的」也算进前面那一段，看着的会话就不会跳走。
 */
const sortedGroups = computed(() => {
  const sticky = (g) => g.unread > 0 || g.id === currentGroupId.value
  return [...groups.value.filter(sticky), ...groups.value.filter((g) => !sticky(g))]
})

function selectGroup(groupId) {
  currentGroupId.value = groupId
  const group = groups.value.find((item) => item.id === groupId)
  if (group) group.unread = 0
}

function appendEmoji(emoji) {
  draftMessage.value += emoji
  emojiPopoverVisible.value = false
}

/*
 * ---- AI 助手说「帮我在群里发一句…」时，真正动手的是这里 ----
 *
 * 群名和群列表只有这个组件知道（数据在组件内部），所以【匹配也在这里做】——
 * 服务端只递一个名字过来，不维护第二份群名表（这个项目吃过“同一份数据写两遍”的亏）。
 *
 * immediate 是为了处理「AI 先跳页再操作」：跳过来时暗号可能已经放好了。
 */
function findGroupByName(name) {
  if (!name) return null
  const key = String(name).trim()
  return (
    groups.value.find((group) => group.name === key) ??
    groups.value.find((group) => group.name.includes(key) || key.includes(group.name)) ??
    null
  )
}

watch(
  pendingCommand,
  async () => {
    const command = consumeCommand('chat')
    if (!command) return

    const group = findGroupByName(command.groupName)

    /*
     * ⚠️ AI 说了群名、这里却匹配不到 —— 【什么都不做】，不要退而求其次发到当前群。
     *    发错群比不发更糟：消息发出去撤不回来，而且是拿用户的名义发的。
     */
    if (command.groupName && !group) {
      ElMessage.warning(`没找到「${command.groupName}」这个群，先没动`)
      return
    }

    if (group && group.id !== currentGroupId.value) selectGroup(group.id)

    // 只是想看某个群，不发消息
    if (command.type === 'chat_open') return

    const text = String(command.text ?? '').trim()
    if (!text) return

    draftMessage.value = text
    await nextTick()

    if (command.type === 'chat_draft') {
      // 只说「写」就不发 —— 消息发出去撤不回来，最后一步留给用户按
      ElMessage.success('草稿已写好，改完按发送')
      return
    }

    await sendMessage()
    ElMessage.success('已发送')
  },
  { immediate: true },
)

async function sendMessage() {
  const content = draftMessage.value.trim()
  if (!content) return

  const group = currentGroup.value
  const groupId = group.id
  group.messages.push({
    id: Date.now(),
    userId: currentUser.value.id,
    content,
    time: new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  })
  group.preview = content
  group.time = '刚刚'
  draftMessage.value = ''

  await scrollToBottom()

  const timer = setTimeout(async () => {
    replyTimers.delete(timer)
    const replyGroup = groups.value.find((item) => item.id === groupId)
    if (!replyGroup) return

    replyGroup.messages.push({
      id: Date.now(),
      userId: 2,
      name: '用户A',
      avatar: 'A',
      color: 'avatar-green',
      content: '收到',
      time: new Date().toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    })
    replyGroup.preview = '收到'
    replyGroup.time = '刚刚'

    if (currentGroupId.value === groupId) {
      await scrollToBottom()
    } else {
      replyGroup.unread += 1
    }
  }, 800)
  replyTimers.add(timer)
}

async function scrollToBottom() {
  await nextTick()
  const wrap = messageScrollbar.value?.wrapRef
  const scrollElement = wrap?.value ?? wrap
  if (scrollElement) scrollElement.scrollTop = scrollElement.scrollHeight
}

onUnmounted(() => {
  replyTimers.forEach(clearTimeout)
  replyTimers.clear()
})
</script>

<style scoped>
.chat-view {
  display: grid;
  grid-template-columns: 260px minmax(360px, 1fr) 240px;
  height: min(760px, calc(100vh - 150px));
  min-height: 520px;
  overflow: hidden;
  background: var(--st-bg-card);
  border: 1px solid var(--st-border-color-light);
  border-radius: var(--st-radius-lg);
  box-shadow: var(--st-shadow-card);
}

.chat-sidebar,
.members-sidebar {
  display: flex;
  min-height: 0;
  flex-direction: column;
  background: var(--st-bg-card);
}

/* ---------- 入场：接全站那套（st-fade-up + --st-duration/ease 令牌）----------
   页面切换本身的淡入由 BasicLayout 的 <transition name="page"> 负责，
   这里补的是「进来之后三栏依次出现」和「消息逐条冒出来」。
   减少动效的兜底在 global.css（prefers-reduced-motion / .st-no-motion）。 */
.chat-sidebar {
  animation: st-fade-up var(--st-duration-slow) var(--st-ease) both;
}

.chat-main {
  animation: st-fade-up var(--st-duration-slow) var(--st-ease) both;
  animation-delay: 0.06s;
}

.members-sidebar {
  animation: st-fade-up var(--st-duration-slow) var(--st-ease) both;
  animation-delay: 0.12s;
}

.chat-sidebar {
  border-right: 1px solid var(--st-border-color-light);
}

.members-sidebar {
  border-left: 1px solid var(--st-border-color-light);
}

.sidebar-heading,
.members-heading,
.chat-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  padding: 18px 16px;
  border-bottom: 1px solid var(--st-border-color-light);
}

.sidebar-heading h2,
.members-heading h2,
.chat-title h2 {
  margin: 0;
  color: var(--st-text-primary);
  font-size: 16px;
  font-weight: 600;
}

.sidebar-heading p {
  margin: 5px 0 0;
  color: var(--st-text-secondary);
  font-size: 12px;
}

.group-scroll,
.members-scroll {
  flex: 1;
  min-height: 0;
}

.group-item {
  position: relative;
  display: flex;
  width: calc(100% - 16px);
  align-items: center;
  gap: 10px;
  margin: 8px;
  padding: 12px 10px;
  border: 0;
  border-radius: var(--st-radius-base);
  background: transparent;
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition:
    background-color var(--st-duration-fast) var(--st-ease),
    box-shadow var(--st-duration-fast) var(--st-ease);
  animation: st-fade-up var(--st-duration-base) var(--st-ease) both;
}

/* 群列表错峰：挨个冒出来（再多就不像动画，像卡了） */
.group-item:nth-child(1) {
  animation-delay: 0.1s;
}

.group-item:nth-child(2) {
  animation-delay: 0.16s;
}

.group-item:nth-child(3) {
  animation-delay: 0.22s;
}

.group-item:hover,
.group-item.is-active {
  background: var(--st-primary-light);
}

/* 选中项：左侧渐变竖条（和侧边栏菜单、区块标题同一套语言）。
   inset box-shadow 不支持渐变，所以用伪元素画。 */
.group-item.is-active::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 3px;
  height: 22px;
  background: var(--st-gradient-brand);
  border-radius: var(--st-radius-pill);
  transform: translateY(-50%);
}

.group-avatar,
.message-avatar,
.member-avatar {
  flex: 0 0 auto;
  color: var(--st-text-inverse);
  font-weight: 600;
}

.avatar-blue,
.self-avatar {
  background: var(--st-primary);
}

.avatar-green {
  background: var(--st-success);
}

.avatar-orange {
  background: var(--st-warning);
}

/* ⚠️ 原来这两个是写死的 #8b7bd8 / #42a99b，
 *    数值上就跟我那套色相令牌很像，但没走变量 —— 换主题时会被漏掉。
 *    现在直接指到调色板的 deep 档。 */
.avatar-purple {
  background: var(--tone-violet-deep);
}

.avatar-teal {
  background: var(--tone-teal-deep);
}

.avatar-gray {
  background: var(--st-info);
}

.group-info {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 7px;
}

.group-title-row,
.message-meta,
.member-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.group-title-row strong,
.member-info strong {
  overflow: hidden;
  color: var(--st-text-primary);
  font-size: 14px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-title-row time,
.group-preview,
.message-meta time {
  color: var(--st-text-secondary);
  font-size: 12px;
}

.group-preview {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unread-dot,
.online-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
}

.unread-dot {
  background: var(--st-danger);
  /* 新未读出现时弹一下 */
  animation: st-pop var(--st-duration-base) var(--st-ease-back) both;
}

.online-dot {
  background: var(--st-success);
}

.chat-main {
  display: flex;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  background: var(--st-bg-page);
}

.chat-header {
  background: var(--st-bg-card);
}

.chat-title span {
  display: inline-block;
  margin-top: 5px;
  color: var(--st-text-secondary);
  font-size: 12px;
}

.message-scroll {
  flex: 1;
  min-height: 0;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
}

.date-divider {
  align-self: center;
  padding: 5px 12px;
  color: var(--st-text-secondary);
  font-size: 12px;
  background: var(--st-bg-card);
  border-radius: 999px;
  animation: st-fade-in var(--st-duration-base) var(--st-ease) both;
}

.message-row {
  display: flex;
  max-width: 85%;
  align-items: flex-start;
  gap: 10px;
  /* 新消息插入时自动播；初次进页 / 切群时（列表按 currentGroupId 重建）也播一遍 */
  animation: chat-msg-in var(--st-duration-base) var(--st-ease) both;
}

/* 自己发的从右侧进来，更符合「消息是我推出去的」直觉 */
.message-row.is-self {
  align-self: flex-end;
  animation-name: chat-msg-in-self;
}

/* 前几条错峰，后面（包括刚发的新消息）立刻出现 */
.message-row:nth-child(2) {
  animation-delay: 0.03s;
}

.message-row:nth-child(3) {
  animation-delay: 0.06s;
}

.message-row:nth-child(4) {
  animation-delay: 0.09s;
}

.message-row:nth-child(5) {
  animation-delay: 0.12s;
}

@keyframes chat-msg-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}

@keyframes chat-msg-in-self {
  from {
    opacity: 0;
    transform: translate(10px, 6px);
  }
}

.message-content {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.message-meta strong {
  color: var(--st-text-regular);
  font-size: 12px;
  font-weight: 500;
}

.message-bubble {
  padding: 11px 14px;
  color: var(--st-text-primary);
  line-height: 1.6;
  overflow-wrap: anywhere;
  background: var(--st-bg-card);
  border-radius: 4px var(--st-radius-base) var(--st-radius-base) var(--st-radius-base);
  box-shadow: var(--st-shadow-card);
}

.is-self .message-bubble {
  color: #fff;
  background: var(--st-primary);
  border-radius: var(--st-radius-base) 4px var(--st-radius-base) var(--st-radius-base);
}

.composer {
  flex: 0 0 auto;
  padding: 10px 16px 14px;
  background: var(--st-bg-card);
  border-top: 1px solid var(--st-border-color-light);
}

.composer-tools,
.composer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.composer-tools {
  margin-bottom: 6px;
}

.emoji-picker {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
}

.emoji-option {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: var(--st-radius-sm);
  background: transparent;
  cursor: pointer;
  font: inherit;
  font-size: 20px;
}

.emoji-option:hover,
.emoji-option:focus-visible {
  background: var(--st-primary-light);
  outline: none;
}

.composer-tools span,
.composer-footer > span {
  color: var(--st-text-secondary);
  font-size: 12px;
}

.composer-footer {
  margin-top: 8px;
}

/* 发送按钮：品牌渐变（全站渐变只做点缀，这里是本页唯一的主操作） */
.chat-send {
  background-image: var(--st-gradient-brand);
  border-color: transparent;
  box-shadow: var(--st-shadow-grad);
}

.chat-send:hover,
.chat-send:focus {
  background-image: var(--st-gradient-brand);
  border-color: transparent;
  filter: brightness(1.07);
}

/* 输入为空时禁用：渐变和投影都撤掉，一眼能看出“现在发不了” */
.chat-send.is-disabled,
.chat-send.is-disabled:hover {
  background-image: none;
  box-shadow: none;
  filter: none;
}

.members-heading {
  gap: 8px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
}

.member-info {
  min-width: 0;
  flex: 1;
}

.member-role {
  padding: 2px 6px;
  color: var(--st-primary);
  font-size: 11px;
  background: var(--st-primary-light);
  border-radius: var(--st-radius-sm);
}

.member-status {
  color: var(--st-text-secondary);
  font-size: 11px;
}

.group-note {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 6px;
  padding: 14px 12px;
  color: var(--st-text-secondary);
  font-size: 12px;
  border-top: 1px solid var(--st-border-color-light);
}

@media (max-width: 1000px) {
  .chat-view {
    grid-template-columns: 230px minmax(320px, 1fr);
  }

  .members-sidebar {
    display: none;
  }
}

@media (max-width: 640px) {
  .chat-view {
    grid-template-columns: 76px minmax(0, 1fr);
    height: calc(100vh - 130px);
    min-height: 460px;
  }

  .sidebar-heading {
    justify-content: center;
    padding: 16px 6px;
  }

  .sidebar-heading > div,
  .sidebar-heading .el-button,
  .group-info,
  .group-item .unread-dot {
    display: none;
  }

  .group-item {
    justify-content: center;
    margin: 8px 4px;
    width: calc(100% - 8px);
    padding: 10px 4px;
  }

  .message-list {
    padding: 16px 10px;
  }

  .message-row {
    max-width: 96%;
    gap: 6px;
  }

  .message-avatar {
    width: 30px;
    height: 30px;
    font-size: 12px;
  }

  .composer {
    padding: 8px;
  }

  .composer-footer > span {
    display: none;
  }
}
</style>
