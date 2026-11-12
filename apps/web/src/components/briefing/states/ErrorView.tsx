// 로드 실패.

import { StatusMessage } from './StatusMessage';

export function ErrorView({ message }: { message?: string }) {
  return (
    <StatusMessage>
      <p>최신 브리핑을 불러오지 못했어요.</p>
      {message && <p className="mt-1 text-xs opacity-70">{message}</p>}
    </StatusMessage>
  );
}
