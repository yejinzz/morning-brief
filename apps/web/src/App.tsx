import { Route, Routes } from 'react-router-dom';
import { HomeRoute } from './routes/HomeRoute';
import { SettingsRoute } from './routes/SettingsRoute';

export function App() {
  return (
    <div className="mx-auto min-h-full max-w-reader px-5 py-7">
      <Routes>
        <Route path="/" element={<HomeRoute />} />
        <Route path="/d/:date" element={<HomeRoute />} />
        <Route path="/settings" element={<SettingsRoute />} />
      </Routes>
    </div>
  );
}
