// 오프라인: 저장된 마지막 브리핑 안내 배너.

export function OfflineBanner({ generatedAt }: { generatedAt?: string | null }) {
  return (
    <div className="flex items-center gap-2 rounded-full bg-black/5 px-4 py-2 text-xs text-accent dark:bg-white/10">
      <span className="accent-glow inline-block h-1.5 w-1.5 rounded-full bg-accent" aria-hidden />
      오프라인 — 저장된 마지막 브리핑{generatedAt ? ` (${generatedAt})` : ''}
    </div>
  );
}
