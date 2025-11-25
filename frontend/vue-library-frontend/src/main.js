// 导入 Element Plus 的 CSS 样式文件
import 'element-plus/dist/index.css'

// 导入 Vue 的核心功能
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 导入 Element Plus 库
import ElementPlus from 'element-plus'
// 导入 Element Plus 图标库
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 全局注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 告诉 Vue 我们要使用路由和 Element Plus
app.use(router)
app.use(ElementPlus)

// 将应用挂载到页面上
app.mount('#app')