<template>
  <el-card shadow="never" class="section">
    <el-table v-loading="loading" :data="list" stripe style="width: 100%">
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
        layout="total, sizes, prev, pager, next, jumper"
        background
        @size-change="emit('size-change')"
      />
    </div>
  </el-card>
</template>

<script setup>
/**
 * 公告表格：只负责展示当前页数据和分页控件。
 * 列表切片、总数、每页条数都由父级算好后传进来。
 */
import { View } from '@element-plus/icons-vue'

defineProps({
  list: { type: Array, required: true },
  total: { type: Number, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['detail', 'size-change'])

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

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--st-gap-base);
}
</style>
