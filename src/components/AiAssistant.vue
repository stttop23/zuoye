<template>
  <!-- 悬浮入口，全站常驻。可以拖着走，松手会吸附到左右最近的一侧 -->
  <div
    class="ai-fab"
    :class="{ 'is-dragging': dragging, 'is-ready': ready }"
    :style="{ transform: `translate3d(${x}px, ${y}px, 0)` }"
    @pointerdown="按下"
    @click.capture="点的时候"
  >
    <el-button
      type="primary"
      circle
      size="large"
      aria-label="打开 AI 助手"
      @click="drawerVisible = true"
    >
      <el-icon :size="22"><ChatDotRound /></el-icon>
    </el-button>
  </div>

  <!-- 抽屉从哪边出来，跟着按钮吸附到哪边 -->
  <el-drawer
    v-model="drawerVisible"
    title="AI 助手"
    :direction="side === 'left' ? 'ltr' : 'rtl'"
    size="380px"
    class="ai-drawer"
  >
    <AiChatPanel />
  </el-drawer>
</template>

<script setup>
/**
 * 悬浮入口（抽屉壳 + 可拖动的悬浮按钮）。
 *
 * 聊天的本体在 AiChatPanel.vue，跟「AI 助手」独立页面共用同一份——
 * 对话状态存在 composables/aiAgent.js，所以抽屉里聊到一半切到页面，记录还在。
 *
 * ============================================================
 * 拖动 + 边缘吸附
 * ------------------------------------------------------------
 * 为什么用 transform 而不是 left/top：
 *   transform 走合成层，拖动时只重绘不重排，跟手得多；
 *   而且吸附回弹可以直接用 CSS transition，不用手写动画。
 *
 * 为什么松手要吸附：
 *   悬浮按钮停在屏幕正中间会挡住内容，贴边是唯一不烦人的位置。
 *   但垂直方向保留用户拖到的高度，不然「拖了等于没拖」。
 * ============================================================
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import AiChatPanel from '@/components/AiChatPanel.vue'
import { onAgentCloseRequest } from '@/composables/aiAgent'

/**
 * 抽屉开关【必须】是本组件自己的 ref。
 * 曾经把它放在 aiAgent.js 里共享，结果 el-drawer 的写回到不了那个 ref，
 * 表现是「点 X / 按 Esc / 点遮罩都关不掉」。自己的 ref 没这个问题。
 */
const drawerVisible = ref(false)

// AI 填完表要自动收起抽屉：composable 发「关闭请求」过来，这里接住
onAgentCloseRequest(() => {
  drawerVisible.value = false
})

/* ---------- 位置状态 ---------- */
const SIZE = 52 // 按钮直径，和 CSS 里的宽高一致
const EDGE = 24 // 离屏幕边缘留多少
const STORAGE_KEY = 'student-work-ai-fab'

/** 吸附在哪一侧；垂直位置记住用户拖到的 y（null = 还没定过，用默认的右下角） */
const side = ref('right')
const x = ref(0)
const y = ref(null)
const dragging = ref(false)
/** 首次定位算完之前先隐藏，免得看到按钮从左上角飞过来 */
const ready = ref(false)

let 起点X = 0
let 起点Y = 0
let 起点位置X = 0
let 起点位置Y = 0
let 拖过 = false

function 存() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ side: side.value, y: y.value }))
  } catch {
    /* 存不进去就算了 */
  }
}

function 读() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const saved = raw ? JSON.parse(raw) : null
    if (saved && (saved.side === 'left' || saved.side === 'right')) {
      side.value = saved.side
      if (typeof saved.y === 'number') y.value = saved.y
    }
  } catch {
    /* 读不出来就用默认位置 */
  }
}

/** 按当前 side / y 算出实际坐标，并夹进可视区（窗口变小了也不会跑到屏幕外） */
function 归位(带动画 = true) {
  const 宽 = window.innerWidth
  const 高 = window.innerHeight
  const 最下 = Math.max(高 - SIZE - EDGE, EDGE)

  x.value = side.value === 'left' ? EDGE : 宽 - SIZE - EDGE
  // 没拖过的就贴着底部（原来的位置），拖过的就记住那个高度
  y.value = y.value == null ? 最下 : Math.min(Math.max(y.value, EDGE), 最下)

  if (!带动画) {
    // 拖着的时候别加过渡，不然手指和按钮不同步
    dragging.value = true
    requestAnimationFrame(() => {
      dragging.value = false
    })
  }
  ready.value = true
}

