// vite.config.js
import { defineConfig } from 'vite';
import dotenv from 'dotenv';
import svelte from '@sveltejs/vite-plugin-svelte';

// .envファイルから環境変数を読み込む
dotenv.config();

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: process.env.VITE_PORT || 3000,
    host: process.env.VITE_HOST || '0.0.0.0', // グローバルアクセスを許可するために '0.0.0.0' に変更
  },
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || 'http://localhost:8000'),
  },
});
