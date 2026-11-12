import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ArticleCard } from './ArticleCard';
import type { ArticleCard as Card } from '@/types';

const card: Card = {
  id: 'a1',
  category: 'dev',
  title: '보안 패치 공개',
  summary: '요약 내용',
  keywords: ['원격 코드 실행', '즉시 업그레이드'],
  rationale: '근거 내용',
  source: 'Hacker News',
  published_at: '2026-11-10T02:30:00+09:00',
  url: 'https://example.com/x',
  impact: 'HIGH',
  evidence_basis: 'title_desc_only',
  display_order: 1,
  is_high: true,
};

describe('ArticleCard', () => {
  it('제목·요약·근거·출처 링크를 렌더한다', () => {
    render(<ArticleCard card={card} read={false} onToggleRead={() => {}} />);
    expect(screen.getByText('보안 패치 공개')).toBeInTheDocument();
    expect(screen.getByText('요약 내용')).toBeInTheDocument();
    expect(screen.getByText(/근거 내용/)).toBeInTheDocument();
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', 'https://example.com/x');
  });

  it('키워드를 칩으로 렌더한다', () => {
    render(<ArticleCard card={card} read={false} onToggleRead={() => {}} />);
    expect(screen.getByText('#원격 코드 실행')).toBeInTheDocument();
    expect(screen.getByText('#즉시 업그레이드')).toBeInTheDocument();
  });

  it('읽음 버튼 클릭 시 토글 핸들러를 호출한다', async () => {
    const onToggle = vi.fn();
    render(<ArticleCard card={card} read={false} onToggleRead={onToggle} />);
    await userEvent.click(screen.getByRole('button', { name: /읽음/ }));
    expect(onToggle).toHaveBeenCalledWith('a1');
  });
});
