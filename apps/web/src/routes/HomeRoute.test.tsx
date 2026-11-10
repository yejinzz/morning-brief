import { describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HomeRoute } from './HomeRoute';

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={<HomeRoute />} />
        <Route path="/d/:date" element={<HomeRoute />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('HomeRoute', () => {
  it('오늘 브리핑의 한 줄 요약과 HIGH 카드를 보여준다', async () => {
    renderAt('/');
    await waitFor(() => expect(screen.getByText(/주요 소식입니다/)).toBeInTheDocument());
    // 전체 탭: 3개 카테고리 카드(제목은 heading 으로 조회해 요약과 구분)
    expect(screen.getByRole('heading', { name: /에이전트 도구 호출 표준/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /기준금리 동결/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /보안 패치/ })).toBeInTheDocument();
  });

  it('카테고리 탭을 누르면 해당 카테고리만 보인다', async () => {
    renderAt('/');
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /기준금리 동결/ })).toBeInTheDocument(),
    );
    await userEvent.click(screen.getByRole('button', { name: /AI·LLM/ }));
    expect(screen.getByRole('heading', { name: /에이전트 도구 호출 표준/ })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /기준금리 동결/ })).not.toBeInTheDocument();
  });

  it('HIGH 0건 날짜는 empty_high 상태를 보여준다', async () => {
    renderAt('/d/2026-11-09');
    await waitFor(() =>
      expect(screen.getByText(/HIGH로 분류된 뉴스가 없습니다/)).toBeInTheDocument(),
    );
  });

  it('존재하지 않는 날짜는 없음 상태를 보여준다', async () => {
    renderAt('/d/2020-01-01');
    await waitFor(() =>
      expect(screen.getByText(/해당 날짜의 브리핑이 없습니다/)).toBeInTheDocument(),
    );
  });
});
