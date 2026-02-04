import { describe, it, expect } from 'vitest';
import { isTransform } from '@/types';

describe('isTransform', () => {
  it('returns true for valid Transform object', () => {
    const transform = {
      id: 't1',
      name: 'my-transform',
      owner_id: 'u1',
      input_dataset_ids: ['ds1'],
      code: 'df.head()',
      owner: { user_id: 'u1', name: 'Alice' },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(isTransform(transform)).toBe(true);
  });

  it('returns false for null', () => {
    expect(isTransform(null)).toBe(false);
  });

  it('returns false for undefined', () => {
    expect(isTransform(undefined)).toBe(false);
  });

  it('returns false when id is missing', () => {
    const obj = {
      name: 'my-transform',
      owner_id: 'u1',
      input_dataset_ids: ['ds1'],
      code: 'df.head()',
      owner: { user_id: 'u1', name: 'Alice' },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(isTransform(obj)).toBe(false);
  });

  it('returns false when name is missing', () => {
    const obj = {
      id: 't1',
      owner_id: 'u1',
      input_dataset_ids: ['ds1'],
      code: 'df.head()',
      owner: { user_id: 'u1', name: 'Alice' },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(isTransform(obj)).toBe(false);
  });

  it('returns false when created_at is missing', () => {
    const obj = {
      id: 't1',
      name: 'my-transform',
      owner_id: 'u1',
      input_dataset_ids: ['ds1'],
      code: 'df.head()',
      owner: { user_id: 'u1', name: 'Alice' },
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(isTransform(obj)).toBe(false);
  });
});
