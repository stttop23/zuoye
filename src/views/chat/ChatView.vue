<template>
  <div class="chat-view">
    <aside class="chat-sidebar">
      <div class="sidebar-heading">
        <div>
          <h2>我的群聊</h2>
          <p>和伙伴保持联系</p>
        </div>
        <el-button circle plain aria-label="新建群聊" @click="openCreateGroupDialog">
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
        <el-button circle plain aria-label="更多群聊选项" @click="openGroupPanel">
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

  <el-drawer
    v-model="groupPanelVisible"
    append-to-body
    :with-header="false"
    size="min(420px, 100vw)"
    class="group-panel-drawer"
    @closed="resetGroupPanel"
  >
    <div class="group-panel">
      <header class="group-panel-header">
        <div>
          <span class="group-panel-eyebrow">群聊管理</span>
          <h2>群聊详情</h2>
        </div>
        <el-button circle plain aria-label="关闭群聊详情" @click="groupPanelVisible = false">
          <el-icon><Close /></el-icon>
        </el-button>
      </header>

      <section class="group-panel-section group-name-section">
        <div class="group-panel-section-heading">
          <h3>群聊名称</h3>
          <el-button
            v-if="!editingGroupName"
            text
            type="primary"
            aria-label="编辑群聊名称"
            @click="startRenameGroup"
          >
            <el-icon><EditPen /></el-icon>
            编辑
          </el-button>
        </div>
        <div v-if="editingGroupName" class="group-name-editor">
          <el-input
            v-model="groupNameDraft"
            maxlength="30"
            show-word-limit
            aria-label="新的群聊名称"
            @keydown.enter.prevent="saveGroupName"
            @keydown.esc="cancelRenameGroup"
          />
          <el-button type="primary" aria-label="保存群聊名称" @click="saveGroupName">
            <el-icon><Check /></el-icon>
          </el-button>
          <el-button aria-label="取消修改群聊名称" @click="cancelRenameGroup">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        <p v-else class="group-panel-current-name">{{ currentGroup.name }}</p>
      </section>

      <section class="group-panel-section">
        <div class="group-panel-section-heading">
          <h3>查找聊天记录</h3>
          <span class="group-panel-count">
            {{ historyQuery.trim() ? historyResults.length : currentGroup.messages.length }} 条
          </span>
        </div>
        <el-input
          v-model="historyQuery"
          clearable
          placeholder="搜索当前群聊消息"
          aria-label="搜索当前群聊聊天记录"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div v-if="historyQuery.trim()" class="history-results">
          <button
            v-for="message in historyResults"
            :key="message.id"
            type="button"
            class="history-result"
          >
            <span class="history-result-meta">
              <strong>{{ getMessageSenderName(message) }}</strong>
              <time>{{ message.time }}</time>
            </span>
            <span class="history-result-content">{{ message.content }}</span>
          </button>
          <el-empty
            v-if="historyResults.length === 0"
            description="没有找到相关聊天记录"
            :image-size="64"
          />
        </div>
        <p v-else class="group-panel-helper">输入关键词，搜索本群历史消息</p>
      </section>

      <section class="group-panel-section group-panel-members">
        <div class="group-panel-section-heading">
          <h3>群成员</h3>
          <span class="group-panel-count">{{ sortedCurrentMembers.length }} 人</span>
        </div>
        <el-scrollbar class="group-panel-member-scroll">
          <div class="group-panel-member-list">
            <div
              v-for="member in sortedCurrentMembers"
              :key="member.userId"
              class="group-panel-member"
            >
              <el-avatar :size="38" :class="['member-avatar', member.color]">
                {{ getMemberAvatar(member) }}
              </el-avatar>
              <div class="group-panel-member-info">
                <strong>{{ getMemberName(member) }}</strong>
                <span v-if="member.role === '群主'" class="owner-badge">群主</span>
              </div>
              <span
                v-if="member.online"
                class="online-dot"
                :aria-label="`${getMemberName(member)}在线`"
              ></span>
              <span v-else class="group-panel-offline">离线</span>
            </div>
          </div>
        </el-scrollbar>
      </section>

      <footer class="group-panel-footer">
        <el-button type="danger" plain class="leave-group-button" @click="leaveCurrentGroup">
          退出群聊
        </el-button>
      </footer>
    </div>
  </el-drawer>

  <el-dialog
    v-model="createGroupDialogVisible"
    title="创建群聊"
    width="min(520px, calc(100vw - 32px))"
    append-to-body
    @closed="resetCreateGroupDialog"
  >
    <p class="create-group-hint">选择要邀请的联系人</p>
    <el-checkbox-group v-model="selectedContactIds" class="create-group-contact-list">
      <el-checkbox
        v-for="contact in availableContacts"
        :key="contact.id"
        :value="contact.id"
        class="create-group-contact"
      >
        <el-avatar :size="38" class="create-group-avatar">
          {{ contact.name.slice(0, 1) }}
        </el-avatar>
        <span class="create-group-contact-info">
          <strong>{{ contact.name }}</strong>
          <span>{{ contact.department }} · {{ contact.role }}</span>
        </span>
      </el-checkbox>
    </el-checkbox-group>
    <el-empty
      v-if="availableContacts.length === 0"
      description="暂无可添加的联系人"
      :image-size="72"
    />
    <template #footer>
      <div class="create-group-footer">
        <span>已选择 {{ selectedContactIds.length }} 人</span>
        <div>
          <el-button @click="createGroupDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :disabled="selectedContactIds.length === 0 || creatingGroup"
            :loading="creatingGroup"
            @click="handleCreateGroup"
          >
            确定
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check,
  Close,
  EditPen,
  ElementPlus,
  InfoFilled,
  MoreFilled,
  Plus,
  Promotion,
  Search,
} from '@element-plus/icons-vue'
import { DIRECTORY_CONTACTS } from '@/mock'

