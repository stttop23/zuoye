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
        // 按人分目录：页面源码在仓库根目录下各自的文件夹里
        component: () => import('../../刘皖/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' },
      },
      {
        path: 'notice',
        name: 'Notice',
        component: () => import('../../刘皖/views/notice/index.vue'),
        meta: { title: '公告通知', icon: 'Bell' },
      },
      {
        path: 'leave',
        name: 'Leave',
        component: () => import('../../罗欣雨/views/leave/index.vue'),
        meta: { title: '请假申请', icon: 'Document' },
      },
      {
        path: 'todo',
        name: 'Todo',
        component: () => import('../../张晶/views/todo/index.vue'),
        meta: { title: '待办事项', icon: 'List' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../../刘皖/views/NotFoundView.vue'),
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
