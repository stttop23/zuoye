<template>
  <el-container class="layout">
    <!-- 手机上侧边栏是盖在内容上的抽屉，后面垫一层遮罩，点一下就关 -->
    <!--
      包 <transition> 是为了**关的时候也能淡出**。
      之前只给遮罩写了入场 animation，v-if 一移除它就是「喷」一下消失：
      抽屉还在往回滑，背景已经亮回来了 —— 看着就像闪了一下。
    -->
    <transition name="mask">
      <div v-if="isMobile && mobileMenuOpen" class="layout__mask" @click="mobileMenuOpen = false" />
    </transition>

    <!-- ==================== 左侧菜单 ==================== -->
    <el-aside :width="sidebarWidth" :class="asideClass">
      <div class="layout__logo">
        <span class="layout__logo-mark">
          <el-icon :size="18"><School /></el-icon>
        </span>
        <span v-show="!sidebarCollapsed" class="layout__logo-text">学生工作管理系统</span>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
        class="layout__menu"
      >
        <el-menu-item
          v-for="item in menus"
          :key="item.path"
          :index="item.path"
          :class="`tone--${item.tone}`"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>

      <!-- ==================== 侧边栏底部：账号入口 ==================== -->
      <div class="layout__footer">
        <el-dropdown trigger="click" placement="top-start" @command="onAccountCommand">
          <button type="button" class="layout__account">
            <el-avatar :size="28" class="layout__avatar">{{ userInitial }}</el-avatar>
            <span v-show="!sidebarCollapsed" class="layout__account-name">{{ userName }}</span>
            <el-icon v-show="!sidebarCollapsed" class="layout__account-caret" :size="14">
              <ArrowDown />
            </el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">我的</el-dropdown-item>
              <el-dropdown-item command="settings">设置</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出账户</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-aside>

    <el-container>
      <!-- ==================== 顶栏 ==================== -->
      <el-header class="layout__header">
        <div class="layout__header-left">
          <!-- 电脑上：折叠成窄条；手机上：开/关闭抽屉 -->
          <el-icon
            class="layout__collapse-btn"
            :size="20"
            :aria-label="isMobile ? '打开菜单' : '折叠侧边栏'"
            @click="toggleSidebar"
          >
            <component :is="isMobile ? Menu : isCollapse ? Expand : Fold" />
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
                <el-badge
                  :value="unreadCount"
                  :hidden="unreadCount === 0 || !bellBadgeOn"
                  :offset="[-2, 6]"
                >
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
          <el-button text class="profile-button" @click="openProfileDialog">
            <el-avatar :size="32" class="layout__avatar">{{ userInitial }}</el-avatar>
            <span class="profile-name">{{ userName }}</span>
            <el-icon><Edit /></el-icon>
          </el-button>
        </div>
      </el-header>

      <!-- ==================== 内容区 ====================
           module--xxx ：告诉页面「你是哪个模块」，页面里的小横条/小竖条
           就自动变成这个模块的色相（变量定义在 global.css）。 -->
      <el-main class="layout__main" :class="moduleClass">
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

    <el-dialog v-model="profileDialogVisible" title="我的" width="420px">
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

        <el-form-item label="身份">
          <el-tag :type="isAdmin ? 'warning' : 'info'" effect="plain">
            {{ isAdmin ? '管理员' : '学生' }}
          </el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 设置：只放真会生效的开关，不摆假选项 -->
    <el-dialog v-model="settingsDialogVisible" title="设置" width="420px">
      <div class="setting-row">
        <span class="setting-row__label">界面动效</span>
        <el-switch v-model="motionOn" />
      </div>
      <div class="setting-row">
        <span class="setting-row__label">未读红点</span>
        <el-switch v-model="bellBadgeOn" />
      </div>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  Bell,
  ChatDotRound,
  Document,
  Edit,
  Expand,
  Fold,
  HomeFilled,
  List,
  Menu,
  School,
  User,
} from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import { useUiSettings } from '@/composables/uiSettings'
import { consumeCommand, pendingCommand } from '@/composables/aiAgent'
import { useIsMobile } from '@/composables/useMediaQuery'
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
const { userName, userInitial, userRole, isAdmin, resetProfile } = useUserProfile()
const { motionOn, bellBadgeOn } = useUiSettings()

/** 设置弹窗开关（侧边栏底部「设置」打开的） */
const settingsDialogVisible = ref(false)

/** 点通知：标记已读，并跳到对应页面 */
function openNotification(item) {
  markNotificationRead(item.id)
  if (item.path) router.push(item.path)
}

/** 侧边栏折叠状态（电脑上才有意义） */
const isCollapse = ref(false)