const currentGroupId = ref('dev')
const draftMessage = ref('')
const messageScrollbar = ref(null)
const replyTimers = new Set()
const createGroupDialogVisible = ref(false)
const selectedContactIds = ref([])
const creatingGroup = ref(false)
const groupPanelVisible = ref(false)
const editingGroupName = ref(false)
const groupNameDraft = ref('')
const historyQuery = ref('')
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
    memberCount: 8,
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
    memberCount: 6,
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
    memberCount: 12,
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

const availableContacts = computed(() =>
  DIRECTORY_CONTACTS.filter((contact) => String(contact.id) !== String(currentUser.value.id)),
)

function openCreateGroupDialog() {
  selectedContactIds.value = []
  createGroupDialogVisible.value = true
}

function resetCreateGroupDialog() {
  selectedContactIds.value = []
  creatingGroup.value = false
}

async function createGroup(memberIds) {
  const selectedContacts = DIRECTORY_CONTACTS.filter((contact) =>
    memberIds.some((id) => String(id) === String(contact.id)),
  )
  if (selectedContacts.length === 0) {
    throw new Error('请选择至少一位联系人')
  }

  const names = selectedContacts.map((contact) => contact.name)
  const name =
    names.length <= 3
      ? `${names.join('、')}群`
      : `${names.slice(0, 2).join('、')}等${names.length}人群聊`
  const colors = ['avatar-green', 'avatar-orange', 'avatar-purple', 'avatar-teal']

  return {
    id: `group-${Date.now()}`,
    name,
    avatar: names
      .map((memberName) => memberName.slice(0, 1))
      .slice(0, 2)
      .join(''),
    color: 'avatar-blue',
    time: '刚刚',
    preview: '群聊已创建',
    unread: 0,
    memberCount: selectedContacts.length + 1,
    messages: [],
    members: [
      {
        userId: currentUser.value.id,
        color: 'avatar-blue',
        role: '群主',
        online: true,
      },
      ...selectedContacts.map((contact, index) => ({
        userId: contact.id,
        name: contact.name,
        avatar: contact.name.slice(0, 1),
        color: colors[index % colors.length],
        online: true,
      })),
    ],
  }
}

