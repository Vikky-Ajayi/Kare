import { create } from 'zustand';
import type { User } from '../types';

const LS = {
  access: 'kare_access_token',
  refresh: 'kare_refresh_token',
  user: 'kare_user',
};

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

function readUser(): User | null {
  try {
    return JSON.parse(localStorage.getItem(LS.user) || 'null');
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: readUser(),
  accessToken: localStorage.getItem(LS.access),
  refreshToken: localStorage.getItem(LS.refresh),
  isAuthenticated: !!localStorage.getItem(LS.access),

  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem(LS.access, accessToken);
    localStorage.setItem(LS.refresh, refreshToken);
    localStorage.setItem(LS.user, JSON.stringify(user));
    set({ user, accessToken, refreshToken, isAuthenticated: true });
  },
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem(LS.access, accessToken);
    localStorage.setItem(LS.refresh, refreshToken);
    set({ accessToken, refreshToken });
  },
  setUser: (user) => {
    localStorage.setItem(LS.user, JSON.stringify(user));
    set({ user });
  },
  logout: () => {
    Object.values(LS).forEach((k) => localStorage.removeItem(k));
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  },
}));
