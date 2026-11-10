import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// 모바일 우선 PWA. 매니페스트/서비스워커는 M3 에서 확장.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Morning Brief',
        short_name: 'Morning Brief',
        description: '매일 아침 AI가 선별하는 개인용 뉴스 브리핑',
        lang: 'ko',
        display: 'standalone',
        theme_color: '#0b0f17',
        background_color: '#0b0f17',
        start_url: '/',
        icons: [],
      },
    }),
  ],
});
