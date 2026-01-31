export interface User {
  user_id: string;
  email: string;
  name?: string;
  created_at: string;
}

export interface UserWithGroups extends User {
  groups: GroupRef[];
}

export interface GroupRef {
  group_id: string;
  name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export function isUser(value: unknown): value is User {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.user_id === 'string' &&
    typeof obj.email === 'string' &&
    typeof obj.created_at === 'string'
  );
}

export function isLoginResponse(value: unknown): value is LoginResponse {
  if (typeof value !== 'object' || value === null) return false;
  const obj = value as Record<string, unknown>;
  return (
    typeof obj.access_token === 'string' &&
    typeof obj.token_type === 'string' &&
    typeof obj.expires_in === 'number' &&
    isUser(obj.user)
  );
}
