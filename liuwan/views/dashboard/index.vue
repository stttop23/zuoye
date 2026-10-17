<template>
  <div class="dashboard">
    <!-- ==================== 欢迎卡（全页唯一一张用渐变的卡） ==================== -->
    <el-card shadow="never" class="welcome st-fade-up">
      <div class="welcome__inner">
        <div class="welcome__left">
          <el-avatar :size="56" class="welcome__avatar">{{ userInitial }}</el-avatar>
          <div>
            <h2 class="welcome__title">欢迎来到工作台，{{ userName }}</h2>
            <p class="welcome__desc">{{ todayText }}</p>
          </div>
        </div>
        <!--
          打卡也放进这张卡：它是工作台上唯一的「动作」，
          而且卡片本来就空着一大块右侧。单独开一张卡反而显得散。
        -->
        <CheckIn />
      </div>
    </el-card>

    <!-- 管理员才算总账：全组今天谁打了、几点、在哪 -->
    <TeamCheckIn v-if="isAdmin" />

    <!-- 下面几块挨个淡入上移，带一点节奏（.st-delay-N 在 global.css 里） -->
    <StatCards :stats="stats" @navigate="onNavigate" />

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
 * TeamCheckIn（管理员的全组打卡）也在这里，只在管理员身份下渲染。
 */
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, List, User, Warning } from '@element-plus/icons-vue'
import { useUserProfile } from '@/composables/userProfile'
import {
  dashboardSummary,
  latestNotices,
  leaveRecords,
  notices,
  todos,
} from '@/composables/appStore'
import { DIRECTORY_CONTACTS } from '@/mock'
import CheckIn from './components/CheckIn.vue'
import TeamCheckIn from './components/TeamCheckIn.vue'
import StatCards from './components/StatCards.vue'
import QuickActions from './components/QuickActions.vue'
import RecentNotices from './components/RecentNotices.vue'

const router = useRouter()
const { userName, userInitial, isAdmin } = useUserProfile()

/**
 * 四个数字全部从 @/composables/appStore 里【数出来】，不再手写。
 * 以前这里是写死的 {todo:5, leave:2, notice:3, member:4}，
 * 而公告页实际有 12 条、待办页有 6 条 —— 首页和页面直接对不上。
 * 现在它和页面共用同一份数据，所以在待办页删一条、发一条公告，这里立刻跟着变。
 */
const summary = computed(() => dashboardSummary())

/** 今天的 'YYYY-MM-DD'。⚠️ 用本地时间拼，别用 toISOString —— 那是 UTC，晚上会差一天 */
function todayStr() {
  const d = new Date()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

/** 未完成 + 截止日已过 = 逾期。（字符串直接比大小，'YYYY-MM-DD' 比日期对象省事） */
function isOverdue(todo, today) {
  return todo.status !== '已完成' && todo.dueDate && todo.dueDate < today
}

/** 'YYYY-MM-DD HH:mm' → 距今天几天。解析不出来就返回 0 */
function daysSince(dateTime, today) {
  if (!dateTime) return 0
  const day = String(dateTime).slice(0, 10)
  const diff = (new Date(today) - new Date(day)) / 86400000
  return Number.isFinite(diff) ? Math.max(0, Math.round(diff)) : 0
}

/**
 * 四张统计卡：**内容按角色不一样**（学生看自己的，管理员看全局）。
 *
 * ⚠️ 为什么必须分：工作台只回答一个问题 ——「我现在该干嘛」。
 *    这个问题的答案两个角色完全不同：学生关心“我的假批了没”，
 *    管理员关心“有几个人在等我批”。同一排放四张一样的卡等于没答。
 *
 * ⚠️ 但【数字必须和点进去那个页面一致】，否则就是老毛病（首页和页面对不上）：
 *    - 待办页**不按人过滤**（两边都看到全部）→ 卡片给总数
 *    - 请假页【按人过滤】（学生只看自己的，管理员看全部）→ 卡片必须跟着分
 *      以前学生首页写 4、点进去只有 1 行，就是这个不一致。
 *
 * tone = 卡片色相（只为好看，不跟模块色绑定）
 * sub  = 底下一行小字，⚠️ 必须是从数据里算出来的真数字，宁可写“无逾期”也别编
 * path = 点这张卡跳到哪儿
 */
const stats = computed(() => {
  const today = todayStr()
  const overdue = todos.value.filter((t) => isOverdue(t, today)).length
  const allPending = leaveRecords.value.filter((r) => r.status === '待审批')
  const mine = leaveRecords.value.filter((r) => r.name === userName.value)
  const myPending = mine.filter((r) => r.status === '待审批').length
  const topped = notices.value.filter((n) => n.top).length
  const departments = new Set(DIRECTORY_CONTACTS.map((c) => c.department)).size

  /* 公告 / 成员这两张卡两边一样，先拼好，免得各写一遍 */
  const noticeCard = {
    label: '公告数量',
    value: summary.value.notice,
    icon: Warning,
    tone: 'violet',
    sub: topped ? `${topped} 条置顶` : '无置顶公告',
    path: '/notice',
  }
  const memberCard = {
    label: '小组成员',
    value: summary.value.member,
    icon: User,
    tone: 'pink',
    sub: `分属 ${departments} 个部门`,
    path: '/contacts',
  }
  const todoCard = {
    label: '待办事项',
    value: summary.value.todo,
    icon: List,
    tone: 'teal',
    sub: overdue ? `其中 ${overdue} 条已逾期` : '暂无逾期',
    path: '/todo',
  }

  if (isAdmin.value) {
    /*
     * 管理员：第一张卡必须是「待审批」。
     * 他打开工作台最想知道的就是“有没有人在等我”，而不是自己有几条待办。
     */
    const oldest = allPending.length
      ? Math.max(...allPending.map((r) => daysSince(r.applyTime, today)))
      : 0
    return [
      {
        label: '待审批',
        value: allPending.length,
        icon: Document,
        tone: 'indigo',
        sub: allPending.length ? `最早的 ${oldest} 天前提交` : '目前没有待审批',
        path: '/leave',
      },
      todoCard,
      noticeCard,
      memberCard,
    ]
  }

  /* 学生：请假只能看自己的（跟请假页一致），所以是「我的请假」不是「请假申请」 */
  return [
    todoCard,
    {
      label: '我的请假',
      value: mine.length,
      icon: Document,
      tone: 'indigo',
      sub: myPending ? `${myPending} 条待审批` : '全部已处理',
      path: '/leave',
    },
    noticeCard,
    memberCard,
  ]
})

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
  gap: var(--st-page-gap);
}

