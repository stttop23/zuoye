<template>
  <div class="dashboard">
    <!-- ==================== 欢迎条 ==================== -->
    <el-card shadow="never" class="welcome">
      <div class="welcome__inner">
        <el-avatar :size="56" class="welcome__avatar">刘</el-avatar>
        <div>
          <h2 class="welcome__title">欢迎来到工作台，刘皖</h2>
          <p class="welcome__desc">{{ todayText }} · 今天也要元气满满哦</p>
        </div>
      </div>
    </el-card>

    <!-- ==================== 数据卡片 ==================== -->
    <el-row :gutter="16" class="stat-row">
      <el-col v-for="item in stats" :key="item.label" :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card__inner">
            <div class="stat-card__icon" :style="{ background: item.bg, color: item.color }">
              <el-icon :size="22"><component :is="item.icon" /></el-icon>
            </div>
            <div>
              <div class="stat-card__value">{{ item.value }}</div>
              <div class="stat-card__label">{{ item.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ==================== 快捷入口 ==================== -->
    <el-card shadow="never" class="section">
      <template #header>
        <span class="section__title">快捷入口</span>
      </template>

      <el-space wrap :size="12">
        <el-button type="primary" @click="router.push('/notice')">
          <el-icon><Bell /></el-icon>
          查看公告
        </el-button>
        <el-button type="success" @click="router.push('/todo')">
          <el-icon><List /></el-icon>
          我的待办
        </el-button>
        <el-button type="warning" @click="router.push('/leave')">
          <el-icon><Document /></el-icon>
          发起请假
        </el-button>
        <el-button plain @click="onRefresh">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </el-space>
    </el-card>

    <!-- ==================== 最新公告 ==================== -->
    <el-card shadow="never" class="section">
      <template #header>
        <div class="flex-between">
          <span class="section__title">最新公告</span>
          <el-link type="primary" underline="never" @click="router.push('/notice')">
            查看全部
          </el-link>
        </div>
      </template>

      <el-table :data="recentNotices" stripe style="width: 100%">
        <el-table-column prop="title" label="公告标题" min-width="220" show-overflow-tooltip />
        <el-table-column prop="publishTime" label="发布时间" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.top ? 'danger' : 'info'" size="small" effect="light">
              {{ row.top ? '置顶' : '普通' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
/**
 * ⚠️ 当前全部使用「假数据」，前端可以独立开发。
 * 后端接口就绪后，把 data 换成 axios 请求即可，页面结构不用动。
 */
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Bell, Document, List, Refresh, User, Warning } from '@element-plus/icons-vue'

const router = useRouter()

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

/* ---------- 数据卡片 ---------- */
.stat-row {
  margin-bottom: 0;
}

.stat-card {
  margin-bottom: var(--st-gap-base);
}

.stat-card__inner {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--st-radius-base);
}

.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--st-text-primary);
}

.stat-card__label {
  margin-top: 2px;
  font-size: 13px;
  color: var(--st-text-secondary);
}

/* ---------- 区块 ---------- */
.section {
  border: none;
}

.section__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}
</style>
