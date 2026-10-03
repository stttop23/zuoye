<template>
  <div class="notice">
    <!-- ==================== 页头 ==================== -->
    <div class="page-head">
      <div>
        <h2 class="page-title">公告通知</h2>
        <p class="page-desc">查看学生会发布的通知公告，支持关键词搜索与分页浏览</p>
      </div>
      <el-button type="primary" @click="onPublish">
        <el-icon><Plus /></el-icon>
        发布公告
      </el-button>
    </div>

    <!-- ==================== 搜索栏 ==================== -->
    <el-card shadow="never" class="section">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="关键词">
          <el-input
            v-model="keyword"
            placeholder="搜索公告标题或发布人"
            clearable
            style="width: 260px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="类型">
          <el-select v-model="typeFilter" placeholder="全部类型" clearable style="width: 140px">
            <el-option label="通知" value="通知" />
            <el-option label="活动" value="活动" />
            <el-option label="制度" value="制度" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- ==================== 表格 ==================== -->
    <el-card shadow="never" class="section">
      <el-table v-loading="loading" :data="pagedList" stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="title" label="公告标题" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="notice__title" @click="openDetail(row)">{{ row.title }}</span>
            <el-tag v-if="row.top" type="danger" size="small" effect="light" class="notice__top">
              置顶
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="typeTagMap[row.type]" size="small" effect="plain">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="发布人" width="120" align="center" />
        <el-table-column prop="publishTime" label="发布时间" width="180" align="center" />
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openDetail(row)">
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="没有找到符合条件的公告" />
        </template>
      </el-table>

      <!-- ==================== 分页 ==================== -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
          :total="filteredList.length"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- ==================== 详情弹窗 ==================== -->
    <el-dialog v-model="dialogVisible" :title="currentNotice?.title" width="640px">
      <el-descriptions :column="2" border size="default">
        <el-descriptions-item label="发布人">{{ currentNotice?.author }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentNotice?.type }}</el-descriptions-item>
        <el-descriptions-item label="发布时间" :span="2">
          {{ currentNotice?.publishTime }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="notice__content">{{ currentNotice?.content }}</div>

      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="onConfirmRead">我已知晓</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * ⚠️ 说明：本页数据为「假数据」，目的是让前端页面先跑起来。
 * 后端接口就绪后，把 allNotices 换成接口请求即可。
 * 分页是前端分页（先把全部数据过滤，再切片），数据量大时要改成后端分页。
 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Search, View } from '@element-plus/icons-vue'

/** 类型 -> 标签颜色 */
const typeTagMap = { 通知: 'primary', 活动: 'success', 制度: 'warning' }

/** ---------- 假数据 ---------- */
const allNotices = ref([
  {
    id: 12,
    title: '关于期末学生工作总结的通知',
    type: '通知',
    author: '张晶',
    publishTime: '2026-10-02 09:15',
    top: true,
    content:
      '请各部门于 10 月 15 日前提交本学期工作总结，内容包括工作成果、存在问题及下学期计划。总结需以 Word 文档形式发送至学生会邮箱。',
  },
  {
    id: 11,
    title: '校园文化活动报名开始啦',
    type: '活动',
    author: '罗欣雨',
    publishTime: '2026-10-01 14:30',
    top: true,
    content:
      '本届校园文化活动共设 8 个项目，报名截止时间为 10 月 10 日 18:00，欢迎各班级积极组织参与。',
  },
  {
    id: 10,
    title: '学生会例会时间调整说明',
    type: '通知',
    author: '刘皖',
    publishTime: '2026-09-28 16:40',
    top: false,
    content: '因课程安排冲突，本周例会调整至周三 19:00，地点仍为综合楼 302 教室。',
  },
  {
    id: 9,
    title: '学生考勤管理制度（修订版）',
    type: '制度',
    author: '张晶',
    publishTime: '2026-09-25 11:20',
    top: false,
    content: '本次修订主要明确请假审批流程与销假要求，自发布之日起执行。',
  },
  {
    id: 8,
    title: '国庆假期值班安排',
    type: '通知',
    author: '刘皖',
    publishTime: '2026-09-23 08:50',
    top: false,
    content: '假期期间每日安排 2 名同学值班，具体名单见附件。',
  },
  {
    id: 7,
    title: '宿舍卫生检查结果公示',
    type: '通知',
    author: '罗欣雨',
    publishTime: '2026-09-20 10:00',
    top: false,
    content: '本次检查共评出优秀宿舍 12 间，具体名单已张贴于宿舍楼下公告栏。',
  },
  {
    id: 6,
    title: '志愿服务招募通知',
    type: '活动',
    author: '张晶',
    publishTime: '2026-09-18 15:10',
    top: false,
    content: '社区支教志愿服务招募 20 人，服务时间为每周六上午。',
  },
  {
    id: 5,
    title: '关于使用统一开发规范的说明',
    type: '制度',
    author: '刘皖',
    publishTime: '2026-09-15 09:00',
    top: false,
    content: '为保证代码风格一致，全组统一使用 Prettier 格式化，颜色统一走 CSS 变量。',
  },
  {
    id: 4,
    title: '新生入学教育安排',
    type: '通知',
    author: '罗欣雨',
    publishTime: '2026-09-12 13:45',
    top: false,
    content: '新生入学教育分三批进行，具体时间见各班级群通知。',
  },
  {
    id: 3,
    title: '班级篮球赛报名通知',
    type: '活动',
    author: '张晶',
    publishTime: '2026-09-10 17:30',
    top: false,
    content: '篮球赛即日起接受报名，每队 5 至 8 人，报名请联系体育委员。',
  },
  {
    id: 2,
    title: '关于奖学金评定工作的通知',
    type: '通知',
    author: '刘皖',
    publishTime: '2026-09-08 10:20',
    top: false,
    content: '奖学金评定材料提交截止时间为 9 月 20 日，请务必按时提交。',
  },
  {
    id: 1,
    title: '新学期学生干部名单公布',
    type: '通知',
    author: '罗欣雨',
    publishTime: '2026-09-01 09:00',
    top: false,
    content: '经个人申报与面试考评，新学期学生干部名单现予公布。',
  },
])

/** ---------- 搜索 / 筛选 ---------- */
const keyword = ref('')
const typeFilter = ref('')

const filteredList = computed(() => {
  const kw = keyword.value.trim()
  return allNotices.value
    .filter((item) => {
      const matchKeyword =
        !kw || item.title.includes(kw) || item.author.includes(kw) || item.content.includes(kw)
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

function openDetail(row) {
  currentNotice.value = row
  dialogVisible.value = true
}

function onConfirmRead() {
  dialogVisible.value = false
  ElMessage.success('已标记为已读')
}

function onPublish() {
  ElMessage.info('发布功能由后端接口支持，当前为前端演示版本')
}
</script>

<style scoped>
.notice {
  display: flex;
  flex-direction: column;
  gap: var(--st-gap-base);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.section {
  border: none;
}

.section :deep(.el-form-item) {
  margin-bottom: 0;
}

.notice__title {
  color: var(--st-text-primary);
  cursor: pointer;
}

.notice__title:hover {
  color: var(--st-primary);
}

.notice__top {
  margin-left: 8px;
}

.notice__content {
  margin-top: var(--st-gap-base);
  padding: var(--st-gap-base);
  font-size: 14px;
  line-height: 1.8;
  color: var(--st-text-regular);
  background: var(--st-bg-page);
  border-radius: var(--st-radius-sm);
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--st-gap-base);
}
</style>