/* ---------- 顶部欢迎卡：全页唯一一张铺渐变的卡 ----------
 * 规矩就一条：**渐变只当点缀**。
 *   这一张卡是“主视觉”，整块铺；其他卡片一律纯白 + 一条渐变顶边。
 *   如果把渐变铺满整页，人眼没有休息的地方，再好的色也会显土。
 *
 * 【重要】底色是浅色彩虹 → 所以文字【必须是深灰】，不能用白字。
 *   浅底配白字会糊成一片（白字只在上一版那种深蓝底上才行）。
 * 【取消了】原来的两个白色装饰圆 —— 大块半透明圆属于“大光斑”，和克制相反。
 */
.welcome {
  position: relative;
  overflow: hidden;
  color: var(--st-text-primary);
  /*
   * 两层叠起来：
   *   上层：白色蒙版，左边 74% 几乎盖白、到最右边完全透明。
   *   下层：--grad-hero（100° 的浅彩虹）。
   * 效果是「白卡从左边渐变出血到彩虹」—— 文字/头像落在白底那一侧，
   * 对比度反而比整张铺满彩色更好，也不会显得脏。
   * ⚠️ 色值一律走令牌，别在这写死 hex（换主题时要全找一遍）。
   */
  background:
    linear-gradient(
      100deg,
      rgb(255 255 255 / 74%) 0%,
      rgb(255 255 255 / 12%) 78%,
      rgb(255 255 255 / 0%) 100%
    ),
    var(--st-gradient-hero);
  border: none;
  border-radius: var(--st-radius-card);
  box-shadow: var(--st-shadow-rainbow);
}

.welcome__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--st-gap-base);
}

.welcome__left {
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
  min-width: 0;
}

/* 头像反过来用【深档】彩虹：浅底上放浅色头像就看不见了。
   白字是撑得住这个深度的（大号粗体，对比度够）。 */
.welcome__avatar {
  flex-shrink: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  background: var(--grad-rainbow);
  border: 2px solid rgb(255 255 255 / 72%);
  box-shadow: 0 4px 12px rgb(131 113 194 / 26%);
  transition: transform var(--st-duration-base) var(--st-ease-back);
}

.welcome:hover .welcome__avatar {
  transform: scale(1.06) rotate(-4deg);
}

.welcome__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--st-text-primary);
}

/* 日期压灰一点：次要信息不该和大标题抢视力 */
.welcome__desc {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgb(48 49 51 / 62%);
}

/* 数据卡片、区块的样式已随子组件移走，见 ./components/ */
</style>
