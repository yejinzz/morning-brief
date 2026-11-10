/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        high: '#dc2626', // HIGH 영향도 강조색
      },
      maxWidth: {
        reader: '640px', // 모바일 우선 읽기 폭
      },
    },
  },
  plugins: [],
};
