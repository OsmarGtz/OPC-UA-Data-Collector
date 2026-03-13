import { apiFetch } from './client';
import type { Alert, AlertRule } from '../types';

export function listAlerts(status?: string, severity?: string): Promise<Alert[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (severity) params.set('severity', severity);
  const qs = params.toString();
  return apiFetch<Alert[]>(`/api/v1/alerts${qs ? `?${qs}` : ''}`);
}

export function listAlertRules(): Promise<AlertRule[]> {
  return apiFetch<AlertRule[]>('/api/v1/alert-rules');
}

export function acknowledgeAlert(alertId: number): Promise<Alert> {
  return apiFetch<Alert>(`/api/v1/alerts/${alertId}/acknowledge`, { method: 'POST' });
}

export interface CreateAlertRulePayload {
  name: string;
  tag_id: number;
  operator: 'gt' | 'lt' | 'gte' | 'lte';
  threshold: number;
  duration_seconds: number;
  severity: 'info' | 'warning' | 'critical';
}

export function createAlertRule(payload: CreateAlertRulePayload): Promise<AlertRule> {
  return apiFetch<AlertRule>('/api/v1/alert-rules', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function deleteAlertRule(ruleId: number): Promise<void> {
  return apiFetch<void>(`/api/v1/alert-rules/${ruleId}`, { method: 'DELETE' });
}
