// 선택 카테고리에 주요 뉴스 없음.

import { StatusMessage } from './StatusMessage';

export function CategoryEmptyView() {
  return <StatusMessage>이 카테고리의 주요 뉴스가 없어요.</StatusMessage>;
}
