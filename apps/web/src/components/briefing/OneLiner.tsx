// 히어로(시그니처): 오늘의 한 줄 브리핑 — 글래스 카드 + 모드별 악센트 바.

import { Card } from '@/components/ui';

export function OneLiner({ text }: { text: string }) {
  return (
    <Card as="section" className="relative overflow-hidden p-5">
      <span aria-hidden className="accent-glow absolute left-0 top-0 h-full w-1 bg-accent" />
      <p className="pl-3 text-[11px] font-semibold uppercase tracking-[0.2em] text-accent">Today</p>
      <p className="mt-1.5 pl-3 text-[17px] font-semibold leading-relaxed">{text}</p>
    </Card>
  );
}
