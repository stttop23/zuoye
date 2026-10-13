<template>
  <el-card shadow="never" class="section">
    <!--
      手机：只列标题，点标题看详情。
      六列表格在 390px 宽下要横向滚，序号/发布人/发布时间都挤成一团，
      而那些信息在详情弹窗里都有 —— 列表上真正需要的只有「叫什么」。
    -->
    <template v-if="isMobile">
      <ul v-if="list.length" class="notice-list">
        <li v-for="row in list" :key="row.id">
          <button type="button" class="notice-list__item" @click="emit('detail', row)">
            <span class="notice-list__title">{{ row.title }}</span>
            <el-tag v-if="row.top" type="danger" size="small" effect="light">置顶</el-tag>
          </button>
        </li>
      </ul>
      <el-empty v-else :image-size="72" description="没有找到符合条件的公告" />
    </template>

    <el-table v-else v-loading="loading" :data="list" stripe style="width: 100%">
      <el-table-column type="index" label="序号" width="70" align="center" />
      <el-table-column prop="title" label="公告标题" min-width="240" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="notice__title" @click="emit('detail', row)">{{ row.title }}</span>
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
          <el-button type="primary" link @click="emit('detail', row)">
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
        :total="total"
        :layout="paginationLayout"
        background
        @size-change="emit('size-change', $event)"
      />
    </div>
  </el-card>
</template>

<script setup>
/**
 * 公告列表：手机上一列标题，电脑上是表格。
 * 列表切片、总数、每页条数都由父级算好后传进来。
 */
import { computed } from 'vue'
import { View } from '@element-plus/icons-vue'
import { useIsMobile } from '@/composables/useMediaQuery'

defineProps({
  list: { type: Array, required: true },
  total: { type: Number, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['detail', 'size-change'])

const isMobile = useIsMobile()

/** 手机上「总数/每页条数/跳页」这一长串放不下，只留翻页 */
const paginationLayout = computed(() =>
  isMobile.value ? 'prev, pager, next' : 'total, sizes, prev, pager, next, jumper',
)

/** 类型 -> 标签颜色 */
const typeTagMap = { 通知: 'primary', 活动: 'success', 制度: 'warning' }

const currentPage = defineModel('currentPage', { type: Number, default: 1 })
const pageSize = defineModel('pageSize', { type: Number, default: 5 })
</script>

<style scoped>
.section {
  border: none;
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

/* ---------- 手机版：只有标题的一列清单 ---------- */
.notice-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.notice-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 14px 0;
  border: none;
  border-bottom: 1px solid var(--st-border-color-hair);
  font: inherit;
  font-size: 15px;
  color: var(--st-text-primary);
  text-align: left;
  appearance: none;
  background: none;
  cursor: pointer;
  transition: color var(--st-duration-fast) var(--st-ease);
}

.notice-list li:last-child .notice-list__item {
  border-bottom: none;
}

.notice-list__item:active {
  color: var(--st-primary);
}

.notice-list__title {
  flex: 1;
  min-width: 0;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--st-gap-base);
}

@media (max-width: 768px) {
  .pagination {
    justify-content: center;
  }
}
</style>
