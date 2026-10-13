/**
 * 把 CSS 媒体查询搬进 JS
 * ======================
 *
 * 为什么需要它：
 *   有些适配光靠 CSS 改不了。比如公告页，手机上是「一列标题」，
 *   电脑上是「六列表格」—— 这是两套完全不同的结构，不是改两个宽度就行的，
 *   只能用 v-if 切。这类判断就得在 JS 里做。
 *
 * 用法：
 *   const isMobile = useIsMobile()
 *   <div v-if="isMobile">手机版</div>
 *   <div v-else>电脑版</div>
 *
 * ⚠️ 断点值必须和 CSS 里的 @media 一致，所以在这里导出一个常量，
 *    JS 和 CSS 都认同一个数，改的时候不会漏掉一边。
 *    （CSS 里的 @media (max-width: 768px) 是手写的，改断点要一起改。）
 *
 * ⚠️ 初始值是**同步**取的（不是等 onMounted 再取），
 *    否则第一帧会先按电脑版渲染、再跳成手机版，能看见一下闪动。
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

/** 全站唯一的移动端断点 */
export const MOBILE_QUERY = '(max-width: 768px)'

export function useMediaQuery(query) {
  const matches = ref(
    typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia(query).matches
      : false,
  )

  let mql = null

  function sync(event) {
    matches.value = event.matches
  }

  onMounted(() => {
    mql = window.matchMedia(query)
    sync(mql)
    mql.addEventListener('change', sync)
  })

  onBeforeUnmount(() => {
    mql?.removeEventListener('change', sync)
  })

  return matches
}

/** 是不是手机宽度（≤768px） */
export function useIsMobile() {
  return useMediaQuery(MOBILE_QUERY)
}
