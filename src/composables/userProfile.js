import { computed, ref, watch } from 'vue'

const storageKey = 'student-work-user-name'

function readUserName() {
  try {
    return localStorage.getItem(storageKey)?.trim() || '刘皖'
  } catch {
    return '刘皖'
  }
}

const userName = ref(readUserName())
const userInitial = computed(() => Array.from(userName.value.trim())[0] || '用')

watch(userName, (name) => {
  try {
    localStorage.setItem(storageKey, name)
  } catch {
    // Keep the in-memory profile usable when browser storage is unavailable.
  }
})

export function useUserProfile() {
  return { userName, userInitial }
}