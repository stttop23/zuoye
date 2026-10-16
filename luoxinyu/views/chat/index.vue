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
          v-for="group in groups"
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
          <span>{{ currentGroup.memberCount }} 位成员</span>
        </div>
        <el-button circle plain aria-label="更多群聊选项">
          <el-icon><MoreFilled /></el-icon>
        </el-button>
      </header>

      <el-scrollbar ref="messageScrollbar" class="message-scroll">
        <div class="message-list">
          <div class="date-divider"><span>今天</span></div>
          <div
            v-for="message in currentGroup.messages"
            :key="message.id"
            class="message-row"
            :class="{ 'is-self': message.isSelf }"
          >
            <el-avatar v-if="!message.isSelf" :size="38" :class="['message-avatar', message.color]">
              {{ message.avatar }}
            </el-avatar>
            <div class="message-content">
              <div class="message-meta">
                <strong>{{ message.isSelf ? '我' : message.name }}</strong>
                <time>{{ message.time }}</time>
              </div>
              <div class="message-bubble">{{ message.content }}</div>
            </div>
            <el-avatar v-if="message.isSelf" :size="38" class="message-avatar self-avatar">
              我
            </el-avatar>
          </div>
        </div>
      </el-scrollbar>

      <div class="composer">
        <div class="composer-tools">
          <el-button text aria-label="表情">
            <el-icon><ElementPlus /></el-icon>
          </el-button>
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
          <el-button type="primary" :disabled="!draftMessage.trim()" @click="sendMessage">
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
          <div v-for="member in currentGroup.members" :key="member.name" class="member-item">
            <el-avatar :size="38" :class="['member-avatar', member.color]">
              {{ member.avatar }}
            </el-avatar>
            <div class="member-info">
              <strong>{{ member.name }}</strong>
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
import { computed, nextTick, onUnmounted, ref } from 'vue'
import { ElementPlus, InfoFilled, MoreFilled, Plus, Promotion } from '@element-plus/icons-vue'

const currentGroupId = ref('dev')
const draftMessage = ref('')
const messageScrollbar = ref(null)
const replyTimers = new Set()

const groups = ref([
  {
    id: 'dev',
    name: '开发1群',
    avatar: '开',
    color: 'avatar-blue',
    time: '10:42',
    preview: '我在写代码，稍等。',
    unread: 2,
    memberCount: 8,
    messages: [
      {
        id: 1,
        name: '用户A',
        avatar: 'A',
        color: 'avatar-green',
        content: '大家今天打卡了吗？',
        time: '10:30',
      },
      {
        id: 2,
        name: '用户B',
        avatar: 'B',
        color: 'avatar-orange',
        content: '打卡了，今天有什么任务安排？',
        time: '10:34',
      },
      {
        id: 3,
        name: '我',
        avatar: '我',
        color: 'avatar-blue',
        content: '我在写代码，稍等。',
        time: '10:42',
        isSelf: true,
      },
    ],
    members: [
      { name: '刘皖', avatar: '刘', color: 'avatar-blue', role: '群主', online: true },
      { name: '用户A', avatar: 'A', color: 'avatar-green', online: true },
      { name: '用户B', avatar: 'B', color: 'avatar-orange', online: true },
      { name: '林晓', avatar: '林', color: 'avatar-purple', online: false },
      { name: '陈宇', avatar: '陈', color: 'avatar-teal', online: true },
      { name: '我', avatar: '我', color: 'avatar-gray', online: true },
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
    memberCount: 6,
    messages: [
      {
        id: 4,
        name: '林晓',
        avatar: '林',
        color: 'avatar-purple',
        content: '周五我们一起确认方案吧。',
        time: '昨天 16:20',
      },
    ],
    members: [
      { name: '刘皖', avatar: '刘', color: 'avatar-blue', role: '群主', online: true },
      { name: '林晓', avatar: '林', color: 'avatar-purple', online: true },
      { name: '陈宇', avatar: '陈', color: 'avatar-teal', online: false },
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
    memberCount: 12,
    messages: [
      {
        id: 5,
        name: '辅导员',
        avatar: '导',
        color: 'avatar-orange',
        content: '请大家及时查看本周安排。',
        time: '周一 09:15',
      },
    ],
    members: [
      { name: '辅导员', avatar: '导', color: 'avatar-orange', role: '群主', online: true },
      { name: '刘皖', avatar: '刘', color: 'avatar-blue', online: true },
      { name: '林晓', avatar: '林', color: 'avatar-purple', online: false },
    ],
  },
])

const currentGroup = computed(
  () => groups.value.find((group) => group.id === currentGroupId.value) ?? groups.value[0],
)

function selectGroup(groupId) {
  currentGroupId.value = groupId
  const group = groups.value.find((item) => item.id === groupId)
  if (group) group.unread = 0
}

async function sendMessage() {
  const content = draftMessage.value.trim()
  if (!content) return

  const group = currentGroup.value
  const groupId = group.id
  group.messages.push({
    id: Date.now(),
    name: '我',
    avatar: '我',
    color: 'avatar-blue',
    content,
    time: new Date().toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    isSelf: true,
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
  transition: background-color 0.2s;
}

.group-item:hover,
.group-item.is-active {
  background: var(--st-primary-light);
}

.group-item.is-active {
  box-shadow: inset 3px 0 var(--st-primary);
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
}

.message-row {
  display: flex;
  max-width: 85%;
  align-items: flex-start;
  gap: 10px;
}

.message-row.is-self {
  align-self: flex-end;
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

.composer-tools span,
.composer-footer > span {
  color: var(--st-text-secondary);
  font-size: 12px;
}

.composer-footer {
  margin-top: 8px;
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
