import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    sourcemap: false,      // 生产环境关闭 source map
    minify: 'terser',      // 混淆压缩代码
    terserOptions: {
      compress: {
        drop_console: true,   // 移除所有 console.log
        drop_debugger: true   // 移除 debugger
      }
    }
  }
})
