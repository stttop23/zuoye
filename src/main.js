import { createApp } from 'vue'

// Element Plus：全量引入（对小白最友好，官网文档复制即用）
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

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
app.mount('#app')
