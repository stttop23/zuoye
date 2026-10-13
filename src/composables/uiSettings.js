/**
 * 界面偏好（侧边栏底部「我的 / 设置」里那几个开关）
 * ================================================
 * 都是本地偏好：存 localStorage，刷新还记得。
 *
 * 设计原则：**只放真会生效的开关，不摆假选项**。
 * 现在两个都有实际效果：
 *   - 界面动效关掉 → 给 <html> 加 `st-no-motion`，全站动画/过渡时长归零
 *     （和系统的 `prefers-reduced-motion` 用同一套兜底，见 global.css）
 *   - 未读红点关掉 → 铃铛上不再显示未读数
 */
import { ref, watch } from 'vue'

const STORAGE_KEY = 'student-work-ui-settings'

function readSettings() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') || {}
  } catch {
    return {}
  }
}

const saved = readSettings()

/** 界面动效（默认开） */
const motionOn = ref(saved.motionOn !== false)

/** 铃铛上的未读红点（默认开） */
const bellBadgeOn = ref(saved.bellBadgeOn !== false)

/**
 * 把「关动效」落到 <html> 的 class 上。
 * 用 class 而不是直接改样式：CSS 里一处兜底就够了，组件里不用各自判断。
 */
function applyMotion() {
  document.documentElement.classList.toggle('st-no-motion', !motionOn.value)
}

watch([motionOn, bellBadgeOn], () => {
  applyMotion()
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ motionOn: motionOn.value, bellBadgeOn: bellBadgeOn.value }),
    )
  } catch {
    // 存不了就算了，内存里照样生效
  }
})

applyMotion() // 进页面就应用一次，不然刷新后要等用户再点一下

export function useUiSettings() {
  return { motionOn, bellBadgeOn }
}
