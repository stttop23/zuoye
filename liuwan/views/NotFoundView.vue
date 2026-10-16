<template>
  <div class="not-found">
    <el-result icon="warning" title="404" sub-title="抱歉，你访问的页面不存在">
      <template #extra>
        <el-button type="primary" @click="router.push('/dashboard')">返回工作台</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style scoped>
/* v2：整页居中留白，窄屏时四周留出令牌间距，别让 404 卡片贴住屏幕边 */
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--st-gap-base);
  background: var(--st-bg-page);
}
</style>
