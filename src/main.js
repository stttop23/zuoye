import { createApp } from 'vue'

// Element Plus：全量引入（对小白最友好，官网文档复制即用）
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import { ElMessage } from 'element-plus'

import App from './App.vue'
import router from './router'
import { initializeWorkspace } from './composables/appStore'

// ⚠️ 全局样式必须放在 Element Plus 之后引入，否则没法覆盖组件库默认样式
import '@/assets/styles/variables.css'
import '@/assets/styles/global.css'

const app = createApp(App)

// 全量注册图标组件，模板里可直接写 <el-icon><Search /></el-icon>
for (const [name, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, component)
}

app.use(ElementPlus, { locale: zhCn })
app.use(router)

async function startApp() {
  let databaseError
  try {
    await initializeWorkspace()
  } catch (error) {
    databaseError = error
    console.error('SQLite 数据库连接失败', error)
  }

  app.mount('#app')
  if (databaseError) {
    ElMessage.error(
      `数据库连接失败：${databaseError.message}。当前显示本地缓存，数据修改不会保存到数据库。`,
    )
  }
}

startApp()
