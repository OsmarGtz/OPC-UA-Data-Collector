import type { User } from '../types';
import { apiFetch } from './client';

export interface CreateUserPayload {
  username: string;
  email: string;
  password: string;
  role: 'operator' | 'engineer' | 'admin';
}

export interface UpdateUserPayload {
  role?: 'operator' | 'engineer' | 'admin';
  is_active?: boolean;
}

export const listUsers         = ()                                       => apiFetch<User[]>('/auth/users');
export const createUser        = (data: CreateUserPayload)                => apiFetch<User>('/auth/users', { method: 'POST', body: JSON.stringify(data) });
export const updateUser        = (id: number, data: UpdateUserPayload)    => apiFetch<User>(`/auth/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteUser        = (id: number)                             => apiFetch<void>(`/auth/users/${id}`, { method: 'DELETE' });
export const adminSetPassword  = (id: number, new_password: string)       => apiFetch<void>(`/auth/users/${id}/password`, { method: 'PATCH', body: JSON.stringify({ new_password }) });
export const changeSelfPassword = (current_password: string, new_password: string) => apiFetch<void>('/auth/change-password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) });
