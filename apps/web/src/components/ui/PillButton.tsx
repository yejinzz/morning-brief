import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface PillButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  children: ReactNode;
}

// 뉴모피즘 토글 알약(컨트롤): 기본 솟음, active 면 눌림(inset) + 악센트.
export function PillButton({ active = false, children, className = '', ...rest }: PillButtonProps) {
  return (
    <button
      type="button"
      className={`rounded-full px-4 py-2 text-sm transition-shadow duration-150 ${
        active
          ? 'neu-inset font-semibold text-accent'
          : 'neu-raised-sm text-mute-light dark:text-mute-dark'
      } ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
