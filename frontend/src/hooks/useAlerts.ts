import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { acknowledgeAlert, createAlertRule, deleteAlertRule, listAlertRules, listAlerts } from '../api/alerts';
import type { CreateAlertRulePayload } from '../api/alerts';

export function useAlerts(status?: string, severity?: string) {
  return useQuery({
    queryKey: ['alerts', status, severity],
    queryFn: () => listAlerts(status, severity),
    refetchInterval: 10_000,
  });
}

export function useAlertRules() {
  return useQuery({
    queryKey: ['alert-rules'],
    queryFn: listAlertRules,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function useCreateAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateAlertRulePayload) => createAlertRule(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });
}

export function useDeleteAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: number) => deleteAlertRule(ruleId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });
}
