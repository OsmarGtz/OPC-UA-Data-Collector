import { createContext, useCallback, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { login as apiLogin } from '../api/auth';
import { setAccessToken } from '../api/client';

interface AuthState {
  accessToken: string | null;
  username: string | null;
  role: 'operator' | 'engineer' | 'admin' | null;
}

interface AuthContextValue {
  auth: AuthState;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function parseJwtRole(token: string): 'operator' | 'engineer' | 'admin' | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
    return payload.role ?? null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({ accessToken: null, username: null, role: null });

  const login = useCallback(async (username: string, password: string) => {
    const tokens = await apiLogin(username, password);
    setAccessToken(tokens.access_token);
    setAuth({ accessToken: tokens.access_token, username, role: parseJwtRole(tokens.access_token) });
  }, []);

  const logout = useCallback(() => {
    setAccessToken(null);
    setAuth({ accessToken: null, username: null, role: null });
  }, []);

  return (
    <AuthContext.Provider value={{ auth, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
