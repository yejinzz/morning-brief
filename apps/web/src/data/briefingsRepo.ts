// 브리핑 데이터 접근 계층 (M3). UI 는 이 인터페이스만 의존.
// 환경이 구성되면 Supabase(anon 읽기), 아니면 Mock.

import type { Briefing } from '@/types';
import { supabaseConfigured } from '@/lib/env';
import { getMockBriefing, mockAvailableDates, MOCK_LATEST_DATE } from './mockData';
import { SupabaseBriefingsRepo } from './briefingsRepoSupabase';

export interface BriefingsRepo {
  getByDate(date: string): Promise<Briefing | null>;
  latestDate(): Promise<string | null>;
  availableDates(): Promise<string[]>;
}

/** 지연·네트워크를 흉내 내는 Mock 저장소. */
class MockBriefingsRepo implements BriefingsRepo {
  async getByDate(date: string): Promise<Briefing | null> {
    return getMockBriefing(date);
  }
  async latestDate(): Promise<string | null> {
    return MOCK_LATEST_DATE;
  }
  async availableDates(): Promise<string[]> {
    return mockAvailableDates();
  }
}

// 환경 구성 시 Supabase(anon 읽기), 아니면 Mock.
export const repo: BriefingsRepo = supabaseConfigured()
  ? new SupabaseBriefingsRepo()
  : new MockBriefingsRepo();
