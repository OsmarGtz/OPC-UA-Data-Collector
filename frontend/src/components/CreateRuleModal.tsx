import { type CSSProperties, type ReactNode, FormEvent, useState } from 'react';
import type { Tag } from '../types';
import { useCreateAlertRule } from '../hooks/useAlerts';
import type { CreateAlertRulePayload } from '../api/alerts';
import { IconClose } from './Icons';

interface Props {
  tag: Tag;
  onClose: () => void;
}

const OPERATORS = [
  { value: 'gt',  label: '> Greater than'    },
  { value: 'gte', label: '≥ Greater or equal' },
  { value: 'lt',  label: '< Less than'        },
  { value: 'lte', label: '≤ Less or equal'    },
] as const;

const SEVERITIES = ['info', 'warning', 'critical'] as const;

const C = {
  bg:      'rgba(0,0,0,0.65)',
  card:    '#161b22',
  inner:   '#0d1117',
  border:  '#21262d',
  accent:  '#00d4aa',
  textPri: '#e6edf3',
  textSec: '#7d8590',
};

export function CreateRuleModal({ tag, onClose }: Props) {
  const { mutateAsync, isPending, isError, error } = useCreateAlertRule();

  const [name,      setName]      = useState(`${tag.name} alert`);
  const [operator,  setOperator]  = useState<CreateAlertRulePayload['operator']>('gt');
  const [threshold, setThreshold] = useState('');
  const [severity,  setSeverity]  = useState<CreateAlertRulePayload['severity']>('warning');
  const [duration,  setDuration]  = useState('0');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await mutateAsync({
      name,
      tag_id: tag.id,
      operator,
      threshold: Number(threshold),
      duration_seconds: Number(duration),
      severity,
    });
    onClose();
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div style={{ width: 440, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 28, boxShadow: '0 24px 64px rgba(0,0,0,0.6)' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: C.textPri, margin: 0 }}>New Alert Rule</h2>
            <p style={{ fontSize: 12, color: C.textSec, marginTop: 3 }}>Define condition to trigger an alert</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: C.textSec, cursor: 'pointer', padding: 4, display: 'flex' }}>
            <IconClose size={16} />
          </button>
        </div>

        {/* Tag pill */}
        <div style={{ marginBottom: 20, padding: '8px 12px', background: C.inner, borderRadius: 8, border: `1px solid ${C.border}`, fontSize: 13, color: C.textSec, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 3, height: 14, background: C.accent, borderRadius: 2, display: 'inline-block' }} />
          Tag: <span style={{ color: C.accent }}>{tag.name}</span>
          {tag.unit && <span style={{ color: '#475569' }}>({tag.unit})</span>}
        </div>

        <form onSubmit={(e) => void handleSubmit(e)}>
          <Field label="Rule name">
            <input style={INPUT} value={name} onChange={(e) => setName(e.target.value)} required />
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 }}>
            <Field label="Condition">
              <select style={INPUT} value={operator} onChange={(e) => setOperator(e.target.value as CreateAlertRulePayload['operator'])}>
                {OPERATORS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </Field>
            <Field label={`Threshold${tag.unit ? ` (${tag.unit})` : ''}`}>
              <input style={INPUT} type="number" step="any" required value={threshold} onChange={(e) => setThreshold(e.target.value)} placeholder="e.g. 80" />
            </Field>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 }}>
            <Field label="Severity">
              <select style={INPUT} value={severity} onChange={(e) => setSeverity(e.target.value as CreateAlertRulePayload['severity'])}>
                {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Duration (seconds)">
              <input style={INPUT} type="number" min="0" step="1" value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="0 = immediate" />
            </Field>
          </div>

          {isError && (
            <div style={{ marginTop: 14, padding: '9px 12px', background: 'rgba(255,68,68,0.1)', border: '1px solid rgba(255,68,68,0.25)', borderRadius: 8, fontSize: 13, color: '#ff8888' }}>
              {error instanceof Error ? error.message : 'Failed to create rule'}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={SEC_BTN}>Cancel</button>
            <button type="submit" disabled={isPending} style={PRI_BTN}>
              {isPending ? 'Saving…' : 'Create Rule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#7d8590', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
        {label}
      </label>
      {children}
    </div>
  );
}

const INPUT: CSSProperties = {
  width: '100%', padding: '9px 11px', fontSize: 13,
  borderRadius: 7, border: '1px solid #21262d',
  background: '#0d1117', color: '#e6edf3', outline: 'none',
};

const PRI_BTN: CSSProperties = {
  padding: '9px 22px', fontSize: 13, fontWeight: 600,
  borderRadius: 8, border: 'none',
  background: '#00d4aa', color: '#0d1117', cursor: 'pointer',
};

const SEC_BTN: CSSProperties = {
  padding: '9px 16px', fontSize: 13,
  borderRadius: 8, border: '1px solid #21262d',
  background: '#0d1117', color: '#7d8590', cursor: 'pointer',
};
