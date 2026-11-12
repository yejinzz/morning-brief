import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface IconButtonProps {
  label: string;
  to?: string;
  onClick?: () => void;
  children: ReactNode;
  className?: string;
}

// 원형 뉴모피즘 아이콘 버튼(컨트롤). to 가 있으면 링크, 없으면 버튼.
export function IconButton({ label, to, onClick, children, className = '' }: IconButtonProps) {
  const cls = `neu-btn flex h-11 w-11 items-center justify-center text-mute-light dark:text-mute-dark ${className}`;
  if (to) {
    return (
      <Link to={to} aria-label={label} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" aria-label={label} onClick={onClick} className={cls}>
      {children}
    </button>
  );
}
