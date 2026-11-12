// Mock 브리핑 데이터 (M3). 실 Supabase 연동 전 UI 개발·데모용.
// 형태는 Python tests/fixtures/briefing.json 과 동일한 계약(Briefing).

import type { Briefing } from '@/types';

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
        '주요 LLM 제공사가 에이전트 도구 호출 표준의 호환성 변경을 공식 발표했다. 기존 방식으로 통합한 서비스는 응답 포맷과 인증 흐름이 바뀌어 영향을 받을 수 있다. 제공사는 단계적 전환을 위한 마이그레이션 가이드와 호환 모드를 함께 공개했다. 전환 기한 전까지는 구버전도 당분간 병행 지원된다.',
      keywords: ['에이전트 도구 호출', '호환성 변경', '마이그레이션 가이드'],
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
      summary:
        '한국은행 금융통화위원회가 기준금리를 현 수준에서 동결하기로 결정했다. 물가 둔화 흐름과 경기 하방 위험을 함께 고려한 신중한 판단으로 해석된다. 시장의 사전 전망과 대체로 부합해 환율과 채권 시장의 충격은 제한적이었다. 다음 회의까지는 추가 인하 여부를 두고 관망세가 이어질 전망이다.',
      keywords: ['한국은행', '기준금리 동결', '금융통화위원회'],
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
      summary:
        '널리 쓰이는 웹 프레임워크에서 원격 코드 실행으로 이어질 수 있는 고위험 보안 취약점이 발견돼 최신 릴리스에서 수정됐다. 영향 범위가 넓어 해당 버전대를 쓰는 서비스는 즉시 업그레이드가 권장된다. 유지보수팀은 임시 완화책과 패치 적용 가이드를 함께 공지했다. 공개된 취약점인 만큼 악용 시도가 빠르게 늘 수 있어 신속한 대응이 필요하다.',
      keywords: ['원격 코드 실행', '고위험 취약점', '즉시 업그레이드'],
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
