<template>
  <el-dialog v-model="visible" :title="notice?.title" width="640px">
    <template #header>
      <div class="notice-dialog__head">
        <h3 class="notice-dialog__title">{{ notice?.title }}</h3>
        <el-tag v-if="notice?.top" type="danger" size="small" effect="light">置顶</el-tag>
      </div>
    </template>

    <el-descriptions :column="2" border size="small">
      <el-descriptions-item label="发布人">{{ notice?.author }}</el-descriptions-item>
      <el-descriptions-item label="类型">
        <el-tag :type="typeTag" size="small" effect="dark">{{ notice?.type }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="发布时间" :span="2">
        {{ notice?.publishTime }}
      </el-descriptions-item>
    </el-descriptions>

    <div class="notice__content">
      <p v-if="notice?.content">{{ notice.content }}</p>
      <p v-else class="notice__empty">暂无正文</p>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
      <el-button class="notice-dialog__confirm" @click="emit('confirm-read')">
        我已知晓
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 公告详情弹窗：只负责展示，开与关由父级 v-model 控制。
 */
import { computed } from 'vue'

const props = defineProps({
  notice: { type: Object, default: null },
})

const emit = defineEmits(['confirm-read'])

const visible = defineModel({ type: Boolean, default: false })

/** 类型 → 标签颜色（和列表页 NoticeTable 保持一致） */
const TYPE_TAGS = { 通知: 'primary', 活动: 'success', 制度: 'warning' }
const typeTag = computed(() => TYPE_TAGS[props.notice?.type] ?? 'info')
</script>

<style scoped>
/* 标题：置顶标识跟标题同一行，左侧竖条用品牌渐变（和区块标题同一套语言） */
.notice-dialog__head {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 32px;
  padding-left: 12px;
}

.notice-dialog__head::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 4px;
  height: 16px;
  background: var(--st-gradient-brand);
  border-radius: var(--st-radius-pill);
  transform: translateY(-50%);
}

.notice-dialog__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--st-text-primary);
}

/* 信息表的标签列：中性灰底 + 次要色文字，让「值」和彩色类型标签更突出
   （别用浅蓝底 —— 类型标签的浅蓝底会和它糊成一片） */
:deep(.el-descriptions__label.is-bordered-label) {
  font-weight: 500;
  color: var(--st-text-secondary);
  background: var(--st-bg-sunken);
}

/* 正文：和上方信息表用一条细线分开；行高放大、首行缩进两字（中文通知的排版习惯）。
   pre-line 让发布公告时敲的换行能保留下来。 */
.notice__content {
  margin-top: var(--st-gap-base);
  padding-top: var(--st-gap-base);
  font-size: 14px;
  line-height: 1.9;
  color: var(--st-text-primary);
  border-top: 1px solid var(--st-border-color-light);
}

.notice__content p {
  margin: 0;
  text-indent: 2em;
  white-space: pre-line;
}

.notice__empty {
  color: var(--st-text-secondary);
  text-align: center;
  text-indent: 0;
}

/* 确认按钮：品牌渐变（渐变只用在这一点上，不铺满）
   ⚠️ 去掉 type="primary" 之后 EP 会把文字色回退成深灰，压在渐变上对比度不够，必须显式给白 */
.notice-dialog__confirm {
  font-weight: 500;
  color: var(--st-text-inverse);
  background-image: var(--st-gradient-brand);
  border-color: transparent;
  box-shadow: var(--st-shadow-grad);
}

.notice-dialog__confirm:hover,
.notice-dialog__confirm:focus {
  color: var(--st-text-inverse);
  background-image: var(--st-gradient-brand);
  border-color: transparent;
  box-shadow: var(--st-shadow-grad);
  filter: brightness(1.07);
}
</style>
