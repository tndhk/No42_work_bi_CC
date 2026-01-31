import type { Layout } from 'react-grid-layout';
import type { LayoutItem } from '@/types/dashboard';

/**
 * LayoutItem 配列を react-grid-layout の Layout 配列に変換
 */
export function toRGLLayout(items: LayoutItem[]): Layout[] {
  return items.map((item) => ({
    i: item.card_id,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
  }));
}

/**
 * react-grid-layout の Layout 配列を LayoutItem 配列に変換
 */
export function fromRGLLayout(layout: Layout[]): LayoutItem[] {
  return layout.map((item) => ({
    card_id: item.i,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
  }));
}