async function handleCreateGroup() {
  if (selectedContactIds.value.length === 0 || creatingGroup.value) return

  creatingGroup.value = true
  try {
    const newGroup = await createGroup([...selectedContactIds.value])
    groups.value.unshift(newGroup)
    currentGroupId.value = newGroup.id
    createGroupDialogVisible.value = false
    ElMessage.success('群聊创建成功')
  } catch (error) {
    console.error('创建群聊失败', error)
    ElMessage.error(error instanceof Error ? error.message : '创建群聊失败，请重试')
  } finally {
    creatingGroup.value = false
  }
}

const currentGroup = computed(
  () => groups.value.find((group) => group.id === currentGroupId.value) ?? groups.value[0],
)

const sortedCurrentMembers = computed(() =>
  [...currentGroup.value.members].sort(
    (first, second) => Number(second.role === '群主') - Number(first.role === '群主'),
  ),
)

const historyResults = computed(() => {
  const query = historyQuery.value.trim().toLocaleLowerCase()
  if (!query) return []

  return [...currentGroup.value.messages]
    .filter((message) =>
      `${message.content} ${getMessageSenderName(message)}`.toLocaleLowerCase().includes(query),
    )
    .reverse()
})

function openGroupPanel() {
  historyQuery.value = ''
  groupNameDraft.value = currentGroup.value.name
  editingGroupName.value = false
  groupPanelVisible.value = true
}

function resetGroupPanel() {
  historyQuery.value = ''
  groupNameDraft.value = ''
  editingGroupName.value = false
}

function startRenameGroup() {
  groupNameDraft.value = currentGroup.value.name
  editingGroupName.value = true
}

function cancelRenameGroup() {
  groupNameDraft.value = currentGroup.value.name
  editingGroupName.value = false
}

function saveGroupName() {
  const name = groupNameDraft.value.trim()
  if (!name) {
    ElMessage.warning('群聊名称不能为空')
    return
  }

  currentGroup.value.name = name
  currentGroup.value.avatar = name.slice(0, 2)
  editingGroupName.value = false
  ElMessage.success('群聊名称已更新')
}

function getMemberName(member) {
  return member.userId === currentUser.value.id ? currentUser.value.name : member.name
}

function getMemberAvatar(member) {
  return member.userId === currentUser.value.id ? currentUser.value.avatar : member.avatar
}

function getMessageSenderName(message) {
  return message.userId === currentUser.value.id ? currentUser.value.name : message.name || '群成员'
}

async function leaveCurrentGroup() {
  if (groups.value.length <= 1) {
    ElMessage.warning('至少保留一个群聊，暂时无法退出')
    return
  }

  try {
    await ElMessageBox.confirm('确认退出该群聊吗？退出后该群聊将从列表中移除。', '退出群聊', {
      confirmButtonText: '确认退出',
      cancelButtonText: '取消',
      type: 'warning',
      distinguishCancelAndClose: true,
    })
  } catch (action) {
    if (action === 'cancel' || action === 'close') return
    console.error('退出群聊确认失败', action)
    ElMessage.error('退出群聊失败，请重试')
    return
  }

  const leavingGroupId = currentGroup.value.id
  groups.value = groups.value.filter((group) => group.id !== leavingGroupId)
  currentGroupId.value = groups.value[0].id
  groupPanelVisible.value = false
  ElMessage.success('已退出群聊')
}

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
function selectGroup(groupId) {
  currentGroupId.value = groupId
  const group = groups.value.find((item) => item.id === groupId)
  if (group) group.unread = 0
}

function appendEmoji(emoji) {
  draftMessage.value += emoji
  emojiPopoverVisible.value = false
}

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
  color: #fff;
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

.avatar-purple {
  background: #8b7bd8;
}

.avatar-teal {
  background: #42a99b;
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

.create-group-hint {
  margin: 0 0 var(--st-gap-sm);
  color: var(--st-text-secondary);
  font-size: 13px;
}

.create-group-contact-list {
  display: flex;
  max-height: 360px;
  flex-direction: column;
  overflow: auto;
}

.create-group-contact {
  display: flex;
  width: 100%;
  min-height: 60px;
  align-items: center;
  gap: var(--st-gap-base);
  margin: 0;
  padding: var(--st-gap-sm) var(--st-gap-sm);
  border-bottom: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-sm);
  transition: background-color var(--st-duration-fast) var(--st-ease);
}

