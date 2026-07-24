import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import type { ReactNode } from 'react';
import { authGetStatus, authLogin, authLogout, authRegister, type AuthStatus, type AuthUser } from '../services/api';

interface AuthContextValue {
  status: AuthStatus | null;
  loading: boolean;
  userId: string;
  username: string;
  isLoggedIn: boolean;
  authEnabled: boolean;
  login: (username: string, password: string) => Promise<{ status: string; user: AuthUser }>;
  register: (username: string, password: string) => Promise<{ status: string; user: AuthUser }>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const s = await authGetStatus();
      setStatus(s);
    } catch (e) {
      setStatus({ auth_enabled: true, logged_in: false, user: null });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const login = useCallback(async (username: string, password: string) => {
    const result = await authLogin(username, password);
    await fetchStatus();
    return result;
  }, [fetchStatus]);

  const register = useCallback(async (username: string, password: string) => {
    const result = await authRegister(username, password);
    await fetchStatus();
    return result;
  }, [fetchStatus]);

  const logout = useCallback(async () => {
    await authLogout();
    await fetchStatus();
  }, [fetchStatus]);

  const value = useMemo<AuthContextValue>(() => ({
    status,
    loading,
    userId: status?.user?.user_id || '',
    username: status?.user?.username || '',
    isLoggedIn: status?.logged_in ?? false,
    authEnabled: status?.auth_enabled ?? true,
    login,
    register,
    logout,
    refresh: fetchStatus,
  }), [status, loading, login, register, logout, fetchStatus]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