/* ============================================================
 * 移动端适配
 * ------------------------------------------------------------
 * 屏幕窄的时候，侧边栏不再是「折叠成窄条」，而是变成从左边滑出来的抽屉。
 * 因为手机上窄条菜单又占位置又点不准，盖在内容上更实用。
 *
 * 判断逻辑在 composables/useMediaQuery.js（公告页也用同一个断点）。
 * ============================================================ */
const isMobile = useIsMobile()
const mobileMenuOpen = ref(false)

// 回到电脑宽度就把抽屉收起来，不然会留个悬空状态
watch(isMobile, (窄) => {
  if (!窄) mobileMenuOpen.value = false
})

/** 手机上永远展开（抽屉里塞个窄条图标没有意义） */
const sidebarCollapsed = computed(() => !isMobile.value && isCollapse.value)
const sidebarWidth = computed(() => (sidebarCollapsed.value ? '64px' : '220px'))

/*
 * ⚠️ 这个 class 列表特意放在 computed 里，不在模板里直接写。
 *    因为 Vue 的模板编译器【不允许属性值里换行】：
 *      :class="[
 *        'a', { b: c },
 *      ]"
 *    会直接报 “Error parsing JavaScript expression”，整个页面白屏。
 *    而且这种错 get_errors / TS 检查都抓不到，只有跑起来才看得见。
 */
const asideClass = computed(() => [
  'layout__aside',
  {
    'is-collapsed': sidebarCollapsed.value,
    'is-mobile': isMobile.value,
    'is-open': mobileMenuOpen.value,
  },
])

/** 顶栏那个按钮：手机上开关抽屉，电脑上切换折叠 */
function toggleSidebar() {
  if (isMobile.value) mobileMenuOpen.value = !mobileMenuOpen.value
  else isCollapse.value = !isCollapse.value
}

/** 按 Esc 也能关掉抽屉 */
function onKeydown(event) {
  if (event.key === 'Escape' && mobileMenuOpen.value) mobileMenuOpen.value = false
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})

// 手机上点了菜单跳走之后，抽屉得自己收起来，不然会挡住新页面
watch(
  () => route.path,
  () => {
    mobileMenuOpen.value = false
  },
)

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
  /* tone = 这个菜单的色相（浅色彩虹：青→紫→粉）。
     侧边栏是深色的，所以图标用 light 档、选中竖条用 deep 档渐变 ——
     在 #1a2a42 上 soft 档基本看不见。 */
  { path: '/assistant', title: 'AI 助手', icon: ChatDotRound, tone: 'rainbow' },
  { path: '/dashboard', title: '工作台', icon: HomeFilled, tone: 'teal' },
  { path: '/notice', title: '公告通知', icon: Bell, tone: 'indigo' },
  { path: '/leave', title: '请假申请', icon: Document, tone: 'violet' },
  { path: '/todo', title: '待办事项', icon: List, tone: 'orchid' },
  { path: '/contacts', title: '通讯录', icon: User, tone: 'pink' },
]

/*
 * 内容区的模块色 class：global.css 里为每个色相定义了 --module-grad / ink / soft。
 * 用路由 name 拼（Dashboard → module--dashboard），小写就行。
 * 碰到没定义的（比如 404）只会挂一个空壳 class，使用处都有 fallback，不会白屏。
 */
const moduleClass = computed(() => {
  const name = String(route.name ?? '').toLowerCase()
  return name ? `module--${name}` : ''
})

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

/** 侧边栏底部那个入口点了哪一项（值写在模板的 command 上） */
function onAccountCommand(command) {
  if (command === 'profile') openProfileDialog()
  else if (command === 'settings') settingsDialogVisible.value = true
  else if (command === 'logout') logout()
}

/**
 * 退出账户。
 * 本地演示没有账号系统（没后端、没登录），“退出”就是把本地改过的身份恢复默认，
 * 然后退回工作台 —— 不然会停在一个“已退出”却还看着自己名字的奇怪状态。
 */