.create-group-contact:hover {
  background: var(--st-bg-hover);
}

.create-group-contact :deep(.el-checkbox__label) {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: var(--st-gap-base);
}

.create-group-avatar {
  flex: 0 0 auto;
  color: var(--st-primary);
  font-weight: 600;
  background: var(--st-primary-light);
}

.create-group-contact-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.create-group-contact-info strong {
  color: var(--st-text-primary);
  font-size: 14px;
  font-weight: 500;
}

.create-group-contact-info span {
  overflow: hidden;
  color: var(--st-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.create-group-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--st-gap-sm);
  color: var(--st-text-secondary);
  font-size: 12px;
}

.create-group-footer > div {
  display: flex;
  gap: var(--st-gap-sm);
}

.group-panel-drawer :deep(.el-drawer__body) {
  padding: 0;
  overflow: hidden;
}

.group-panel {
  display: flex;
  height: 100%;
  min-height: 0;
  flex-direction: column;
  color: var(--st-text-primary);
}

.group-panel-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  padding: 22px 24px 18px;
  border-bottom: 1px solid var(--st-border-color-light);
}

.group-panel-eyebrow {
  color: var(--st-primary);
  font-size: 12px;
  font-weight: 600;
}

.group-panel-header h2 {
  margin: 6px 0 0;
  font-size: 19px;
  font-weight: 600;
}

.group-panel-section {
  flex: 0 0 auto;
  padding: 18px 24px;
  border-bottom: 1px solid var(--st-border-color-light);
}

.group-panel-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.group-panel-section-heading h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.group-panel-count,
.group-panel-helper {
  color: var(--st-text-secondary);
  font-size: 12px;
}

.group-panel-current-name {
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 15px;
}

.group-name-editor {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-name-editor .el-input {
  min-width: 0;
  flex: 1;
}

.group-name-editor .el-button + .el-button {
  margin-left: 0;
}

.group-panel-helper {
  margin: 10px 0 0;
}

.history-results {
  max-height: 200px;
  margin-top: 8px;
  overflow-y: auto;
}

.history-result {
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: 6px;
  padding: 10px 8px;
  border: 0;
  border-bottom: 1px solid var(--st-border-color-hair);
  background: transparent;
  cursor: default;
  font: inherit;
  text-align: left;
}

.history-result-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.history-result-meta strong {
  color: var(--st-text-regular);
  font-size: 12px;
  font-weight: 600;
}

.history-result-meta time {
  flex: 0 0 auto;
  color: var(--st-text-secondary);
  font-size: 11px;
}

.history-result-content {
  overflow-wrap: anywhere;
  color: var(--st-text-primary);
  font-size: 13px;
  line-height: 1.5;
}

.group-panel-members {
  display: flex;
  min-height: 0;
  flex: 1 1 auto;
  flex-direction: column;
  border-bottom: 0;
}

.group-panel-member-scroll {
  min-height: 0;
  flex: 1;
}

.group-panel-member-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.group-panel-member {
  display: flex;
  min-height: 52px;
  align-items: center;
  gap: 10px;
}

.group-panel-member-info {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 8px;
}

.group-panel-member-info strong {
  overflow: hidden;
  font-size: 13px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.owner-badge {
  flex: 0 0 auto;
  padding: 2px 6px;
  color: var(--st-primary);
  font-size: 10px;
  background: var(--st-primary-light);
  border-radius: var(--st-radius-sm);
}

.group-panel-offline {
  color: var(--st-text-secondary);
  font-size: 11px;
}

.group-panel-footer {
  flex: 0 0 auto;
  padding: 16px 24px 22px;
  border-top: 1px solid var(--st-border-color-light);
}

.leave-group-button {
  width: 100%;
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
  .group-panel-header,
  .group-panel-section {
    padding-right: 18px;
    padding-left: 18px;
  }

  .group-panel-footer {
    padding-right: 18px;
    padding-left: 18px;
  }

  .create-group-footer {
    align-items: flex-start;
    flex-direction: column;
  }

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
