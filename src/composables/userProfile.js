import { computed, ref, watch } from 'vue'

const storageKey = 'student-work-user-name'
const roleStorageKey = 'student-work-user-role'

/** 没在本地改过时的默认身份 */
const DEFAULT_NAME = '刘皖'

/** 全部合法身份。组长：能发公告给社员，但不能审批（审批只有管理员能做） */
const ROLES = ['student', 'leader', 'admin']

function readUserRole() {
  try {
    const saved = localStorage.getItem(roleStorageKey)
    return ROLES.includes(saved) ? saved : 'student'
  } catch {
    return 'student'
  }
}

function readUserName() {
  try {
    return localStorage.getItem(storageKey)?.trim() || DEFAULT_NAME
  } catch {
    return DEFAULT_NAME
  }
}

const userName = ref(readUserName())
const userInitial = computed(() => Array.from(userName.value.trim())[0] || '用')
const userRole = ref(readUserRole())
const isAdmin = computed(() => userRole.value === 'admin')
const isLeader = computed(() => userRole.value === 'leader')

watch(userName, (name) => {
  try {
    localStorage.setItem(storageKey, name)
  } catch {
    // Keep the in-memory profile usable when browser storage is unavailable.
  }
})

watch(userRole, (role) => {
  try {
    localStorage.setItem(roleStorageKey, role)
  } catch {
    // Keep the in-memory role usable when browser storage is unavailable.
  }
})

/**
 * 「退出账户」用：把本地身份恢复成默认。
 * 本地演示没有账号系统（没后端、没登录），所以“退出”就是忘掉本地改过的名字和身份。
 */
function resetProfile() {
  userName.value = DEFAULT_NAME
  userRole.value = 'student'
}

export function useUserProfile() {
  return { userName, userInitial, userRole, isAdmin, isLeader, resetProfile }
}
