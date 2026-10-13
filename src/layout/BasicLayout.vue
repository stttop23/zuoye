<template>
  <el-container class="layout">
    <!-- ==================== 左侧菜单 ==================== -->
    <el-aside
      :width="isCollapse ? '64px' : '220px'"
      :class="['layout__aside', { 'is-collapsed': isCollapse }]"
    >
      <div class="layout__logo">
        <span class="layout__logo-mark">
          <el-icon :size="18"><School /></el-icon>
        </span>
        <span v-show="!isCollapse" class="layout__logo-text">学生工作管理系统</span>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        class="layout__menu"
      >
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- ==================== 顶栏 ==================== -->
      <el-header class="layout__header">
        <div class="layout__header-left">
          <el-icon class="layout__collapse-btn" :size="20" @click="isCollapse = !isCollapse">
            <component :is="isCollapse ? Expand : Fold" />
          </el-icon>

          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="layout__header-right">
          <!-- 通知中心：小铃铛 + 未读红点 -->
          <el-popover
            placement="bottom-end"
            :width="300"
            trigger="click"
            popper-class="notify-popper"
          >
            <template #reference>
              <span class="layout__bell-btn">
                <el-badge :value="unreadCount" :hidden="unreadCount === 0" :offset="[-2, 6]">
                  <el-icon :size="18"><Bell /></el-icon>
                </el-badge>
              </span>
            </template>

            <div class="notify">
              <div class="notify__head">
                <span>通知</span>
                <el-button v-if="unreadCount" link size="small" @click="markAllNotificationsRead">
                  全部已读
                </el-button>
              </div>
              <ul class="notify__list">
                <li
                  v-for="item in notifications"
                  :key="item.id"
                  :class="[
                    'notify__item',
                    { 'notify__item--unread': !isNotificationRead(item.id) },
                  ]"
                  @click="openNotification(item)"
                >
                  <div class="notify__title">{{ item.title }}</div>
                  <div v-if="item.content" class="notify__content">{{ item.content }}</div>
                  <div class="notify__time">{{ item.time }}</div>
                </li>
              </ul>
            </div>
          </el-popover>

          <el-select v-model="userRole" class="role-select" aria-label="切换用户身份">
            <el-option label="学生" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
          <el-tooltip content="修改显示名称">
            <el-button text class="profile-button" @click="openProfileDialog">
              <el-avatar :size="32" class="layout__avatar">{{ userInitial }}</el-avatar>
              <span class="profile-name">{{ userName }}</span>
              <el-icon><Edit /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </el-header>

      <!-- ==================== 内容区 ==================== -->
      <el-main class="layout__main">
        <!-- 切换页面时淡入淡出 + 轻微上移，比「啪」一下换掉有质感 -->
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>

    <!-- AI 助手：右下角悬浮窗，全站常驻，不属于任何一个页面 -->
    <AiAssistant />

    <el-dialog v-model="profileDialogVisible" title="修改显示名称" width="420px">
      <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" @submit.prevent>
        <el-form-item label="显示名称" prop="name">
          <el-input
            v-model="profileForm.name"
            maxlength="20"
            show-word-limit
            autofocus
            placeholder="输入你的名称"
            @keyup.enter="saveProfile"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Bell,
  ChatDotRound,
  Document,
  Edit,
  Expand,
  Fold,
  HomeFilled,
  List,
  School,
} from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import {
  isNotificationRead,
  markAllNotificationsRead,
  markNotificationRead,
  notifications,
  unreadCount,
} from '@/composables/notifications'
import AiAssistant from '@/components/AiAssistant.vue'

const route = useRoute()
const router = useRouter()
const { userName, userInitial, userRole } = useUserProfile()

/** 点通知：标记已读，并跳到对应页面 */
function openNotification(item) {
  markNotificationRead(item.id)
  if (item.path) router.push(item.path)
}

/** 侧边栏折叠状态 */
const isCollapse = ref(false)
const profileDialogVisible = ref(false)
const profileFormRef = ref()
const profileForm = reactive({ name: userName.value })
const profileRules = {
  name: [
    { required: true, whitespace: true, message: '请输入显示名称', trigger: 'blur' },
    { max: 20, message: '名称不能超过 20 个字符', trigger: 'blur' },
  ],
}

/** 菜单项：队友新增页面时，只需在这里加一行 */
const menus = [
  { path: '/assistant', title: 'AI 助手', icon: ChatDotRound },
  { path: '/dashboard', title: '工作台', icon: HomeFilled },
  { path: '/notice', title: '公告通知', icon: Bell },
  { path: '/leave', title: '请假申请', icon: Document },
  { path: '/todo', title: '待办事项', icon: List },
]

/** 面包屑第二级标题，直接读路由 meta */
const currentTitle = computed(() => route.meta?.title ?? '')

function openProfileDialog() {
  profileForm.name = userName.value
  profileDialogVisible.value = true
}

async function saveProfile() {
  try {
    await profileFormRef.value.validate()
  } catch {
    return
  }

  userName.value = profileForm.name.trim()
  profileDialogVisible.value = false
  ElMessage.success('显示名称已更新')
}
</script>

<style scoped>
.layout {
  height: 100%;
}

/* ---------- 侧边栏 ---------- */
.layout__aside {
  background: var(--st-gradient-sidebar);
  border-right: 1px solid var(--st-border-color-hair);
  transition: width var(--st-duration-base) var(--st-ease);
  overflow: hidden;
}

