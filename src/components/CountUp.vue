<template>{{ display }}</template>

<script setup>
/**
 * 数字滚动（从 0 滚到目标值）
 * ========================
 * 用在首页那四个统计卡片上：数字「跳」出来比直接怼一个数字有生气。
 *
 * 用法： <CountUp :value="6" />
 *
 * ⚠️ 两个细节：
 * 1. 用 requestAnimationFrame 而不是 setInterval —— 前者跟屏幕刷新同步，
 *    不会掉帧，切到后台标签页时会自动停下来，不白烧 CPU。
 * 2. 缓动用的是 easeOutCubic（先快后慢），数字冲上去再稳稳停住，
 *    比匀速滚动自然得多。
 */
import { onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  value: { type: Number, required: true },
  /** 滚多久（毫秒） */
  duration: { type: Number, default: 900 },
})

const display = ref(0)
let frame = null
let from = 0
let startedAt = 0

/** 系统开了「减少动态效果」就别滚了，直接给最终值 */
function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
}

function run(to) {
  cancelAnimationFrame(frame)

  if (prefersReducedMotion()) {
    display.value = to
    return
  }

  from = display.value
  startedAt = performance.now()

  const tick = (now) => {
    const progress = Math.min(1, (now - startedAt) / props.duration)
    const eased = 1 - Math.pow(1 - progress, 3) // easeOutCubic
    display.value = Math.round(from + (to - from) * eased)
    if (progress < 1) frame = requestAnimationFrame(tick)
  }

  frame = requestAnimationFrame(tick)
}

// immediate：进页面就先从 0 滚上去
watch(() => props.value, run, { immediate: true })

onBeforeUnmount(() => cancelAnimationFrame(frame))
</script>