async function logout() {
  try {
    await ElMessageBox.confirm('本地保存的身份会恢复默认。', '退出账户', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return // 点了取消
  }

  resetProfile()
  router.push('/dashboard')
  ElMessage.success('已退出')
}

/*
 * ---- AI 助手：切换身份 / 改显示名称 / 开关设置 ----
 * 这三件事不依赖任何页面（侧边栏是全站常驻的），所以不用跳页就能干。
 */
watch(
  pendingCommand,
  () => {
    const command = consumeCommand('system')
    if (!command) return

    if (command.type === 'switch_role') {
      if (userRole.value === command.role) {
        ElMessage.info(command.role === 'admin' ? '现在就是管理员' : '现在就是学生')
        return
      }
      userRole.value = command.role
      ElMessage.success(command.role === 'admin' ? '已切到管理员' : '已切回学生')
      return
    }

    if (command.type === 'rename_user') {
      if (command.name === userName.value) {
        ElMessage.info('名字没变')
        return
      }
      userName.value = command.name
      ElMessage.success(`以后就叫你「${command.name}」`)
      return
    }

    if (command.type === 'toggle_setting') {
      const target = command.name === '界面动效' ? motionOn : bellBadgeOn
      if (target.value === command.value) {
        ElMessage.info(`${command.name}已经${command.value ? '开着' : '关着'}了`)
        return
      }
      target.value = command.value
      ElMessage.success(`${command.name}已${command.value ? '打开' : '关闭'}`)
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.layout {
  height: 100%;
  /*
   * 底色就用变量表里的页面灰，【不再叠径向光斑】。
   * 之前这里有两团很大的径向渐变（左上蓝、右上绿），看着很“亮”，但
   * 1) 径向大光斑是最容易显土的手法，和「克制、通透」相反；
   * 2) 它把白卡片的边界搅浑了，卡片反而不突出。
   * 现在让白卡片自己靠发丝边和柔影浮起来，背景干净就行。
   */
  background-color: var(--st-bg-page);
}

/* ---------- 侧边栏 ---------- */
.layout__aside {
  display: flex;
  flex-direction: column;
  background: var(--st-nav-bg);
  /*
   * ⚠️ 这条右边框【不能省】：侧边栏和内容区现在都是白的，
   *    没有它两块会连成一片，看不出导航到哪儿结束。
   */
  border-right: 1px solid var(--st-nav-border);
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
  border-bottom: 1px solid var(--st-nav-divider);
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
  /* 菜单占满剩下的高度，把底部的账号入口顶到最下面 */
  flex: 1;
  min-height: 0;
  overflow-y: auto;
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

/* 左侧那根「长出来」的指示条 —— 用高度而非透明度，看着更利落 */
.layout__menu :deep(.el-menu-item)::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -8px;
  width: 3px;
  height: 0;
  /* 选中条用【本菜单自己的色相】—— 六个菜单就是一段青→紫→粉的小彩虹 */
  background: var(--menu-grad, var(--grad-blue));
  border-radius: var(--st-radius-pill);
  transform: translateY(-50%);
  transition: height var(--st-duration-base) var(--st-ease-back);
}

/*
 * 每个菜单项自己的三个变量（模板里挂的 tone--xxx）：
 *   --menu-grad  选中竖条的颜色（deep 档渐变）
 *   --menu-tone  图标颜色
 *   --menu-wash  悬停 / 选中的底色
 *
 * ⚠️ 侧边栏改成【白底】之后，图标必须用 deep 档 ——
 *    原来读的是 light 档（#86c9c1 那种），那是配深海军蓝才够亮的颜色，
 *    放白底上几乎看不清。
 */
.layout__menu :deep(.el-menu-item.tone--teal) {
  --menu-grad: var(--grad-teal);
  --menu-tone: var(--tone-teal-deep);
  --menu-wash: var(--tone-teal-fade);
}

.layout__menu :deep(.el-menu-item.tone--indigo) {
  --menu-grad: var(--grad-indigo);
  --menu-tone: var(--tone-indigo-deep);
  --menu-wash: var(--tone-indigo-fade);
}

.layout__menu :deep(.el-menu-item.tone--violet) {
  --menu-grad: var(--grad-violet);
  --menu-tone: var(--tone-violet-deep);
  --menu-wash: var(--tone-violet-fade);
}

.layout__menu :deep(.el-menu-item.tone--orchid) {
  --menu-grad: var(--grad-orchid);
  --menu-tone: var(--tone-orchid-deep);
  --menu-wash: var(--tone-orchid-fade);
}

.layout__menu :deep(.el-menu-item.tone--pink) {
  --menu-grad: var(--grad-pink);
  --menu-tone: var(--tone-pink-deep);
  --menu-wash: var(--tone-pink-fade);
}

.layout__menu :deep(.el-menu-item.tone--rainbow) {
  --menu-grad: var(--grad-rainbow);
  --menu-tone: var(--tone-violet-deep);
  --menu-wash: var(--tone-violet-fade);
}

.layout__menu :deep(.el-menu-item.is-active)::before {
  height: 18px;
}

/* 白底上的菜单：默认中灰，悬停/选中变深。
   悬停 / 选中的底色用【本菜单自己的浅色】—— 白侧边栏也能看出那抹彩虹。 */
.layout__menu :deep(.el-menu-item) {
  color: var(--st-nav-text);
}

.layout__menu :deep(.el-menu-item:hover) {
  color: var(--st-nav-text-active);
  background: var(--menu-wash, var(--st-nav-hover-bg));
  transform: translateX(3px);
}

.layout__menu :deep(.el-menu-item.is-active) {
  color: var(--st-nav-text-active);
  font-weight: 600;
  background: var(--menu-wash, var(--st-nav-active-bg));
}

/* 图标带本菜单的色相 —— 侧边栏一眼就是一小段彩虹 */
.layout__menu :deep(.el-menu-item .el-icon) {
  color: var(--menu-tone, currentcolor);
  transition:
    color var(--st-duration-base) var(--st-ease),
    transform var(--st-duration-base) var(--st-ease-back);
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

/* ---------- 侧边栏底部：账号入口 ---------- */
.layout__footer {
  padding: 8px 10px 12px;
  border-top: 1px solid var(--st-nav-divider);
}

.layout__account {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px;
  border: 0;
  border-radius: var(--st-radius-sm);
  background: transparent;
  color: var(--st-nav-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    background-color var(--st-duration-base) var(--st-ease),
    color var(--st-duration-base) var(--st-ease);
}

.layout__account:hover {
  color: var(--st-nav-text-active);
  background: var(--st-nav-hover-bg);
}

.layout__account-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.layout__account-caret {
  color: var(--st-nav-text);
  opacity: 0.7;
}

/* 折叠成窄条时只留头像，居中放 */
.layout__aside.is-collapsed .layout__account {
  justify-content: center;
  padding: 8px 0;
}

/* 设置弹窗里的一行：左边名字、右边开关 */
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
}

.setting-row + .setting-row {
  border-top: 1px solid var(--st-border-color-hair);
}

.setting-row__label {
  color: var(--st-text-primary);
  font-size: 14px;
}

/* ---------- 顶栏 ---------- */
.layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--st-header-height);
  background: var(--st-gradient-topbar);
  /* 和侧边栏右边框同一根线：白底白底靠它划开，不能更淡了 */
  border-bottom: 1px solid var(--st-nav-border);
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
  /* 加到 20px：清新系的观感一半靠留白，内容贴着浏览边会显挤 */
  padding: 20px;
  /* 透明，让 .layout 上的底色透出来 */
  background: transparent;
}

/* ============================================================
   移动端
   ------------------------------------------------------------
   断点就一个：768px。低于它侧边栏变成抽屉。
   只改布局与间隔，不动任何业务逻辑。
   ============================================================ */

/*
 * 手机端抽屉的遮罩（点一下就关）。
 * ⚠️ 层级必须夹在中间：浮球（1500）< 遮罩（1700）< 抽屉（1800）< Element Plus 浮层（2000 起）。
 * 原来写的是 2000 / 2100，结果**抽屉里点出来的下拉菜单被抽屉自己盖住了**
 * （EP 下拉实测 z-index 2024 < 2100）—— 看着就是「点了没反应」。
 * 注意 EP 的浮层是从 2000 开始递增的，所以这两个值只能比 2000 小。
 */
.layout__mask {
  position: fixed;
  inset: 0;
  z-index: 1700;
  background: rgba(16, 42, 82, 0.42);
  backdrop-filter: blur(2px);
}

/* 进出都淡，且和抽屉同时结束 —— 两边节奏一样才不会看着“闪” */
.mask-enter-active,
.mask-leave-active {
  transition: opacity var(--st-duration-drawer) var(--st-ease);
}

.mask-enter-from,
.mask-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  /* 侧边栏改成从左侧滑出的抽屉，盖在内容上（fixed 之后不再占宽度） */
  .layout__aside.is-mobile {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 1800;
    width: 220px !important;
    transform: translateX(-100%);
    transition: transform var(--st-duration-drawer) var(--st-ease);
    box-shadow: var(--st-shadow-float);
  }

  .layout__aside.is-mobile.is-open {
    transform: translateX(0);
  }

  .layout__header {
    padding: 0 12px;
  }

  .layout__main {
    padding: var(--st-gap-md);
  }
}

/* 更窄一点：名字收起来只留头像，角色下拉做窄些 */
@media (max-width: 640px) {
  .profile-name {
    display: none;
  }

  .role-select {
    width: 92px;
  }
}

/* 再窄：面包屑也没地方放了，直接隐藏（侧边栏里本来就能看到当前在哪） */
@media (max-width: 480px) {
  .layout__header-left :deep(.el-breadcrumb) {
    display: none;
  }
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
