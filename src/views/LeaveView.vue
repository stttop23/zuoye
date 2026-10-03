<template>
  <div class="placeholder">
    <el-card shadow="never">
      <el-result icon="info" title="请假申请（开发中）">
        <template #sub-title>
          <p>
            本页由
            <strong>罗欣雨</strong>
            负责开发，当前是占位页面。
          </p>
          <p>
            请你新建分支
            <code>feature/罗欣雨</code>
            ，把本文件内容替换成真实页面。
          </p>
        </template>

        <template #extra>
          <el-descriptions :column="1" border size="small" class="tip">
            <el-descriptions-item label="文件位置">src/views/LeaveView.vue</el-descriptions-item>
            <el-descriptions-item label="访问地址">
              http://localhost:5173/leave
            </el-descriptions-item>
            <el-descriptions-item label="建议实现">
              el-form 请假单 + el-table 请假记录 + el-dialog 详情
            </el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
// 占位页：队友开发完成后直接覆盖本文件即可，路由已配好，不需要改 router。
</script>

<style scoped>
.placeholder {
  height: 100%;
}

.tip {
  display: inline-block;
  text-align: left;
}

code {
  padding: 2px 6px;
  font-family: Consolas, Monaco, monospace;
  color: var(--st-primary);
  background: var(--st-primary-light);
  border-radius: var(--st-radius-sm);
}
</style>
