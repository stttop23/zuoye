/**
 * 权限（能力表）
 * ==============
 *
 * ⚠️ 先把话说清楚：**这是前端控制，不是安全控制。**
 *    浏览器里的判断谁都能绕过（打开控制台改个变量就行了）。
 *    它只解决「别让用户看到他根本用不了的按钮」这种体验问题。
 *    真正拦住人必须在后端做 —— 后端收到请求时要重新验一遍身份，
 *    因为在浏览器里，任何前端判断都只是建议。
 *
 * 为什么单独放一个文件：
 *    权限如果散在每个页面里手写 `if (role === 'admin')`，
 *    早晚有人把角色名写错（'管理员' / 'admin' / 'Admin'），
 *    或者新加一个按钮时忘了加判断。集中成一张表，谁都能查到、改一处就够。
 *
 * 用法：
 *    const { canDo } = usePermissions()
 *    canDo('notice.publish')     // true / false
 *    模板里直接写 v-if="canDo('notice.publish')"
 *
 * 加新能力：往 MATRIX 里的角色数组塞一个名字就行。
 */
import { useUserProfile } from './userProfile'

/** 能力表：谁能做什么 */
const MATRIX = {
  // 学生：能自己请假、自己建待办，但不能审批别人的假、不能发布公告
  student: ['leave.apply', 'leave.cancelOwn', 'todo.create', 'todo.editOwn'],

  // 管理员：在学生的全部能力之上，多出「审别人的」和「发公告」
  admin: [
    'leave.apply',
    'leave.cancelOwn',
    'leave.approve',
    'todo.create',
    'todo.editOwn',
    'todo.deleteAny',
    'notice.publish',
    'notice.delete',
  ],
}

/** 某个角色能不能做某件事 */
export function can(role, action) {
  return (MATRIX[role] || []).includes(action)
}

/**
 * 页面里用它。
 * ⚠️ 不需要 computed 包一层：canDo 里读了 userRole.value，
 *    在模板/渲染函数里调用时就已经建立了依赖，角色一变就会重渲染。
 */
export function usePermissions() {
  const { userRole, isAdmin } = useUserProfile()

  return {
    userRole,
    isAdmin,
    canDo: (action) => can(userRole.value, action),
  }
}
