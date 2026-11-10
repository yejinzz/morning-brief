import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { App } from './App';
import { applyTheme } from './lib/theme';
import './index.css';

// 초기 테마 적용(플래시 최소화)
applyTheme(
  (typeof localStorage !== 'undefined' &&
    (localStorage.getItem('mb.theme') as 'light' | 'dark' | 'system' | null)) ||
    'system',
);

const rootEl = document.getElementById('root');
if (!rootEl) throw new Error('#root 요소를 찾을 수 없습니다.');

createRoot(rootEl).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
