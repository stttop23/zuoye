<template>
  <div class="swipe-row" :class="{ 'is-static': disabled }">
    <!--
      操作按钮。
      小屏 / 触屏：藏在这一行后面，内容向左滑开就露出来。
      大屏：直接排到行右边（就是 is-static 那个模式），不需要滑。
      @click="收起" 是等按钮自己的处理跑完之后冒泡上来，点完任何一个都收回这一行。
    -->
    <div class="swipe-row__actions" :class="{ 'is-inline': disabled }" @focusin="打开" @click="收起">
      <slot name="actions" />
    </div>

    <!-- 跟着手指 / 鼠标走的那一层（静态模式下它就是个普通容器） -->
    <div
      class="swipe-row__content"
      :class="{ 'is-animating': !dragging }"
      :style="disabled ? null : { transform: `translateX(${offset}px)` }"
      @pointerdown="按下"
      @pointermove="移动"
      @pointerup="松手"
      @pointercancel="松手"
      @click.capture="点的时候"
    >
      <slot />
    </div>
  </div>
</template>

<script setup>
/**
 * 左滑露出操作（Swipe to reveal）
 * ================================
 * 手机上很常见：列表项往左划，右边滑出一排操作按钮。
 * 这里鼠标拖拽也能用，所以桌面上照样能演示。
 *
 * 用法：
 *   <SwipeRow :width="208">
 *     <div>这一行正常显示的内容</div>
 *     <template #actions>
 *       <button @click="完成">完成</button>
 *       ...
 *     </template>
 *   </SwipeRow>
 *
 * ⚠️ 几个必须处理的细节（不处理就会很难用）：
 *   1. **先分清是横划还是竖划**：手机上手指一划十有八九带点横向偏移，
 *      如果不管不顾全当横划，页面就滑不动了。所以先比 |dx| 和 |dy|，
 *      竖的就把控制权还给页面。
 *   2. **拖过就不算点击**：不然「划开操作区」这个动作会被当成点了行内容。
 *   3. **同时只允许一行打开**：不然划开三行，满屏都是按钮。
 *   4. 用 transform 而不是 left/top：前者走合成层，不触发重排。
 */
import { ref } from 'vue'

const props = defineProps({
  /** 操作区总宽度（px），要和 actions 里按钮的宽度合得上 */
  width: { type: Number, default: 200 },
  /**
   * 静态模式：不滑动，按钮直接排在行右边。
   * 大屏上用它 —— 屏幕有地方，鼠标划来划去反而别扭。
   */
  disabled: { type: Boolean, default: false },
})

const offset = ref(0)
const dragging = ref(false)

let 起点X = 0
let 起点Y = 0
let 起点位移 = 0
let 拖过 = false
let 方向 = null

/**
 * 模块级变量：所有 SwipeRow 实例共用同一个。
 * 谁滑开就先把上一行关掉。
 */
let 上一个打开的行 = null

function 收起() {
  offset.value = 0
}

function 打开() {
  if (props.disabled || offset.value !== 0) return
  if (上一个打开的行 && 上一个打开的行 !== 收起) 上一个打开的行()
  上一个打开的行 = 收起
  offset.value = -props.width
}

function 按下(e) {
  if (props.disabled) return
  if (e.pointerType === 'mouse' && e.button !== 0) return
  dragging.value = true
  起点X = e.clientX
  起点Y = e.clientY
  起点位移 = offset.value
  拖过 = false
  方向 = null
  上一个打开的行 = 收起
  e.currentTarget.setPointerCapture?.(e.pointerId)
}

function 移动(e) {
  if (!dragging.value) return

  const dx = e.clientX - 起点X
  const dy = e.clientY - 起点Y

  // 还没动够，先不下结论（避免手指轻微抖动就判定方向）
  if (!方向) {
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return
    方向 = Math.abs(dx) > Math.abs(dy) ? 'x' : 'y'
    if (方向 === 'y') {
      // 用户在上下滑页面，这一行不参与
      dragging.value = false
      return
    }
  }

  拖过 = true
  // 只能往左滑出操作区；往右最多回到原位，滑不出白边
  offset.value = Math.min(0, Math.max(-props.width, 起点位移 + dx))
}

function 松手() {
  if (!dragging.value) return
  dragging.value = false
  // 滑过一半就吸附到「打开」，否则弹回去
  const 该打开 = offset.value < -props.width / 2
  offset.value = 该打开 ? -props.width : 0
  上一个打开的行 = 该打开 ? 收起 : null
}

function 点的时候(e) {
  if (props.disabled) return
  // ① 刚拖过：这次 click 是拖拽的副产品，拦掉
  if (拖过) {
    拖过 = false
    e.stopPropagation()
    e.preventDefault()
    return
  }
  // ② 已经是打开状态，点内容 = 收起（而不是触发行本身的点击）
  if (offset.value < 0) {
    e.stopPropagation()
    e.preventDefault()
    收起()
  }
}

defineExpose({ 收起 })
</script>

<style scoped>
.swipe-row {
  position: relative;
  overflow: hidden;
  background: var(--st-bg-card);
}

/* 背后的操作区：贴在右边，内容滑开后正好填满露出来的那块 */
.swipe-row__actions {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: stretch;
}

.swipe-row__content {
  position: relative;
  background: var(--st-bg-card);
  /* 只动 transform：走合成层，不触发重排，滑起来才跟手 */
  will-change: transform;
  /* 横向我们自己接管，竖向还给页面滚动 */
  touch-action: pan-y;
}

.swipe-row__content.is-animating {
  transition: transform var(--st-duration-base) var(--st-ease);
}

/* ============================================================
   静态模式（大屏）
   ------------------------------------------------------------
   屏幕宽的时候不藏按钮，直接排到这一行右边。
   原因：滑动是触屏的手势，台式机用鼠标划反而别扭，而且大屏本来就有地方。
   ============================================================ */
.swipe-row.is-static {
  display: flex;
  align-items: center;
}

.swipe-row.is-static .swipe-row__actions {
  position: static;
  order: 2;
  flex-shrink: 0;
  align-items: center;
  gap: 4px;
  padding-right: 12px;
}

.swipe-row.is-static .swipe-row__content {
  order: 1;
  flex: 1;
  min-width: 0;
  /* 静态模式下不看手势，竖向横向都还给页面 */
  touch-action: auto;
  will-change: auto;
}
</style>
