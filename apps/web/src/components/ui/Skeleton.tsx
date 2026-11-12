// 로딩 스켈레톤(카드 표면 + 펄스).
export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`card animate-pulse rounded-2xl ${className}`} />;
}
