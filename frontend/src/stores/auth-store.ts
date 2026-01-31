import { create } from 'zustand';
import type { User } from '@/types';

export interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  setAuth: (token: string, user: User) =>
    set({ token, user, isAuthenticated: true }),
  clearAuth: () =>
    set({ token: null, user: null, isAuthenticated: false }),
}));
