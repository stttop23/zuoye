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
/* v2：卡片统一「白底 + 发丝边 + 14px 圆角 + 一层几乎看不见的柔影」。
   以前这里写 border:none 想「去掉卡片的框」，结果 scoped 的 0,2,0 权重
   和 global.css 里 .el-card.el-card.el-card 打平、又注入得更晚，把全局
   已经给好的边界感顶掉了，白卡贴在浅灰页底上整块会「平」掉。 */
.section {
  border: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-card);
  box-shadow: var(--st-shadow-card);
}

.section :deep(.el-form-item) {
  margin-bottom: 0;
}

/* 搜索栏是内联表单，默认行距会把两个控件贴在一起，让卡片内部透口气 */
.section :deep(.el-form--inline) {
  margin-top: var(--st-gap-xs);
}

/* 窄屏：关键词框的 260px 内联宽度会把「类型 + 按钮组」挤出卡片，
   放开成弹性宽度并允许整行换行。按钮组自身在 ≤768px 下也会换行。 */
@media (max-width: 768px) {
  .section :deep(.el-input),
  .section :deep(.el-select) {
    width: 100% !important;
  }
}
</style>
