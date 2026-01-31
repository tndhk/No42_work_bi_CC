export interface ApiResponse<T> {
  data: T;
  meta?: {
    request_id: string;
  };
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    request_id: string;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}

export interface Pagination {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  if (typeof obj.error !== 'object' || obj.error === null) return false;
  const error = obj.error as Record<string, unknown>;
  return typeof error.code === 'string' && typeof error.message === 'string';
}

export function isPagination(value: unknown): value is Pagination {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.total === 'number' &&
    typeof obj.limit === 'number' &&
    typeof obj.offset === 'number' &&
    typeof obj.has_next === 'boolean'
  );
}
