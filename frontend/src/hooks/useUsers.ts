import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminSetPassword, changeSelfPassword, createUser, deleteUser, listUsers, updateUser } from '../api/users';
import type { CreateUserPayload, UpdateUserPayload } from '../api/users';

const KEY = ['users'];

export function useUsers() {
  return useQuery({ queryKey: KEY, queryFn: listUsers, refetchInterval: 30_000 });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateUserPayload) => createUser(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserPayload }) => updateUser(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteUser(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}

export function useAdminSetPassword() {
  return useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) => adminSetPassword(id, password),
  });
}

export function useChangeSelfPassword() {
  return useMutation({
    mutationFn: ({ current, next }: { current: string; next: string }) => changeSelfPassword(current, next),
  });
}
