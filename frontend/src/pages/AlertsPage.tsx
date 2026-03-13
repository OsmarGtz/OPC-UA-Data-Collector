import { useState } from 'react';
import { AlertsTable } from '../components/AlertsTable';
import { useAcknowledgeAlert, useAlertRules, useAlerts } from '../hooks/useAlerts';
import type { Severity } from '../types';

type StatusFilter = 'all' | 'open' | 'resolved';

const SEVERITIES: Severity[] = ['critical', 'warning', 'info'];

const C = {
  card:    '#161b22',
  border:  '#21262d',
  textSec: '#7d8590',
};

export function AlertsPage() {
  const [statusFilter,   setStatusFilter]   = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all');

  const { data: alerts = [], isLoading } = useAlerts(
    statusFilter === 'all' ? undefined : statusFilter,
    severityFilter === 'all' ? undefined : severityFilter,
  );
  const { data: rules = [] }               = useAlertRules();
  const { mutate: acknowledge, isPending } = useAcknowledgeAlert();

  const sorted = [...alerts].sort((a, b) => {
    const order = (x: typeof a) => x.resolved_at ? 2 : x.acknowledged_at ? 1 : 0;
    const diff = order(a) - order(b);
    return diff !== 0 ? diff : new Date(b.fired_at).getTime() - new Date(a.fired_at).getTime();
  });

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3', margin: 0 }}>Alerts</h1>
        <p style={{ fontSize: 13, color: C.textSec, marginTop: 4 }}>
          {sorted.length} alert{sorted.length !== 1 ? 's' : ''} · auto-refreshes every 10 s
        </p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 20, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <FilterGroup label="Status">
          {(['all', 'open', 'resolved'] as StatusFilter[]).map((s) => (
            <Chip key={s} active={statusFilter === s} onClick={() => setStatusFilter(s)}>{s}</Chip>
          ))}
        </FilterGroup>
        <FilterGroup label="Severity">
          <Chip active={severityFilter === 'all'} onClick={() => setSeverityFilter('all')}>all</Chip>
          {SEVERITIES.map((s) => (
            <Chip key={s} active={severityFilter === s} onClick={() => setSeverityFilter(s)}>{s}</Chip>
          ))}
        </FilterGroup>
      </div>

      {/* Table */}
      <div style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        overflow: 'hidden',
      }}>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: C.textSec, fontSize: 13 }}>
            Loading alerts…
          </div>
        ) : (
          <AlertsTable
            alerts={sorted}
            rules={rules}
            onAcknowledge={(id) => acknowledge(id)}
            isAcknowledging={isPending}
          />
        )}
      </div>
    </div>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontSize: 11, color: '#7d8590', textTransform: 'uppercase', letterSpacing: '0.07em', minWidth: 52 }}>
        {label}
      </span>
      <div style={{ display: 'flex', gap: 4 }}>{children}</div>
    </div>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '4px 12px', fontSize: 11, fontWeight: 500,
        borderRadius: 6,
        border: active ? '1px solid rgba(0,212,170,0.4)' : '1px solid #21262d',
        background: active ? 'rgba(0,212,170,0.12)' : '#0d1117',
        color:  active ? '#00d4aa' : '#7d8590',
        cursor: 'pointer',
        textTransform: 'capitalize',
        transition: 'all 0.12s',
      }}
    >
      {children}
    </button>
  );
}
