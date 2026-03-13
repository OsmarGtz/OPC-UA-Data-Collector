import { apiFetch } from './client';
import type { TokenPair } from '../types';

export async function login(username: string, password: string): Promise<TokenPair> {
  return apiFetch<TokenPair>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function refreshTokens(refreshToken: string): Promise<TokenPair> {
  return apiFetch<TokenPair>('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}
