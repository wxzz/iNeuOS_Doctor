import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 扩展 Window 接口以支持微信 JSAPI
declare global {
  interface Window {
    wx?: any
  }
}

const app = createApp(App)

app.use(router)

app.mount('#app')
