<template>
  <!-- 这个块嵌在首页那张渐变欢迎卡里，所以自己不再是卡片、背景透明 -->
  <div class="check-in">
    <div class="check-in__status">
      <el-icon class="check-in__icon" :class="{ 'check-in__icon--done': done }" :size="18">
        <component :is="done ? CircleCheckFilled : Clock" />
      </el-icon>

      <div class="check-in__text">
        <div class="check-in__title">{{ done ? `已打卡 ${lastTime}` : '今日未打卡' }}</div>
        <!-- 日期在卡片左边已经显示了，这里不重复；只留地点 -->
        <div v-if="placeText" class="check-in__place" :title="placeText">{{ placeText }}</div>
      </div>

      <span v-if="streak > 0" class="check-in__streak">连续 {{ streak }} 天</span>
    </div>

    <!-- 撤销是给演示用的：答辩时讲完可以点掉，重新演一遍 -->
    <button v-if="done" type="button" class="check-in__undo" @click="undo">撤销</button>
    <button v-else type="button" class="check-in__btn" :disabled="locating" @click="doCheckIn">
      {{ locating ? '定位中…' : '打卡' }}
    </button>
  </div>
</template>

<script setup>
/**
 * 每日打卡（带地理位置）。
 *
 * ⚠️ 三件事要清楚：
 * 1. 记录存在 @/composables/appStore 里（它自己会写 localStorage，刷新还在），
 *    但只有你自己这台电脑知道 —— 接后端后应该改成调接口，让「谁在哪打的卡」真正进数据库。
 * 2. 定位需要浏览器权限，而且**必须是 https 或 localhost**，
 *    用 http 的 IP 直访，浏览器会直接拒绝给位置（这是浏览器的硬性规定）。
 *    定位失败**不会阻止打卡**，只在记录里标一下——不然用户就被卡死了。
 *    （这也是我们最终没把项目挂到服务器上的原因之一）
 * 3. 「坐标变地名」要走逆地理编码（见 src/api/geo.js）：
 *    浏览器自带的定位**只给坐标，不给地名**，要地名必须查地图服务。
 *    没配 key 也能用，只是显示坐标而不是地名。
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, Clock } from '@element-plus/icons-vue'
import { reverseGeocode } from '@/api/geo'
import { checkin } from '@/composables/appStore'
import { consumeCommand, pendingCommand } from '@/composables/aiAgent'

/** 本地日期字符串。别用 toISOString()，它按 UTC 算，会把日期算偏一天 */
function dateStr(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function timeStr(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/**
 * 打卡状态结构：{ lastDate, lastTime, streak, place }。
 * 存的是 appStore 里那个 ref —— 与 AI 助手读的快照是同一份，
 * 所以「我今天打卡了吗」AI 答得出来（以前打卡状态只活在本组件里，它看不到）。
 */
const state = checkin
const locating = ref(false) // 正在定位

/** 今天（本组件打开时算一次；跨天不刷新，演示够用） */
const today = dateStr()

const done = computed(() => state.value.lastDate === today)
const lastTime = computed(() => state.value.lastTime)
const streak = computed(() => state.value.streak)

/**
 * 打卡块里那一行地点。
 * 日期不用在这里显示 —— 左边大标题下面已经有了，重复一遍是噪音。
 */
const placeText = computed(() => {
  const place = state.value.place
  if (!place) return ''
  if (place.error) return place.error

  // 顺序：附近 POI 名 > 拼好的短地址 > 完整地址 > 坐标。
  // 「短地址」是后端专门拼的（市+区+街道），比完整地址短得多。
  // 拿不到地名就退回坐标 —— 退回去是常态，不算出错。
  return (
    place.poi ||
    place.short ||
    place.address ||
    `${place.lat}, ${place.lng}（±${place.accuracy} 米）`
  )
})

/**
 * 取当前位置。
 * 注意它【不一定成功】：用户可能拒绝、可能超时、可能没网。
 * 所以这里永远 resolve，把失败也当成一种正常结果交回去。
 */
function getPosition() {
  return new Promise((resolve) => {
    if (!('geolocation' in navigator)) {
      resolve({ error: '浏览器不支持定位' })
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: Number(position.coords.latitude.toFixed(5)),
          lng: Number(position.coords.longitude.toFixed(5)),
          accuracy: Math.round(position.coords.accuracy),
        })
      },
      (error) => {
        const reasons = {
          1: '未授予定位权限',
          2: '定位失败（取不到位置）',
          3: '定位超时',
        }
        resolve({ error: reasons[error.code] || '定位失败' })
      },
      { timeout: 8000, maximumAge: 60000 },
    )
  })
}

/** 撤销用：记一下打卡前的样子 */
let beforeCheckIn = null

