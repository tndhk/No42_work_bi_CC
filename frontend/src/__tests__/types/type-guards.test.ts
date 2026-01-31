import { describe, it, expect } from 'vitest';
import {
  isUser,
  isLoginResponse,
  isDataset,
  isColumnSchema,
  isCard,
  isDashboard,
  isLayoutItem,
  isApiErrorResponse,
  isPagination,
} from '@/types';

describe('Type Guards', () => {
  describe('isUser', () => {
    it('returns true for valid user', () => {
      expect(isUser({ user_id: 'u1', email: 'a@b.com', created_at: '2024-01-01T00:00:00Z' })).toBe(true);
    });
    it('returns false for null', () => {
      expect(isUser(null)).toBe(false);
    });
    it('returns false for missing fields', () => {
      expect(isUser({ user_id: 'u1' })).toBe(false);
    });
  });

  describe('isLoginResponse', () => {
    it('returns true for valid login response', () => {
      const data = {
        access_token: 'tok',
        token_type: 'bearer',
        expires_in: 86400,
        user: { user_id: 'u1', email: 'a@b.com', created_at: '2024-01-01T00:00:00Z' },
      };
      expect(isLoginResponse(data)).toBe(true);
    });
    it('returns false for missing user', () => {
      expect(isLoginResponse({ access_token: 'tok', token_type: 'bearer', expires_in: 86400 })).toBe(false);
    });
  });

  describe('isDataset', () => {
    it('returns true for valid dataset', () => {
      expect(isDataset({
        dataset_id: 'ds1', name: 'test', source_type: 'local_csv', row_count: 100,
      })).toBe(true);
    });
    it('returns false for wrong types', () => {
      expect(isDataset({ dataset_id: 123 })).toBe(false);
    });
  });

  describe('isColumnSchema', () => {
    it('returns true for valid column schema', () => {
      expect(isColumnSchema({ name: 'col1', type: 'string', nullable: false })).toBe(true);
    });
    it('returns false for missing nullable', () => {
      expect(isColumnSchema({ name: 'col1', type: 'string' })).toBe(false);
    });
  });

  describe('isCard', () => {
    it('returns true for valid card', () => {
      expect(isCard({ card_id: 'c1', name: 'card', created_at: '2024-01-01' })).toBe(true);
    });
    it('returns false for non-object', () => {
      expect(isCard('string')).toBe(false);
    });
  });

  describe('isDashboard', () => {
    it('returns true for valid dashboard', () => {
      expect(isDashboard({
        dashboard_id: 'd1', name: 'dash', created_at: '2024-01-01', updated_at: '2024-01-01',
      })).toBe(true);
    });
  });

  describe('isLayoutItem', () => {
    it('returns true for valid layout item', () => {
      expect(isLayoutItem({ card_id: 'c1', x: 0, y: 0, w: 6, h: 4 })).toBe(true);
    });
    it('returns false for missing dimensions', () => {
      expect(isLayoutItem({ card_id: 'c1', x: 0 })).toBe(false);
    });
  });

  describe('isApiErrorResponse', () => {
    it('returns true for valid error response', () => {
      expect(isApiErrorResponse({ error: { code: 'NOT_FOUND', message: 'Not found' } })).toBe(true);
    });
    it('returns false for non-error object', () => {
      expect(isApiErrorResponse({ data: {} })).toBe(false);
    });
  });

  describe('isPagination', () => {
    it('returns true for valid pagination', () => {
      expect(isPagination({ total: 100, limit: 20, offset: 0, has_next: true })).toBe(true);
    });
    it('returns false for missing has_next', () => {
      expect(isPagination({ total: 100, limit: 20, offset: 0 })).toBe(false);
    });
  });
});
