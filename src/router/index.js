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
        // 按人分目录（拼音，避免中文路径乱码）：liuwan / luoxinyu / zhangjing
        component: () => import('../../liuwan/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'HomeFilled' },
      },
      {
        path: 'notice',
        name: 'Notice',
        component: () => import('../../liuwan/views/notice/index.vue'),
        meta: { title: '公告通知', icon: 'Bell' },
      },
      {
        path: 'leave',
        name: 'Leave',
        component: () => import('../../luoxinyu/views/leave/index.vue'),
        meta: { title: '请假申请', icon: 'Document' },
      },
      {
        path: 'todo',
        name: 'Todo',
        component: () => import('../../zhangjing/views/todo/index.vue'),
        meta: { title: '待办事项', icon: 'List' },
      },
      {
        path: 'contacts',
        name: 'Contacts',
        component: () => import('../../liuwan/views/contacts/index.vue'),
        meta: { title: '通讯录', icon: 'User' },
      },
      // 群聊模块来自 feature/luo-xinyu
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/chat/ChatView.vue'),
        meta: { title: '群聊', icon: 'ChatLineRound' },
      },
      {
        path: 'assistant',
        name: 'Assistant',
        // AI 助手独立页面（抽屉里的那份聊天本体复用 AiChatPanel.vue）
        component: () => import('../../liuwan/views/assistant/index.vue'),
        meta: { title: 'AI 助手', icon: 'ChatDotRound' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../../liuwan/views/NotFoundView.vue'),
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