.layout__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--st-header-height);
  padding: 0 16px;
  white-space: nowrap;
  border-bottom: 1px solid var(--st-border-color-hair);
}

/* logo 图标做成一块渐变小方块，比裸图标有品牌感 */
.layout__logo-mark {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: #fff;
  background: var(--st-gradient-logo);
  border-radius: 10px;
  box-shadow: 0 4px 12px var(--st-primary-glow);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.layout__logo:hover .layout__logo-mark {
  transform: rotate(-8deg) scale(1.06);
}

.layout__logo-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}

/* ==================== 菜单 ==================== */
.layout__menu {
  padding: 8px 0;
  border-right: none;
  background: transparent;
}

/* 每个菜单项做成胶囊，悬停时往右轻轻挪一下 */
.layout__menu :deep(.el-menu-item) {
  position: relative;
  height: 44px;
  margin: 4px 10px;
  border-radius: var(--st-radius-sm);
  transition:
    background-color var(--st-duration-base) var(--st-ease),
    color var(--st-duration-base) var(--st-ease),
    transform var(--st-duration-base) var(--st-ease);
}

/* 左侧那根「长出来」的指示条 —— 用高度而非透明度，看着更利塔 */
.layout__menu :deep(.el-menu-item)::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -8px;
  width: 3px;
  height: 0;
  background: var(--st-primary);
  border-radius: var(--st-radius-pill);
  transform: translateY(-50%);
  transition: height var(--st-duration-base) var(--st-ease-back);
}

.layout__menu :deep(.el-menu-item.is-active)::before {
  height: 18px;
}

.layout__menu :deep(.el-menu-item:hover) {
  color: var(--st-primary);
  background: var(--st-primary-lighter);
  transform: translateX(3px);
}

.layout__menu :deep(.el-menu-item.is-active) {
  color: var(--st-primary);
  font-weight: 600;
  background: var(--st-primary-light);
}

.layout__menu :deep(.el-menu-item .el-icon) {
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.layout__menu :deep(.el-menu-item:hover .el-icon) {
  transform: scale(1.15);
}

/* 折叠的时候去掉左右外边距和指示条，不然图标会偏 */
.layout__aside.is-collapsed .layout__menu :deep(.el-menu-item) {
  margin: 4px 0;
}

.layout__aside.is-collapsed .layout__menu :deep(.el-menu-item)::before {
  display: none;
}

/* 折叠时内容居中由 EP 自己管，这里只把悬停位移取消，免得看着在抖 */
.layout__aside.is-collapsed .layout__menu :deep(.el-menu-item:hover) {
  transform: none;
}

/* ---------- 顶栏 ---------- */
.layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--st-header-height);
  background: var(--st-gradient-topbar);
  border-bottom: 1px solid var(--st-border-color-hair);
}

.layout__header-left {
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
}

.layout__collapse-btn {
  color: var(--st-text-regular);
  cursor: pointer;
  transition:
    transform var(--st-duration-base) var(--st-ease-back),
    color var(--st-duration-fast) var(--st-ease);
}

.layout__collapse-btn:hover {
  color: var(--st-primary);
  transform: scale(1.15);
}

.layout__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-select {
  width: 112px;
}

.layout__avatar {
  font-weight: 600;
  color: #fff;
  background: var(--st-gradient-brand);
  box-shadow: 0 4px 10px var(--st-primary-glow);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.profile-button:hover .layout__avatar {
  transform: scale(1.08);
}

.profile-button {
  display: inline-flex;
  align-items: center;
  gap: var(--st-gap-sm);
  height: 40px;
  color: var(--st-text-regular);
}

.profile-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 铃铛外面套一层，把点击区域撑大一点，免得小红点挡住点不到 */
.layout__bell-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 8px;
  color: var(--st-text-regular);
  border-radius: var(--st-radius-sm);
  cursor: pointer;
  transition:
    transform var(--st-duration-base) var(--st-ease-back),
    background-color var(--st-duration-fast) var(--st-ease),
    color var(--st-duration-fast) var(--st-ease);
}

/* 悬停时铃铛「歪一下」，有点小脾气 */
.layout__bell-btn:hover {
  color: var(--st-primary);
  background: var(--st-primary-lighter);
  transform: scale(1.08) rotate(-8deg);
}

.layout__bell-btn:active {
  transform: scale(0.96);
}

.layout__bell-btn:hover {
  color: var(--st-primary);
  background: var(--st-bg-page);
}

/* ---------- 内容区 ---------- */
.layout__main {
  padding: var(--st-gap-base);
  background: var(--st-bg-page);
}
</style>

<!--
  通知弹层被 teleport 到了 body，scoped 的样式够不到它，
  所以单独写一段不加 scoped 的，用 popper-class="notify-popper" 圈住范围。
-->
<style>
.notify__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 6px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.notify__list {
  max-height: 320px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}

.notify__item {
  padding: 8px 10px;
  margin: 0 -10px;
  border-radius: 6px;
  cursor: pointer;
}

.notify__item:hover {
  background: var(--st-bg-page);
}

/* 未读的左边有一小竖条 */
.notify__item--unread {
  border-left: 3px solid var(--st-primary);
  padding-left: 8px;
}

.notify__title {
  font-size: 14px;
  color: var(--st-text-primary);
}

.notify__content,
.notify__time {
  margin-top: 2px;
  font-size: 12px;
  color: var(--st-text-secondary);
}
</style>
