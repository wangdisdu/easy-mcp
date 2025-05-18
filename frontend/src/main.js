import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import './assets/styles/global.css'

import App from './App.vue'
import router from './router'
import { configureMonaco } from './utils/monaco-config'
import './utils/axios-config' // Import axios configuration

// Configure Monaco Editor
configureMonaco()

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(Antd)

app.mount('#app')
