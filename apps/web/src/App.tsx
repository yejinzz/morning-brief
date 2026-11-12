import { Route, Routes } from 'react-router-dom';
import { HomeRoute } from './routes/HomeRoute';
import { SettingsRoute } from './routes/SettingsRoute';
import { useBodyScrollbars } from '@/hooks/useBodyScrollbars';

export function App() {
  useBodyScrollbars();

  return (
    <div className="mx-auto min-h-full max-w-[560px] px-5 py-7">
      <Routes>
        <Route path="/" element={<HomeRoute />} />
        <Route path="/d/:date" element={<HomeRoute />} />
        <Route path="/settings" element={<SettingsRoute />} />
      </Routes>
    </div>
  );
}
