// 홈/브리핑 화면 (M3). 오늘(/) 또는 지난 날짜(/d/:date).

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  ArticleCard,
  BriefingHeader,
  CategoryEmptyView,
  CategoryTabs,
  EmptyHighView,
  ErrorView,
  GeneratingView,
  LoadingView,
  NotFoundView,
  OfflineBanner,
  OneLiner,
  StatsBar,
} from '@/components/briefing';
import { useBriefing } from '@/hooks/useBriefing';
import { useOnline } from '@/hooks/useOnline';
import { useReadState } from '@/hooks/useReadState';
import { categoryCounts, filterByTab, type Tab } from '@/lib/tabs';

export function HomeRoute() {
  const { date } = useParams();
  const state = useBriefing(date ?? null);
  const online = useOnline();
  const { isRead, toggle } = useReadState();
  const [tab, setTab] = useState<Tab>('all');

  if (state.status === 'loading') return <LoadingView />;
  if (state.status === 'error') return <ErrorView message={state.error} />;

  const briefing = state.briefing;
  if (!briefing) return <NotFoundView />;

  const counts = categoryCounts(briefing.articles);
  const visible = filterByTab(briefing.articles, tab);

  return (
    <div className="space-y-5">
      {!online && <OfflineBanner generatedAt={briefing.generated_at} />}
      <BriefingHeader briefing={briefing} />
      {briefing.headline && <OneLiner text={briefing.headline} />}
      <StatsBar briefing={briefing} />
      <CategoryTabs active={tab} counts={counts} onSelect={setTab} />

      {briefing.status === 'generating' ? (
        <GeneratingView />
      ) : briefing.status === 'empty_high' || briefing.high_count === 0 ? (
        <EmptyHighView />
      ) : visible.length === 0 ? (
        <CategoryEmptyView />
      ) : (
        <ul className="space-y-5">
          {visible.map((card) => (
            <li key={card.id}>
              <ArticleCard card={card} read={isRead(card.id)} onToggleRead={toggle} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
