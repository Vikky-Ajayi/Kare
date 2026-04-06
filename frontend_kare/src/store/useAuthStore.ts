import { create } from 'zustand';
import { User, PatientProfile } from '../types';

interface AuthState {
  user: User | null;
  profile: PatientProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, accessToken: string, refreshToken: string) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setProfile: (profile: PatientProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: JSON.parse(localStorage.getItem('kare_user') || 'null'),
  profile: null,
  accessToken: localStorage.getItem('kare_access_token'),
  refreshToken: localStorage.getItem('kare_refresh_token'),
  isAuthenticated: !!localStorage.getItem('kare_access_token'),
  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem('kare_access_token', accessToken);
    localStorage.setItem('kare_refresh_token', refreshToken);
    localStorage.setItem('kare_user', JSON.stringify(user));
    set({ user, accessToken, refreshToken, isAuthenticated: true });
  },
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem('kare_access_token', accessToken);
    localStorage.setItem('kare_refresh_token', refreshToken);
    set({ accessToken, refreshToken });
  },
  setProfile: (profile) => set({ profile }),
  logout: () => {
    localStorage.removeItem('kare_access_token');
    localStorage.removeItem('kare_refresh_token');
    localStorage.removeItem('kare_user');
    set({ user: null, profile: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  },
}));
