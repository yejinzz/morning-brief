// Mock 브리핑 데이터 (M3). 실 Supabase 연동 전 UI 개발·데모용.
// 형태는 Python tests/fixtures/briefing.json 과 동일한 계약(Briefing).

import type { Briefing } from '../types/contracts';

const TODAY = '2026-11-10';
const YESTERDAY = '2026-11-09';

const todayBriefing: Briefing = {
  brief_date: TODAY,
  headline: "오늘은 'AI 에이전트 도구 표준 변경' 등 HIGH 3건이 주요 소식입니다.",
  collected_count: 42,
  high_count: 3,
  est_read_minutes: 4,
  status: 'ready',
  generated_at: '2026-11-10T07:04:00+09:00',
  articles: [
    {
      id: 'a1',
      category: 'ai',
      title: '주요 LLM 제공사, 에이전트 도구 호출 표준 업데이트 발표',
      summary:
        '에이전트 도구 호출 표준의 호환성 변경이 발표되었다. 기존 통합이 영향받을 수 있다. 마이그레이션 가이드가 함께 공지되었다.',
      rationale: '다수 AI 플랫폼 통합에 직접적인 호환성 영향을 주는 변화.',
      dev_relevance: '에이전트/도구 호출 구현 서비스는 클라이언트 업데이트가 필요할 수 있음.',
      source: 'Google News',
      published_at: '2026-11-10T00:12:00+09:00',
      url: 'https://example.com/ai/agent-tool-standard',
      impact: 'HIGH',
      evidence_basis: 'title_desc_only',
      display_order: 1,
      is_high: true,
    },
    {
      id: 'a2',
      category: 'economy',
      title: '한국은행 기준금리 동결 결정',
      summary: '한국은행이 기준금리를 현 수준으로 동결했다. 시장 예상과 부합한다.',
      rationale: '거시경제 전반에 광범위한 영향을 주는 통화정책 결정.',
      dev_relevance: '해당 없음',
      source: '연합뉴스',
      published_at: '2026-11-09T15:00:00+09:00',
      url: 'https://example.com/econ/base-rate',
      impact: 'HIGH',
      evidence_basis: 'full',
      display_order: 1,
      is_high: true,
    },
    {
      id: 'a3',
      category: 'dev',
      title: '널리 쓰이는 웹 프레임워크, 고위험 보안 패치 공개',
      summary: '고위험 보안 취약점이 최신 릴리스에서 수정되었다. 즉시 업그레이드가 권장된다.',
      rationale: '심각한 보안 취약점으로 개발 실무에 직접적인 조치가 필요.',
      dev_relevance: '해당 프레임워크 사용 프로젝트는 즉시 업그레이드 권장.',
      source: 'Hacker News',
      published_at: '2026-11-10T02:30:00+09:00',
      url: 'https://example.com/dev/framework-security',
      impact: 'HIGH',
      evidence_basis: 'title_desc_only',
      display_order: 1,
      is_high: true,
    },
  ],
};

// 어제: HIGH 0건(empty_high) 상태 데모
const yesterdayBriefing: Briefing = {
  brief_date: YESTERDAY,
  headline: null,
  collected_count: 28,
  high_count: 0,
  est_read_minutes: 0,
  status: 'empty_high',
  generated_at: '2026-11-09T07:02:00+09:00',
  articles: [],
};

const BY_DATE: Record<string, Briefing> = {
  [TODAY]: todayBriefing,
  [YESTERDAY]: yesterdayBriefing,
};

export const MOCK_LATEST_DATE = TODAY;

export function getMockBriefing(date: string): Briefing | null {
  return BY_DATE[date] ?? null;
}

export function mockAvailableDates(): string[] {
  return Object.keys(BY_DATE).sort((a, b) => b.localeCompare(a));
}
