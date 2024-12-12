import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: '0.0.0.0', // 開発サーバーのホスト
    port: 5174       // 開発サーバーのポート
  },
  preview: {
    host: '0.0.0.0', // プレビューサーバーのホスト
    port: 5174       // プレビューサーバーのポート
  }
});
