// 상태 UI (M3). docs/06 §3: 로딩/생성중/HIGH 0건/카테고리 0건/오류/오프라인.

function Centered({ children }: { children: React.ReactNode }) {
  return <div className="py-16 text-center text-sm text-slate-500">{children}</div>;
}

export function LoadingView() {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="불러오는 중">
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-100 dark:bg-slate-800" />
      ))}
    </div>
  );
}

export function GeneratingView() {
  return <Centered>오늘 브리핑을 준비 중입니다.</Centered>;
}

export function EmptyHighView() {
  return <Centered>오늘은 HIGH로 분류된 뉴스가 없습니다.</Centered>;
}

export function CategoryEmptyView() {
  return <Centered>이 카테고리의 주요 뉴스가 없습니다.</Centered>;
}

export function ErrorView({ message }: { message?: string }) {
  return (
    <Centered>
      <p>최신 브리핑을 불러오지 못했습니다.</p>
      {message && <p className="mt-1 text-xs text-slate-400">{message}</p>}
    </Centered>
  );
}

export function NotFoundView() {
  return <Centered>해당 날짜의 브리핑이 없습니다.</Centered>;
}

export function OfflineBanner({ generatedAt }: { generatedAt?: string | null }) {
  return (
    <div className="rounded bg-amber-100 px-3 py-2 text-xs text-amber-900 dark:bg-amber-900/40 dark:text-amber-200">
      오프라인 — 저장된 마지막 브리핑을 표시합니다{generatedAt ? ` (${generatedAt})` : ''}.
    </div>
  );
}
