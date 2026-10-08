<template>
  <el-card shadow="never" class="section">
    <el-form :inline="true" @submit.prevent>
      <el-form-item label="关键词">
        <el-input
          v-model="keyword"
          placeholder="搜索公告标题或发布人"
          clearable
          style="width: 260px"
          @keyup.enter="emit('search')"
          @clear="emit('search')"
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
        <el-button type="primary" @click="emit('search')">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="emit('reset')">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
/**
 * 搜索栏：只管收集关键词和类型。
 * 两个条件用 v-model 双向绑定出去，过滤逻辑由父级负责。
 */
import { Refresh, Search } from '@element-plus/icons-vue'

const keyword = defineModel('keyword', { type: String, default: '' })
const typeFilter = defineModel('typeFilter', { type: String, default: '' })

const emit = defineEmits(['search', 'reset'])
</script>

<style scoped>
.section {
  border: none;
}

.section :deep(.el-form-item) {
  margin-bottom: 0;
}
</style>
