import { describe, expect, it } from 'vitest';
import type { Layout } from 'react-grid-layout';
import { fromRGLLayout, toRGLLayout } from '@/lib/layout-utils';
import type { LayoutItem } from '@/types/dashboard';

describe('layout-utils', () => {
  describe('toRGLLayout', () => {
    it('正常な LayoutItem 配列を react-grid-layout Layout 配列に変換', () => {
      const layoutItems: LayoutItem[] = [
        { card_id: 'card-1', x: 0, y: 0, w: 4, h: 2 },
        { card_id: 'card-2', x: 4, y: 0, w: 4, h: 2 },
      ];

      const result = toRGLLayout(layoutItems);

      expect(result).toEqual([
        { i: 'card-1', x: 0, y: 0, w: 4, h: 2 },
        { i: 'card-2', x: 4, y: 0, w: 4, h: 2 },
      ]);
    });

    it('空配列を空配列に変換', () => {
      const result = toRGLLayout([]);
      expect(result).toEqual([]);
    });

    it('単一要素を正しく変換', () => {
      const layoutItems: LayoutItem[] = [
        { card_id: 'only-card', x: 2, y: 3, w: 6, h: 4 },
      ];

      const result = toRGLLayout(layoutItems);

      expect(result).toEqual([
        { i: 'only-card', x: 2, y: 3, w: 6, h: 4 },
      ]);
    });
  });

  describe('fromRGLLayout', () => {
    it('正常な react-grid-layout Layout 配列を LayoutItem 配列に変換', () => {
      const rglLayout: Layout[] = [
        { i: 'card-1', x: 0, y: 0, w: 4, h: 2 },
        { i: 'card-2', x: 4, y: 0, w: 4, h: 2 },
      ];

      const result = fromRGLLayout(rglLayout);

      expect(result).toEqual([
        { card_id: 'card-1', x: 0, y: 0, w: 4, h: 2 },
        { card_id: 'card-2', x: 4, y: 0, w: 4, h: 2 },
      ]);
    });

    it('空配列を空配列に変換', () => {
      const result = fromRGLLayout([]);
      expect(result).toEqual([]);
    });

    it('単一要素を正しく変換', () => {
      const rglLayout: Layout[] = [
        { i: 'only-card', x: 2, y: 3, w: 6, h: 4 },
      ];

      const result = fromRGLLayout(rglLayout);

      expect(result).toEqual([
        { card_id: 'only-card', x: 2, y: 3, w: 6, h: 4 },
      ]);
    });

    it('追加のプロパティを無視して変換', () => {
      const rglLayout: Layout[] = [
        { i: 'card-1', x: 0, y: 0, w: 4, h: 2, static: false, isDraggable: true },
      ];

      const result = fromRGLLayout(rglLayout);

      expect(result).toEqual([
        { card_id: 'card-1', x: 0, y: 0, w: 4, h: 2 },
      ]);
    });
  });

  describe('双方向変換', () => {
    it('toRGLLayout → fromRGLLayout で元に戻る', () => {
      const original: LayoutItem[] = [
        { card_id: 'card-1', x: 0, y: 0, w: 4, h: 2 },
        { card_id: 'card-2', x: 4, y: 0, w: 4, h: 2 },
      ];

      const converted = toRGLLayout(original);
      const reverted = fromRGLLayout(converted);

      expect(reverted).toEqual(original);
    });
  });
});
