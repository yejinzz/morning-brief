import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// GitHub Pages project site 는 /<repo>/ 서브경로로 서빙된다.
// 빌드 시 base 를 주입(배포 워크플로가 VITE_BASE 를 설정), 로컬 dev/test 는 '/'.
const base = process.env.VITE_BASE ?? '/';

// 모바일 우선 PWA. 매니페스트/서비스워커 + 오프라인 앱셸 캐시.
export default defineConfig({
  base,
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        navigateFallback: `${base}index.html`,
        globPatterns: ['**/*.{js,css,html,ico,svg,webmanifest}'],
      },
      manifest: {
        name: 'Morning Brief',
        short_name: 'Morning Brief',
        description: '매일 아침 AI가 선별하는 개인용 뉴스 브리핑',
        lang: 'ko',
        display: 'standalone',
        theme_color: '#0b0f17',
        background_color: '#0b0f17',
        start_url: base,
        scope: base,
        icons: [],
      },
    }),
  ],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    css: false,
  },
});
