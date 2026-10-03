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
          <el-tag type="info" effect="plain" round>前端开发：刘皖</el-tag>
          <el-avatar :size="32" class="layout__avatar">刘</el-avatar>
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
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Bell, Document, Expand, Fold, HomeFilled, List, School } from '@element-plus/icons-vue'

const route = useRoute()

/** 侧边栏折叠状态 */
const isCollapse = ref(false)

/** 菜单项：队友新增页面时，只需在这里加一行 */
const menus = [
  { path: '/dashboard', title: '工作台', icon: HomeFilled },
  { path: '/notice', title: '公告通知', icon: Bell },
  { path: '/leave', title: '请假申请', icon: Document },
  { path: '/todo', title: '待办事项', icon: List },
]

/** 面包屑第二级标题，直接读路由 meta */
const currentTitle = computed(() => route.meta?.title ?? '')
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

/* ---------- 内容区 ---------- */
.layout__main {
  padding: var(--st-gap-base);
  background: var(--st-bg-page);
}
</style>
