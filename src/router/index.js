import { createRouter, createWebHistory } from 'vue-router'

/**
 * ⚠️ 路由表由刘皖统一维护
 * 队友写完自己的页面后，只需要把自己的那一行 path/component 告诉我，
 * 不要各自去改 main.js，避免冲突。
 */
const routes = [
  {
    path: '/',
    component: () => import('@/layout/BasicLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' },
      },
      {
        path: 'notice',
        name: 'Notice',
        component: () => import('@/views/NoticeView.vue'),
        meta: { title: '公告通知', icon: 'Bell' },
      },
      {
        path: 'leave',
        name: 'Leave',
        component: () => import('@/views/LeaveView.vue'),
        meta: { title: '请假申请', icon: 'Document' },
      },
      {
        path: 'todo',
        name: 'Todo',
        component: () => import('@/views/TodoView.vue'),
        meta: { title: '待办事项', icon: 'List' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 每次跳转自动改浏览器标签页标题
router.afterEach((to) => {
  const base = '学生工作管理系统'
  document.title = to.meta?.title ? `${to.meta.title} - ${base}` : base
})

export default router
