import { CATEGORY_LABELS, type Briefing } from './types/contracts';

// M0: 계약 타입을 실제로 사용하는 최소 스켈레톤. 전체 UI/조회는 M3 에서 구현.
// 아래 Mock 은 Python 쪽 tests/fixtures/briefing.json 과 동일한 형태(계약 검증용).
const MOCK_BRIEFING: Briefing = {
  brief_date: '2026-11-10',
  headline: 'AI 에이전트 도구 표준 변경과 주요 웹 프레임워크 보안 패치가 오늘의 핵심입니다.',
  collected_count: 42,
  high_count: 2,
  est_read_minutes: 4,
  status: 'ready',
  generated_at: '2026-11-10T07:04:00+09:00',
  articles: [
    {
      id: 'a1',
      category: 'ai',
      title: '주요 LLM 제공사, 에이전트 도구 호출 표준 업데이트 발표',
      summary: '에이전트 도구 호출 표준의 호환성 변경이 발표되었다.',
      rationale: '다수 AI 플랫폼 통합에 직접적인 호환성 영향.',
      dev_relevance: '에이전트/도구 호출 구현 서비스는 업데이트 필요 가능성.',
      source: 'Google News',
      published_at: '2026-11-10T00:12:00+09:00',
      url: 'https://example.com/ai/agent-tool-standard',
      impact: 'HIGH',
      evidence_basis: 'title_desc_only',
      display_order: 1,
      is_high: true,
    },
  ],
};

export function App(): React.JSX.Element {
  const b = MOCK_BRIEFING;
  return (
    <main>
      <header>
        <h1>Morning Brief</h1>
        <p>
          {b.brief_date} · 수집 {b.collected_count} · HIGH {b.high_count} · 약 {b.est_read_minutes}
          분
        </p>
      </header>
      {b.headline && <p>{b.headline}</p>}
      <ul>
        {b.articles.map((a) => (
          <li key={a.id}>
            <strong>[{CATEGORY_LABELS[a.category]}]</strong> {a.title}
          </li>
        ))}
      </ul>
      <p style={{ opacity: 0.6 }}>M0 스켈레톤 · 전체 UI는 M3에서 구현됩니다.</p>
    </main>
  );
}
