// 상태 UI. docs/06 §3: 로딩/생성중/HIGH 0건/카테고리 0건/오류/오프라인. 뉴모피즘.

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <div className="neu-inset rounded-neu px-6 py-14 text-center text-sm text-mute-light dark:text-mute-dark">
      {children}
    </div>
  );
}

export function LoadingView() {
  return (
    <div className="space-y-5" aria-busy="true" aria-label="불러오는 중">
      {[0, 1, 2].map((i) => (
        <div key={i} className="neu-raised h-28 animate-pulse rounded-neu" />
      ))}
    </div>
  );
}

export function GeneratingView() {
  return <Centered>오늘 브리핑을 준비하고 있어요.</Centered>;
}

export function EmptyHighView() {
  return <Centered>오늘은 꼭 챙길 만한 뉴스가 없어요. 느긋한 아침 되세요.</Centered>;
}

export function CategoryEmptyView() {
  return <Centered>이 카테고리의 주요 뉴스가 없어요.</Centered>;
}

export function ErrorView({ message }: { message?: string }) {
  return (
    <Centered>
      <p>최신 브리핑을 불러오지 못했어요.</p>
      {message && <p className="mt-1 text-xs opacity-70">{message}</p>}
    </Centered>
  );
}

export function NotFoundView() {
  return <Centered>해당 날짜의 브리핑이 없어요.</Centered>;
}

export function OfflineBanner({ generatedAt }: { generatedAt?: string | null }) {
  return (
    <div className="neu-inset flex items-center gap-2 rounded-full px-4 py-2.5 text-xs text-high">
      <span className="inline-block h-2 w-2 rounded-full bg-high" aria-hidden />
      오프라인 — 저장된 마지막 브리핑{generatedAt ? ` (${generatedAt})` : ''}
    </div>
  );
}
