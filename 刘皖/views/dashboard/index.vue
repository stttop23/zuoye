<template>
  <div class="dashboard">
    <!-- ==================== 欢迎条 ==================== -->
    <el-card shadow="never" class="welcome">
      <div class="welcome__inner">
        <el-avatar :size="56" class="welcome__avatar">{{ userInitial }}</el-avatar>
        <div>
          <h2 class="welcome__title">欢迎来到工作台，{{ userName }}</h2>
          <p class="welcome__desc">{{ todayText }} · 今天也要元气满满哦</p>
        </div>
      </div>
    </el-card>

    <!-- ==================== 数据卡片（子组件） ==================== -->
    <StatCards :stats="stats" />

    <!-- ==================== 快捷入口（子组件） ==================== -->
    <QuickActions @navigate="onNavigate" @refresh="onRefresh" />

    <!-- ==================== 最新公告（子组件） ==================== -->
    <RecentNotices :notices="recentNotices" @view-all="onNavigate('/notice')" />
  </div>
</template>

<script setup>
/**
 * ⚠️ 当前全部使用「假数据」，前端可以独立开发。
 * 后端接口就绪后，把 data 换成 axios 请求即可，页面结构不用动。
 *
 * 本页已拆成三个子组件，都在 ./components/ 下：
 * StatCards（数据卡片）、QuickActions（快捷入口）、RecentNotices（最新公告）
 */
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, List, User, Warning } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import StatCards from './components/StatCards.vue'
import QuickActions from './components/QuickActions.vue'
import RecentNotices from './components/RecentNotices.vue'

const router = useRouter()
const { userName, userInitial } = useUserProfile()

/** 假数据：统计数据 */
const data = ref({
  todo: 5,
  leave: 2,
  notice: 3,
  member: 4,
})

const stats = computed(() => [
  {
    label: '待办事项',
    value: data.value.todo,
    icon: List,
    color: 'var(--st-primary)',
    bg: 'var(--st-primary-light)',
  },
  {
    label: '请假申请',
    value: data.value.leave,
    icon: Document,
    color: 'var(--st-warning)',
    bg: '#fdf6ec',
  },
  {
    label: '公告数量',
    value: data.value.notice,
    icon: Warning,
    color: 'var(--st-danger)',
    bg: '#fef0f0',
  },
  {
    label: '小组成员',
    value: data.value.member,
    icon: User,
    color: 'var(--st-success)',
    bg: '#f0f9eb',
  },
])

/** 假数据：最新公告 */
const recentNotices = ref([
  { id: 3, title: '关于期末学生工作总结的通知', publishTime: '2026-10-02 09:15', top: true },
  { id: 2, title: '学生会例会时间调整说明', publishTime: '2026-09-28 16:40', top: false },
  { id: 1, title: '校园文化活动报名开始啦', publishTime: '2026-09-20 10:00', top: false },
])

const todayText = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }),
)

/** 快捷入口里的按钮点的是哪个路由，统一在这里做 */
function onNavigate(path) {
  router.push(path)
}

/** 模拟刷新：数字随机变一下，方便答辩演示 */
function onRefresh() {
  data.value.todo = Math.floor(Math.random() * 10) + 1
  ElMessage.success('数据已刷新')
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--st-gap-base);
}

/* ---------- 欢迎条 ---------- */
.welcome {
  border: none;
  background: linear-gradient(90deg, #ecf5ff 0%, #ffffff 60%);
}

.welcome__inner {
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
}

.welcome__avatar {
  background: var(--st-primary);
  font-size: 20px;
}

.welcome__title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.welcome__desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--st-text-secondary);
}

/* 数据卡片、区块的样式已随子组件移走，见 ./components/ */
</style>
