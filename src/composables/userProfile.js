import { computed, ref, watch } from 'vue'

const storageKey = 'student-work-user-name'
const roleStorageKey = 'student-work-user-role'

function readUserRole() {
  try {
    return localStorage.getItem(roleStorageKey) === 'admin' ? 'admin' : 'student'
  } catch {
    return 'student'
  }
}

function readUserName() {
  try {
    return localStorage.getItem(storageKey)?.trim() || '刘皖'
  } catch {
    return '刘皖'
  }
}

const userName = ref(readUserName())
const userInitial = computed(() => Array.from(userName.value.trim())[0] || '用')
const userRole = ref(readUserRole())
const isAdmin = computed(() => userRole.value === 'admin')

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

export function useUserProfile() {
  return { userName, userInitial, userRole, isAdmin }
}