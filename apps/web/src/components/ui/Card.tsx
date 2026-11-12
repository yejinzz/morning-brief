import type { ElementType, ReactNode } from 'react';

interface CardProps {
  as?: ElementType;
  className?: string;
  children: ReactNode;
}

// 글래스 카드 표면(반투명 + 블러 + 엣지 하이라이트). 뉴모피즘 아님.
export function Card({ as: Tag = 'div', className = '', children }: CardProps) {
  return <Tag className={`card rounded-2xl ${className}`}>{children}</Tag>;
}
