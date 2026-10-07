<template>
  <el-container class="layout">
    <!-- ==================== 左侧菜单 ==================== -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout__aside">
      <div class="layout__logo">
        <el-icon class="layout__logo-icon" :size="22"><School /></el-icon>
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
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>

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
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, Document, Edit, Expand, Fold, HomeFilled, List, School } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'

const route = useRoute()
const { userName, userInitial } = useUserProfile()

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
  background: var(--st-bg-card);
  border-right: 1px solid var(--st-border-color-light);
  transition: width 0.25s;
  overflow: hidden;
}

.layout__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--st-header-height);
  padding: 0 18px;
  color: var(--st-primary);
  white-space: nowrap;
  border-bottom: 1px solid var(--st-border-color-light);
}

.layout__logo-text {
  font-size: 15px;
  font-weight: 600;
}

.layout__menu {
  border-right: none;
}

/* ---------- 顶栏 ---------- */
.layout__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--st-header-height);
  background: var(--st-bg-card);
  border-bottom: 1px solid var(--st-border-color-light);
}

.layout__header-left {
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
}

.layout__collapse-btn {
  color: var(--st-text-regular);
  cursor: pointer;
}

.layout__collapse-btn:hover {
  color: var(--st-primary);
}

.layout__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.layout__avatar {
  background: var(--st-primary);
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

/* ---------- 内容区 ---------- */
.layout__main {
  padding: var(--st-gap-base);
  background: var(--st-bg-page);
}
</style>