async function doCheckIn() {
  if (done.value || locating.value) return

  locating.value = true
  const place = await getPosition()

  // 拿到坐标后，再问一句「这是哪个地方」。这一步可能失败（没配 key / 没网），
  // 失败了就只存坐标，不影响打卡。
  if (!place.error) {
    const geo = await reverseGeocode(place)
    if (geo) {
      place.poi = geo.poi
      place.address = geo.short || geo.address
    }
  }

  locating.value = false

  beforeCheckIn = { ...state.value }
  const yesterday = dateStr(new Date(Date.now() - 86400000))

  state.value = {
    lastDate: today,
    lastTime: timeStr(),
    // 昨天打过就接着数，断签就从 1 重新开始
    streak: state.value.lastDate === yesterday ? state.value.streak + 1 : 1,
    place,
  }

  // 定位失败也给打上，只是提醒一句——总不能因为没定位就不让人打卡
  if (place.error) ElMessage.warning(`打卡成功（${place.error}）`)
  else ElMessage.success('打卡成功')
}

function undo() {
  state.value = beforeCheckIn ?? { lastDate: '', lastTime: '', streak: 0, place: null }
  beforeCheckIn = null
  ElMessage.info('已撤销')
}

/*
 * ---- AI 助手说「帮你打卡 / 撤销打卡」时，真正动手的是这里 ----
 * 定位和查地名只有浏览器能做，所以服务端（server/app.py 的 check_in 工具）
 * 只递一个信号过来，由这个组件接住并执行。
 * immediate 是为了处理「AI 先跳页再操作」：跳过来时暗号可能已经放好了。
 */
watch(
  pendingCommand,
  () => {
    const command = consumeCommand('checkin')
    if (!command) return

    if (command.type === 'checkin_undo') {
      if (!done.value) {
        ElMessage.info('今天还没打卡，不用撤销')
        return
      }
      undo()
      return
    }

    // 已经打过就说一声，别默默什么都不干（AI 那边不知道本地记录）
    if (done.value) {
      ElMessage.info('今天已经打过卡了')
      return
    }
    doCheckIn()
  },
  { immediate: true },
)
</script>

<style scoped>
/*
 * 打卡块：嵌在首页那张【浅彩虹】欢迎卡里，所以自己【不是卡片】、背景透明。
 *
 * ⚠️ 上一版底色是深蓝，所以这里是白字 + 「白底渐变字」的反渐变按钮。
 *    改成浅彩虹后，白字会糊、白底按钮会看不见 —— 一律改成【深灰字】，
 *    按钮也换成【实底】。浅底 + 白字是行不通的，别再改回去。
 */
.check-in {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--st-gap-base);
}

.check-in__status {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

/* 图标用【本模块的深色】当底：浅底上必须有这么一块实色，不然整个块没重心 */
.check-in__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  color: #fff;
  background: var(--module-ink, var(--st-primary));
  border-radius: var(--st-radius-pill);
  transition: background-color var(--st-duration-base) var(--st-ease);
}

/*
 * 打卡成功：图标弹一下，并翻成「白底 + 绿勾」。
 * 动画由「加上这个 class」触发，所以是打完卡才会弹，不是进页面就弹。
 * （st-pop 定义在 global.css 里）
 */
.check-in__icon--done {
  color: var(--st-success);
  background: #fff;
  animation: st-pop var(--st-duration-base) var(--st-ease-back) both;
}

.check-in__text {
  min-width: 0;
}

.check-in__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.check-in__place {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--st-text-secondary);
}

.check-in__streak {
  padding: 1px 8px;
  font-size: 11px;
  color: var(--st-text-regular);
  white-space: nowrap;
  background: rgb(255 255 255 / 62%);
  border-radius: var(--st-radius-pill);
}

/*
 * ---------- 打卡按钮：实底模块色 ----------
 * 浅底上的主按钮就必须“实”，靠颜色深浅拉开层次；
 * 用白底/浅底都会和背景糊在一起，看不出哪儿能点。
 */
.check-in__btn {
  padding: 7px 20px;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  background: var(--module-grad, var(--grad-blue));
  border: none;
  border-radius: var(--st-radius-pill);
  box-shadow: 0 4px 12px rgb(79 157 148 / 30%);
  transition:
    transform var(--st-duration-base) var(--st-ease),
    filter var(--st-duration-base) var(--st-ease),
    box-shadow var(--st-duration-base) var(--st-ease);
}

.check-in__btn:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgb(79 157 148 / 36%);
}

.check-in__btn:disabled {
  cursor: default;
  opacity: 0.75;
}

/* 撤销：低调一点，不和主按钮抢视线 */
.check-in__undo {
  padding: 6px 14px;
  font: inherit;
  font-size: 13px;
  color: var(--st-text-regular);
  cursor: pointer;
  background: rgb(255 255 255 / 62%);
  border: 1px solid rgb(48 49 51 / 12%);
  border-radius: var(--st-radius-pill);
  transition:
    color var(--st-duration-base) var(--st-ease),
    background-color var(--st-duration-base) var(--st-ease);
}

.check-in__undo:hover {
  color: var(--st-text-primary);
  background: #fff;
}
</style>
