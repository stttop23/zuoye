<template>
  <div class="placeholder">
    <el-card shadow="never">
      <el-result icon="info" title="待办事项（开发中）">
        <template #sub-title>
          <p>
            本页由
            <strong>张晶</strong>
            负责开发，当前是占位页面。
          </p>
          <p>
            你的开发分支是
            <code>feature/zhang-jing</code>
            ，要改的文件只有
            <code>src/views/TodoView.vue</code>
            这一个。
          </p>
          <p>
            完整操作步骤见
            <code>docs/队友开发手册.md</code>
          </p>
        </template>

        <template #extra>
          <el-descriptions :column="1" border size="small" class="tip">
            <el-descriptions-item label="切换分支">
              git checkout feature/zhang-jing
            </el-descriptions-item>
            <el-descriptions-item label="访问地址">http://localhost:5173/todo</el-descriptions-item>
            <el-descriptions-item label="参考实现">
              切到你的分支后，这里会有一份能直接跑起来的待办页示例
            </el-descriptions-item>
          </el-descriptions>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
// 占位页：切到 feature/zhang-jing 分支后这里会替换成完整的待办页示例。
// 路由已配好，不需要改 router。
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
