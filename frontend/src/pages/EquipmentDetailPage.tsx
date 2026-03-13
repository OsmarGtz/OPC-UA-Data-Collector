import { type CSSProperties, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { CreateRuleModal } from '../components/CreateRuleModal';
import { MetricChart } from '../components/MetricChart';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useAlertRules, useDeleteAlertRule } from '../hooks/useAlerts';
import {
  useEquipment,
  useEquipmentReadings,
  useLatestReadings,
  useTagsByEquipment,
} from '../hooks/useEquipment';
import type { Reading, Tag } from '../types';

type Range = '1h' | '6h' | '24h';

const RANGE_LABELS: Record<Range, string> = {
  '1h':  'Last hour',
  '6h':  'Last 6 h',
  '24h': 'Last 24 h',
};

const RANGE_HOURS: Record<Range, number> = { '1h': 1, '6h': 6, '24h': 24 };

function rangeToWindow(range: Range): { start: string; end: string } {
  const end   = new Date();
  const start = new Date(end.getTime() - RANGE_HOURS[range] * 3_600_000);
  return { start: start.toISOString(), end: end.toISOString() };
}

// ─────────────────────────────────────────────────────────────────────────────

export function EquipmentDetailPage() {
  const { id }        = useParams<{ id: string }>();
  const equipmentId   = Number(id);
  const [range, setRange]         = useState<Range>('24h');
  const [ruleModalTag, setRuleModalTag] = useState<Tag | null>(null);
  const [confirmDeleteRule, setConfirmDeleteRule] = useState<number | null>(null);

  const { auth } = useAuth();
  const canWrite = auth.role === 'engineer' || auth.role === 'admin';

  const { mutate: deleteRule, isPending: isDeletingRule } = useDeleteAlertRule();

  const { start, end } = useMemo(() => rangeToWindow(range), [range]);

  const { data: equipment, isLoading: eqLoading }             = useEquipment(equipmentId);
  const { data: tags      = [] }                               = useTagsByEquipment(equipmentId);
  const { data: latest    = [] }                               = useLatestReadings(equipmentId);
  const { data: allReadings = [], isLoading: rdLoading }       = useEquipmentReadings(equipmentId, start, end);
  const { data: allRules  = [] }                               = useAlertRules();

  // Only Good-quality readings make it into the charts (Bad/null skew the scale)
  const goodReadings = useMemo(
    () => allReadings.filter((r) => r.quality === 'Good' && r.value != null),
    [allReadings],
  );

  // Group Good readings by tag_id for per-chart rendering
  const readingsByTag = useMemo(() => {
    const map = new Map<number, Reading[]>();
    for (const r of goodReadings) {
      const arr = map.get(r.tag_id) ?? [];
      arr.push(r);
      map.set(r.tag_id, arr);
    }
    return map;
  }, [goodReadings]);

  // ── Loading / not-found guards ──────────────────────────────────────────
  if (eqLoading) {
    return <p style={{ color: '#64748b', padding: 40 }}>Loading…</p>;
  }
  if (!equipment) {
    return <p style={{ color: '#f87171', padding: 40 }}>Equipment not found.</p>;
  }

  const activeRules = allRules.filter((r) => r.is_active);

  return (
    <div>
      {/* ── Breadcrumb ─────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 20, fontSize: 13, color: '#64748b' }}>
        <Link to="/" style={{ color: '#38bdf8', textDecoration: 'none' }}>
          Equipment
        </Link>{' '}
        / {equipment.name}
      </div>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9' }}>{equipment.name}</h1>
        {equipment.location && (
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>{equipment.location}</p>
        )}
        {equipment.description && (
          <p style={{ fontSize: 13, color: '#475569', marginTop: 2 }}>{equipment.description}</p>
        )}
      </div>

      {/* ── Current snapshot ───────────────────────────────────────────── */}
      <Section title="Current Values">
        {latest.length === 0 ? (
          <Muted>No readings recorded yet.</Muted>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
            {latest.map((r) => {
              const tagRules = activeRules.filter((ru) => ru.tag_id === r.tag_id);
              const breached = tagRules.find((ru) => {
                const v = r.value ?? 0;
                if (ru.operator === 'gt')  return v >  ru.threshold;
                if (ru.operator === 'gte') return v >= ru.threshold;
                if (ru.operator === 'lt')  return v <  ru.threshold;
                if (ru.operator === 'lte') return v <= ru.threshold;
                return false;
              });
              const sev = breached?.severity ?? 'normal';

              return (
                <div key={r.tag_id} style={{ background: '#0f172a', borderRadius: 10, padding: '12px 14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {r.tag_name}
                    </span>
                    <StatusBadge severity={sev as 'normal' | 'info' | 'warning' | 'critical'} />
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#e2e8f0' }}>
                    {r.value != null ? r.value.toFixed(2) : '—'}
                  </div>
                  {r.unit && (
                    <div style={{ fontSize: 11, color: '#475569', marginTop: 2 }}>{r.unit}</div>
                  )}
                  <div style={{ fontSize: 10, color: '#334155', marginTop: 6 }}>
                    {new Date(r.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Section>

      {/* ── Charts ─────────────────────────────────────────────────────── */}
      <Section
        title="Trends"
        right={
          <div style={{ display: 'flex', gap: 8 }}>
            {(Object.keys(RANGE_LABELS) as Range[]).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                style={{
                  padding: '5px 12px', fontSize: 12,
                  borderRadius: 7, border: '1px solid #334155',
                  background: range === r ? '#0ea5e9' : '#1e293b',
                  color:      range === r ? '#fff'    : '#94a3b8',
                  cursor: 'pointer',
                }}
              >
                {RANGE_LABELS[r]}
              </button>
            ))}
          </div>
        }
      >
        {tags.length === 0 ? (
          <Muted>No tags configured for this equipment.</Muted>
        ) : rdLoading ? (
          <Muted>Loading readings…</Muted>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))', gap: 20 }}>
            {tags.map((tag) => {
              const tagReadings = readingsByTag.get(tag.id) ?? [];
              const tagRules    = activeRules.filter((r) => r.tag_id === tag.id);
              return (
                <div key={tag.id}>
                  <MetricChart tag={tag} readings={tagReadings} rules={tagRules} />
                  {canWrite && (
                    <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        onClick={() => setRuleModalTag(tag)}
                        style={{
                          fontSize: 12, padding: '4px 12px',
                          borderRadius: 6, border: '1px solid #334155',
                          background: '#1e293b', color: '#94a3b8', cursor: 'pointer',
                        }}
                      >
                        + Add Alert Rule
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </Section>

      {/* ── Active Alert Rules ─────────────────────────────────────────── */}
      <Section
        title="Alert Rules"
        right={
          canWrite && tags.length > 0 && (
            <button
              onClick={() => setRuleModalTag(tags[0])}
              style={{
                fontSize: 12, padding: '5px 14px',
                borderRadius: 7, border: '1px solid #334155',
                background: '#1e293b', color: '#94a3b8', cursor: 'pointer',
              }}
            >
              + New Rule
            </button>
          )
        }
      >
        {activeRules.filter((r) => tags.some((t) => t.id === r.tag_id)).length === 0 ? (
          <Muted>No alert rules for this equipment yet.</Muted>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {activeRules
              .filter((r) => tags.some((t) => t.id === r.tag_id))
              .map((rule) => {
                const tag = tags.find((t) => t.id === rule.tag_id);
                const SCOLOR: Record<string, string> = { critical: '#f87171', warning: '#fbbf24', info: '#60a5fa' };
                return (
                  <div
                    key={rule.id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 12,
                      background: '#0f172a', borderRadius: 8, padding: '10px 14px',
                      borderLeft: `3px solid ${SCOLOR[rule.severity] ?? '#334155'}`,
                    }}
                  >
                    <StatusBadge severity={rule.severity} />
                    <span style={{ fontSize: 14, color: '#e2e8f0', flex: 1 }}>{rule.name}</span>
                    <span style={{ fontSize: 12, color: '#64748b' }}>
                      {tag?.name} {rule.operator} {rule.threshold}{tag?.unit ? ` ${tag.unit}` : ''}
                    </span>
                    {rule.duration_seconds > 0 && (
                      <span style={{ fontSize: 11, color: '#475569' }}>
                        for {rule.duration_seconds}s
                      </span>
                    )}
                    {canWrite && (
                      confirmDeleteRule === rule.id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 8 }}>
                          <span style={{ fontSize: 11, color: '#f87171' }}>Remove?</span>
                          <button
                            disabled={isDeletingRule}
                            onClick={() => { deleteRule(rule.id); setConfirmDeleteRule(null); }}
                            style={DANGER_BTN}
                          >
                            Yes
                          </button>
                          <button onClick={() => setConfirmDeleteRule(null)} style={GHOST_BTN}>
                            No
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmDeleteRule(rule.id)}
                          style={{ ...GHOST_BTN, marginLeft: 8 }}
                        >
                          Remove
                        </button>
                      )
                    )}
                  </div>
                );
              })}
          </div>
        )}
      </Section>

      {/* ── Create Rule Modal ──────────────────────────────────────────── */}
      {ruleModalTag && (
        <CreateRuleModal
          tag={ruleModalTag}
          onClose={() => setRuleModalTag(null)}
        />
      )}
    </div>
  );
}

// ─── Small helpers ─────────────────────────────────────────────────────────

function Section({
  title,
  right,
  children,
}: {
  title: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: 32 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {title}
        </h2>
        {right}
      </div>
      {children}
    </div>
  );
}

function Muted({ children }: { children: React.ReactNode }) {
  return <p style={{ color: '#475569', fontSize: 14 }}>{children}</p>;
}

const DANGER_BTN: CSSProperties = {
  padding: '3px 10px', fontSize: 11, fontWeight: 600,
  borderRadius: 5, border: '1px solid rgba(248,113,113,0.35)',
  background: 'rgba(248,113,113,0.08)', color: '#f87171', cursor: 'pointer',
};

const GHOST_BTN: CSSProperties = {
  padding: '3px 10px', fontSize: 11,
  borderRadius: 5, border: '1px solid #334155',
  background: 'transparent', color: '#64748b', cursor: 'pointer',
};
