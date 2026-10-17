<template>
  <div class="notice">
    <!-- ==================== 页头 ==================== -->
    <div class="page-head">
      <div>
        <h2 class="page-title">公告通知</h2>
      </div>
      <!-- 发布是管理员的活，学生看不到这个按钮。
           ⚠️ 前端藏按钮只是体验，真正的拦截得后端重验（否则绕过前端照样能发） -->
      <el-button v-if="canDo('notice.publish')" type="primary" @click="onPublish">
        <el-icon><Plus /></el-icon>
        发布公告
      </el-button>
    </div>

    <!-- ==================== 搜索栏（子组件） ==================== -->
    <NoticeFilter
      v-model:keyword="keyword"
      v-model:typeFilter="typeFilter"
      @search="handleSearch"
      @reset="handleReset"
    />

    <!-- ==================== 表格 + 分页（子组件） ==================== -->
    <NoticeTable
      v-model:currentPage="currentPage"
      v-model:pageSize="pageSize"
      :list="pagedList"
      :total="filteredList.length"
      :loading="loading"
      @detail="openDetail"
      @size-change="handleSizeChange"
    />

    <!-- ==================== 详情弹窗（子组件） ==================== -->
    <NoticeDetailDialog
      v-model="dialogVisible"
      :notice="currentNotice"
      @confirm-read="onConfirmRead"
    />

    <!-- ==================== 发布弹窗（子组件） ==================== -->
    <NoticePublishDialog v-model="publishVisible" @publish="onPublished" />
  </div>
</template>

<script setup>
/**
 * ⚠️ 说明：本页数据为「假数据」，目的是让前端页面先跑起来。
 * 后端接口就绪后，把 allNotices 换成接口请求即可。
 * 分页是前端分页（先把全部数据过滤，再切片），数据量大时要改成后端分页。
 *
 * 本页已拆成三个子组件，都在 ./components/ 下：
 * NoticeFilter（搜索栏）、NoticeTable（表格+分页）、NoticeDetailDialog（详情弹窗）
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import NoticeFilter from './components/NoticeFilter.vue'
import NoticeTable from './components/NoticeTable.vue'
import NoticeDetailDialog from './components/NoticeDetailDialog.vue'
import NoticePublishDialog from './components/NoticePublishDialog.vue'
import { nextId, notices } from '@/composables/appStore'
import { useUserProfile } from '@/composables/userProfile'
import { usePermissions } from '@/composables/permissions'
import { consumeCommand, pendingCommand } from '@/composables/aiAgent'

/** 谁能发布公告（见 src/composables/permissions.js） */
const { canDo } = usePermissions()

/** 发布人就是当前用户 */
const { userName } = useUserProfile()

/**
 * 公告数据统一放在 @/composables/appStore —— 首页的「最新公告」、四个统计数字、
 * 顶栏通知中心、AI 助手读的都是同一份（以前这里内联一整份、首页又手抄一份，
 * 同一个「校园文化活动报名开始啦」首页写 09-20、这里写 10-01）。
 * 顺带好处：appStore 会自动写 localStorage，刷新不再丢。
 */
const allNotices = notices

/** ---------- 搜索 / 筛选 ---------- */
const keyword = ref('')
const typeFilter = ref('')

const filteredList = computed(() => {
  const kw = keyword.value.trim()
  return allNotices.value
    .filter((item) => {
      const matchKeyword =
        !kw ||
        item.title.includes(kw) ||
        item.author.includes(kw) ||
        (item.content || '').includes(kw)
      const matchType = !typeFilter.value || item.type === typeFilter.value
      return matchKeyword && matchType
    })
    .sort((a, b) => Number(b.top) - Number(a.top) || b.id - a.id)
})

/** ---------- 分页 ---------- */
const currentPage = ref(1)
const pageSize = ref(5)

const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

// 筛选条件变化时回到第一页，避免停留在空页
watch([keyword, typeFilter], () => {
  currentPage.value = 1
})

const loading = ref(false)

function handleSearch() {
  currentPage.value = 1
  loading.value = true
  // 模拟网络请求，让 loading 有效果（答辩演示更好看）
  setTimeout(() => {
    loading.value = false
    ElMessage.success(`共找到 ${filteredList.value.length} 条公告`)
  }, 300)
}

function handleReset() {
  keyword.value = ''
  typeFilter.value = ''
  currentPage.value = 1
}

function handleSizeChange(size) {
  pageSize.value = size
  currentPage.value = 1
}

/** ---------- 详情弹窗 ---------- */
const dialogVisible = ref(false)
const currentNotice = ref(null)

/** ---------- 发布弹窗 ---------- */
const publishVisible = ref(false)

function openDetail(row) {
  currentNotice.value = row
  dialogVisible.value = true
}

function onConfirmRead() {
  dialogVisible.value = false
  ElMessage.success('已标记为已读')
}

function onPublish() {
  publishVisible.value = true
}

/** 发布弹窗收集完字段后抛上来，真的插进列表（首页数字、通知中心会跟着变） */
function onPublished(payload) {
  allNotices.value.unshift({
    id: nextId(allNotices.value),
    author: userName.value,
    ...payload,
  })
  keyword.value = ''
  typeFilter.value = ''
  currentPage.value = 1
  ElMessage.success('公告已发布')
}

// ---- AI 助手：「看看奖学金那条公告」→ 搜出来并直接打开详情 ----
watch(
  pendingCommand,
  () => {
    const command = consumeCommand('notice')
    if (!command || command.type !== 'notice_open') return

    keyword.value = command.keyword || ''
    typeFilter.value = ''
    currentPage.value = 1

    const hit = filteredList.value[0]
    if (!hit) {
      ElMessage.warning(`没搜到「${keyword.value}」相关的公告`)
      return
    }
    openDetail(hit)
  },
  { immediate: true },
)
</script>

<style scoped>
.notice {
  display: flex;
  flex-direction: column;
  gap: var(--st-page-gap);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

/* 搜索栏、表格、弹窗的样式已随子组件移走，见 ./components/ */
</style>
