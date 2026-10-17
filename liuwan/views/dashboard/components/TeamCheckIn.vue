<template>
  <!-- 管理员专属：全组今天的打卡情况（学生只看自己的，那一块在欢迎卡里） -->
  <el-card shadow="never" class="team-checkin st-fade-up st-delay-1">
    <div class="team-checkin__head">
      <span class="section__title">今日打卡</span>
      <span class="team-checkin__meta">{{ doneCount }} / {{ rows.length }} 人已打卡</span>
    </div>

    <ul class="team-checkin__list">
      <li v-for="row in rows" :key="row.name" class="team-checkin__item">
        <el-avatar :size="32" :class="['team-checkin__avatar', { 'is-done': row.done }]">
          {{ row.name.slice(0, 1) }}
        </el-avatar>

        <div class="team-checkin__info">
          <div class="team-checkin__line">
            <strong>{{ row.name }}</strong>
            <el-tag :type="row.done ? 'success' : 'info'" size="small" effect="light">
              {{ row.done ? row.time : '未打卡' }}
            </el-tag>
          </div>
          <div class="team-checkin__place">{{ row.place || '—' }}</div>
        </div>

        <span v-if="row.streak > 0" class="team-checkin__streak">连续 {{ row.streak }} 天</span>
      </li>
    </ul>
  </el-card>
</template>

<script setup>
/**
 * 管理员的「全组今日打卡」。
 *
 * 数据来源分两半，这样才不会出现「表格里我的打卡和欢迎卡里对不上」：
 *   1. 当前登录用户 → appStore 的 checkin（真的点出来的，带定位和连续天数）
 *   2. 其他成员     → @/mock 的 TEAM_CHECKINS（演示数据）
 *
 * ⚠️ 打卡天生是「每人每天一条」的数据，真实系统里必须由后端按天返回；
 *    现在团队那部分没法真的跨设备，只能演示。接后端时把 rows 换成接口数据即可。
 */
import { computed } from 'vue'
import { checkin } from '@/composables/appStore'
import { useUserProfile } from '@/composables/userProfile'
import { MEMBERS, TEAM_CHECKINS } from '@/mock'

const { userName } = useUserProfile()

/** 本地日期，别用 toISOString（UTC，会差一天） */
function dateStr(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/**
 * 地点的显示口径必须和 CheckIn.vue 一致（省市区 · POI），
 * 否则同一个地方在两处显示成两个样子。
 */
function placeText(place) {
  if (!place) return ''
  if (place.error) return place.error
  if (place.region) return place.poi ? `${place.region} · ${place.poi}` : place.region
  return place.poi || place.short || place.address || ''
}

/** 本组件打开时算一次；跨天不刷新，演示够用（和 CheckIn.vue 一致） */
const today = dateStr()

const rows = computed(() => {
  const mine = checkin.value
  const myDone = mine.lastDate === today
  // 当前用户名可能被改过，所以把它也并进来，别让人在表格里消失
  const names = [...new Set([...MEMBERS, userName.value])]

  return names.map((name) => {
    if (name === userName.value) {
      return {
        name,
        done: myDone,
        time: myDone ? mine.lastTime : '',
        place: myDone ? placeText(mine.place) : '',
        streak: myDone ? mine.streak : 0,
      }
    }

    const record = TEAM_CHECKINS.find((item) => item.name === name)
    return {
      name,
      done: Boolean(record),
      time: record?.time ?? '',
      place: record?.place ?? '',
      streak: record?.streak ?? 0,
    }
  })
})

const doneCount = computed(() => rows.value.filter((row) => row.done).length)
</script>

<style scoped>
.team-checkin__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.team-checkin__meta {
  color: var(--st-text-secondary);
  font-size: 12px;
}

.team-checkin__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.team-checkin__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--st-border-color-hair);
}

.team-checkin__item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.team-checkin__avatar {
  flex: 0 0 auto;
  color: var(--st-text-secondary);
  font-size: 13px;
  background: var(--st-bg-sunken);
}

/* 已打卡的头像用品牌渐变（只看点缀，不铺满） */
.team-checkin__avatar.is-done {
  color: var(--st-text-inverse);
  background: var(--st-gradient-brand);
}

.team-checkin__info {
  min-width: 0;
  flex: 1;
}

.team-checkin__line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.team-checkin__line strong {
  color: var(--st-text-primary);
  font-size: 14px;
  font-weight: 500;
}

.team-checkin__place {
  margin-top: 3px;
  overflow: hidden;
  color: var(--st-text-secondary);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-checkin__streak {
  flex: 0 0 auto;
  color: var(--st-text-secondary);
  font-size: 12px;
}
</style>
