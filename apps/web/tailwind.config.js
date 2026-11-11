/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 뉴모피즘 베이스 — 요소와 배경이 같은 색이어야 '눌림/솟음'이 보인다
        base: { light: '#e6eaf0', dark: '#2b2f3a' },
        ink: { light: '#394150', dark: '#d7dce6' }, // 본문 텍스트
        mute: { light: '#8a93a4', dark: '#8b93a3' }, // 보조 텍스트
        high: '#ef5a47', // HIGH 강조(일출 코랄)
        accent: '#5a7cc4', // 링크·포커스(새벽 블루)
      },
      borderRadius: {
        neu: '1.5rem',
      },
      maxWidth: {
        reader: '560px',
      },
      boxShadow: {
        // 솟음(raised)
        neu: '7px 7px 15px #bcc3cd, -7px -7px 15px #ffffff',
        'neu-sm': '4px 4px 9px #bcc3cd, -4px -4px 9px #ffffff',
        // 눌림(pressed/inset)
        'neu-in': 'inset 5px 5px 10px #bcc3cd, inset -5px -5px 10px #ffffff',
        'neu-in-sm': 'inset 3px 3px 6px #bcc3cd, inset -3px -3px 6px #ffffff',
        // 다크
        'neu-dark': '7px 7px 15px #1e212a, -7px -7px 15px #383d4a',
        'neu-dark-sm': '4px 4px 9px #1e212a, -4px -4px 9px #383d4a',
        'neu-dark-in': 'inset 5px 5px 10px #1e212a, inset -5px -5px 10px #383d4a',
        'neu-dark-in-sm': 'inset 3px 3px 6px #1e212a, inset -3px -3px 6px #383d4a',
      },
    },
  },
  plugins: [],
};