function 按下(e) {
  if (e.pointerType === 'mouse' && e.button !== 0) return
  dragging.value = true
  拖过 = false
  起点X = e.clientX
  起点Y = e.clientY
  起点位置X = x.value
  起点位置Y = y.value
  /*
   * ⚠️ 这里【不能】用 e.currentTarget.setPointerCapture()。
   *    指针被捕获之后，浏览器会把后面的 click 也重定向到捕获的那个元素，
   *    于是按钮自己的 click 永远不会触发 ——
   *    表现就是「拖过一次之后，第一次点按钮没反应」。实测踩到过。
   *    改成在 window 上监听拖动过程，click 的归属就不会被改。
   */
  window.addEventListener('pointermove', 移动)
  window.addEventListener('pointerup', 松手)
  window.addEventListener('pointercancel', 松手)
}

function 移动(e) {
  if (!dragging.value) return
  const dx = e.clientX - 起点X
  const dy = e.clientY - 起点Y
  if (Math.abs(dx) > 4 || Math.abs(dy) > 4) 拖过 = true

  const 宽 = window.innerWidth
  const 高 = window.innerHeight
  // 夹在屏幕里，别拖出去找不回来
  x.value = Math.min(Math.max(起点位置X + dx, EDGE), 宽 - SIZE - EDGE)
  y.value = Math.min(Math.max(起点位置Y + dy, EDGE), 高 - SIZE - EDGE)
}

function 松手() {
  window.removeEventListener('pointermove', 移动)
  window.removeEventListener('pointerup', 松手)
  window.removeEventListener('pointercancel', 松手)

  if (!dragging.value) return
  dragging.value = false
  // 看按钮中心偏左还是偏右，就吸附到哪边
  side.value = x.value + SIZE / 2 < window.innerWidth / 2 ? 'left' : 'right'
  归位()
  存()
}

/** 拖动结束的那次 click 不算点击，不然一边拖一边就把抽屉打开了 */
function 点的时候(e) {
  if (拖过) {
    拖过 = false
    e.stopPropagation()
    e.preventDefault()
  }
}

function onResize() {
  归位(false)
}

onMounted(() => {
  读()
  归位(false)
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('pointermove', 移动)
  window.removeEventListener('pointerup', 松手)
  window.removeEventListener('pointercancel', 松手)
})
</script>

<style scoped>
/*
 * 位置完全由 JS 通过 transform 给（translate3d），
 * 所以这里只写 top/left: 0 当描点，不写 right/bottom。
 */
.ai-fab {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1500;
  /* 吸附回弹就是这个 transition 做的（缓动带一点回弹，弹得更自然） */
  transition:
    transform var(--st-duration-base) var(--st-ease-back),
    opacity var(--st-duration-base) var(--st-ease);
  /* 手机上别让浏览器去猜这是横划还是滚页，拖动交给我们 */
  touch-action: none;
  /* 还没算完位置先藏起来，免得看到它从左上角飞过来 */
  opacity: 0;
}

.ai-fab.is-ready {
  opacity: 1;
}

/* 按住拖动时不能有过渡，否则按钮会「追不上」鼠标 */
.ai-fab.is-dragging {
  cursor: grabbing;
  transition: none;
}

/*
 * 整条彩虹 = AI 的“品牌色”（它不属于任何单个模块，所以用全部色相）。
 * 和面板里的圆形发送按钮同一套，一眼能认出「这俩是一回事」。
 */
.ai-fab :deep(.el-button) {
  width: 52px;
  height: 52px;
  color: #fff;
  background: var(--grad-rainbow);
  box-shadow: 0 6px 18px rgb(131 113 194 / 34%);
  transition:
    transform var(--st-duration-base) var(--st-ease-back),
    box-shadow var(--st-duration-base) var(--st-ease);
}

/* 悬停时放大 + 阴影拉深，让它看起来「能点」 */
.ai-fab :deep(.el-button:hover) {
  color: #fff;
  background: var(--grad-rainbow);
  transform: scale(1.1);
  box-shadow: 0 10px 26px rgb(131 113 194 / 44%);
}

.ai-fab :deep(.el-button:active) {
  transform: scale(0.98);
}

/*
 * 平时轻轻呼吸（一呼一吸 3s），提醒用户「我在这儿」。
 * 只动光晕、不动位置，不然一直抖很吵。
 */
.ai-fab :deep(.el-button) {
  animation: ai-fab-breathe 3s ease-in-out infinite;
}

@keyframes ai-fab-breathe {
  0%,
  100% {
    box-shadow: 0 6px 18px rgb(131 113 194 / 30%);
  }
  50% {
    box-shadow:
      0 6px 18px rgb(131 113 194 / 30%),
      0 0 0 10px rgb(131 113 194 / 8%);
  }
}

/* 鼠标移上去就停下呼吸，专心响应悬停 */
.ai-fab :deep(.el-button:hover) {
  animation: none;
}

/* 抽屉内容由 AiChatPanel 自己排版，这里把内边距清掉 */
.ai-drawer :deep(.el-drawer__body) {
  padding: 0;
}
</style>
