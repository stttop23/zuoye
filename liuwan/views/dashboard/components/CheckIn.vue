<template>
  <el-card shadow="never" class="check-in">
    <div class="check-in__row">
      <div class="check-in__icon" :class="{ 'check-in__icon--done': done }">
        <el-icon :size="24"><component :is="done ? CircleCheckFilled : Clock" /></el-icon>
      </div>

      <div class="check-in__text">
        <div class="check-in__title">{{ done ? `已打卡 ${lastTime}` : '今日未打卡' }}</div>
        <div class="check-in__sub">{{ subText }}</div>
      </div>

      <el-tag v-if="streak > 0" type="warning" effect="plain" size="small">
        连续 {{ streak }} 天
      </el-tag>

      <!-- 撤销是给演示用的：答辩时讲完可以点掉，重新演一遍 -->
      <el-button v-if="done" link @click="undo">撤销</el-button>
      <el-button v-else type="primary" :loading="locating" @click="doCheckIn">
        {{ locating ? '定位中…' : '打卡' }}
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
/**
 * 每日打卡（带地理位置）。
 *
 * ⚠️ 三件事要清楚：
 * 1. 记录现在存在 localStorage（刷新还在），但只有你自己这台电脑知道——
 *    接后端后应该改成调接口，让「谁在哪打的卡」真正进数据库。
 * 2. 定位需要浏览器权限，而且**必须是 https 或 localhost**，
 *    用 IP 直访（http://47.114.62.248）浏览器会直接拒绝定位。
 *    定位失败**不会阻止打卡**，只在记录里标一下——不然用户就被卡死了。
 * 3. 「坐标变地名」要走逆地理编码（见 src/api/geo.js）：
 *    浏览器自带的定位**只给坐标，不给地名**，要地名必须查地图服务。
 *    没配 key 也能用，只是显示坐标而不是地名。
 */
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheckFilled, Clock } from '@element-plus/icons-vue'
import { reverseGeocode } from '@/api/geo'

const STORAGE_KEY = 'student-work-checkin'

/** 本地日期字符串。别用 toISOString()，它按 UTC 算，会把日期算偏一天 */
function dateStr(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function timeStr(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** 存的结构：{ lastDate, lastTime, streak, place }，place 是定位结果或 null */
function readState() {
  const empty = { lastDate: '', lastTime: '', streak: 0, place: null }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? { ...empty, ...JSON.parse(raw) } : empty
  } catch {
    return empty
  }
}

const state = ref(readState())
const locating = ref(false) // 正在定位

/** 今天（本组件打开时算一次；跨天不刷新，演示够用） */
const today = dateStr()

const done = computed(() => state.value.lastDate === today)
const lastTime = computed(() => state.value.lastTime)
const streak = computed(() => state.value.streak)

const todayText = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }),
)

/** 副标题：日期 + 位置（打卡后才有） */
const subText = computed(() => {
  const place = state.value.place
  if (!place) return todayText.value
  if (place.error) return `${todayText.value} · ${place.error}`

  // 有地名就优先显示地名（「浙江大学玉泉校区」比一串数字好认得多）；
  // 拿不到地名就退回坐标 —— 退回去是常态，不算出错。
  const where = place.poi || place.address || `${place.lat}, ${place.lng}（±${place.accuracy} 米）`
  return `${todayText.value} · ${where}`
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

function persist() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.value))
  } catch {
    // 浏览器禁用了本地存储也不影响这一次使用
  }
}

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

  persist()

  // 定位失败也给打上，只是提醒一句——总不能因为没定位就不让人打卡
  if (place.error) ElMessage.warning(`打卡成功（${place.error}）`)
  else ElMessage.success('打卡成功')
}

function undo() {
  state.value = beforeCheckIn ?? { lastDate: '', lastTime: '', streak: 0, place: null }
  persist()
  beforeCheckIn = null
  ElMessage.info('已撤销')
}
</script>

<style scoped>
.check-in {
  border: none;
}

.check-in__row {
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
}

.check-in__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: var(--st-radius-base);
  background: var(--st-primary-light);
  color: var(--st-primary);
}

.check-in__icon--done {
  background: var(--st-bg-page);
  color: var(--st-success);
}

.check-in__text {
  flex: 1;
  min-width: 0;
}

.check-in__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--st-text-primary);
}

.check-in__sub {
  margin-top: 4px;
  font-size: 13px;
  color: var(--st-text-secondary);
}
</style>
