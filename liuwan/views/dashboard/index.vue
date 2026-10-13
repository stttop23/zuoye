<template>
  <div class="dashboard">
    <!-- ==================== 欢迎条 ==================== -->
    <el-card shadow="never" class="welcome st-fade-up">
      <div class="welcome__inner">
        <el-avatar :size="56" class="welcome__avatar">{{ userInitial }}</el-avatar>
        <div>
          <h2 class="welcome__title">欢迎来到工作台，{{ userName }}</h2>
          <p class="welcome__desc">{{ todayText }}</p>
        </div>
      </div>
    </el-card>

    <!-- 下面几块挨个淡入上移，带一点节奏（.st-delay-N 在 global.css 里） -->
    <CheckIn class="st-fade-up st-delay-1" />

    <StatCards :stats="stats" />

    <QuickActions class="st-fade-up st-delay-3" @navigate="onNavigate" @refresh="onRefresh" />

    <RecentNotices
      class="st-fade-up st-delay-4"
      :notices="recentNotices"
      @view-all="onNavigate('/notice')"
    />
  </div>
</template>

<script setup>
/**
 * ⚠️ 当前全部使用「假数据」，前端可以独立开发。
 * 后端接口就绪后，把 data 换成 axios 请求即可，页面结构不用动。
 *
 * 本页已拆成四个子组件，都在 ./components/ 下：
 * CheckIn（每日打卡）、StatCards（数据卡片）、QuickActions（快捷入口）、RecentNotices（最新公告）
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, List, User, Warning } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import { dashboardSummary, latestNotices } from '@/composables/appStore'
import CheckIn from './components/CheckIn.vue'
import StatCards from './components/StatCards.vue'
import QuickActions from './components/QuickActions.vue'
import RecentNotices from './components/RecentNotices.vue'

const router = useRouter()
const { userName, userInitial } = useUserProfile()

/**
 * 四个数字全部从 @/composables/appStore 里【数出来】，不再手写。
 * 以前这里是写死的 {todo:5, leave:2, notice:3, member:4}，
 * 而公告页实际有 12 条、待办页有 6 条 —— 首页和页面直接对不上。
 * 现在它和页面共用同一份数据，所以在待办页删一条、发一条公告，这里立刻跟着变。
 */
const summary = computed(() => dashboardSummary())

const stats = computed(() => [
  {
    label: '待办事项',
    value: summary.value.todo,
    icon: List,
    color: 'var(--st-primary)',
    bg: 'var(--st-primary-light)',
  },
  {
    label: '请假申请',
    value: summary.value.leave,
    icon: Document,
    color: 'var(--st-warning)',
    bg: '#fdf6ec',
  },
  {
    label: '公告数量',
    value: summary.value.notice,
    icon: Warning,
    color: 'var(--st-danger)',
    bg: '#fef0f0',
  },
  {
    label: '小组成员',
    value: summary.value.member,
    icon: User,
    color: 'var(--st-success)',
    bg: '#f0f9eb',
  },
])

/**
 * 最新公告：直接从公告页那份数据里取前 3 条（同一份，所以在公告页发一条，这里马上就有）。
 * 以前首页另手写了一份，结果「校园文化活动报名开始啦」
 * 首页写 09-20、公告页写 10-01 —— 同一个活动两个日期。
 */
const recentNotices = computed(() => latestNotices(3))

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

/**
 * 「刷新数据」：现在没有后端可请求，而上面的数字本来就是实时算出来的，
 * 所以这里只报个到。
 * ⚠️ 以前这里写的是 data.value.todo = Math.random()*10 —— 点一下数字变一个随机值，
 * 老师点一下就穿帮了。宁可什么都不做，也别造假。
 */
function onRefresh() {
  ElMessage.success('数据已是最新')
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--st-gap-base);
}

/* ---------- 欢迎条：做成一块主视觉，不要一片死白 ---------- */
.welcome {
  position: relative;
  overflow: hidden;
  border: none;
  color: #fff;
  background: linear-gradient(120deg, #2b7cd3 0%, #409eff 48%, #66b1ff 100%);
  box-shadow: 0 12px 32px rgba(64, 158, 255, 0.28);
}

/* 两个半透明装饰圆：直线条里掺点弧线，整块就不呆
   ⚠️ ::before / ::after 会盖在内容上（绝对定位的元素在普通内容之上），
      所以下面 .welcome__inner 要给 z-index 提上来 */
.welcome::before,
.welcome::after {
  content: '';
  position: absolute;
  background: rgba(255, 255, 255, 0.09);
  border-radius: 50%;
  pointer-events: none;
}

.welcome::before {
  top: -90px;
  right: 60px;
  width: 240px;
  height: 240px;
}

.welcome::after {
  right: -60px;
  bottom: -110px;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.13);
}

.welcome__inner {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
}

.welcome__avatar {
  flex-shrink: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(4px);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.welcome:hover .welcome__avatar {
  transform: scale(1.06) rotate(-4deg);
}

.welcome__title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.welcome__desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}

/* 数据卡片、区块的样式已随子组件移走，见 ./components/ */
</style>
