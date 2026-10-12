<template>
  <el-dialog v-model="visible" :title="notice?.title" width="640px">
    <el-descriptions :column="2" border size="default">
      <el-descriptions-item label="发布人">{{ notice?.author }}</el-descriptions-item>
      <el-descriptions-item label="类型">{{ notice?.type }}</el-descriptions-item>
      <el-descriptions-item label="发布时间" :span="2">
        {{ notice?.publishTime }}
      </el-descriptions-item>
    </el-descriptions>

    <div class="notice__content">{{ notice?.content }}</div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button type="primary" @click="emit('confirm-read')">我已知晓</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 公告详情弹窗：只负责展示，开与关由父级 v-model 控制。
 */
defineProps({
  notice: { type: Object, default: null },
})

const emit = defineEmits(['confirm-read'])

const visible = defineModel({ type: Boolean, default: false })
</script>

<style scoped>
.notice__content {
  margin-top: var(--st-gap-base);
  padding: var(--st-gap-base);
  font-size: 14px;
  line-height: 1.8;
  color: var(--st-text-regular);
  background: var(--st-bg-page);
  border-radius: var(--st-radius-sm);
}
</style>
