import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // 用 @ 代表 src 目录，全组统一用这种方式写 import，不要写 ../../../
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true, // 允许局域网访问，队友/手机可以直接打开你电脑的地址预览
    port: 5173,
    open: false,
  },
})
