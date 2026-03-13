import { Link } from 'react-router-dom';
import type { Alert, AlertRule, Equipment, LatestReading } from '../types';
import { IconActivity, IconChevronRight } from './Icons';
import { StatusBadge } from './StatusBadge';

interface Props {
  equipment: Equipment;
  latestReadings: LatestReading[];
  openAlerts: Alert[];
  alertRules: AlertRule[];
}

function worstSeverity(openAlerts: Alert[], alertRules: AlertRule[]): 'normal' | 'info' | 'warning' | 'critical' {
  if (openAlerts.length === 0) return 'normal';
  const ruleMap = new Map(alertRules.map((r) => [r.id, r]));
  const order = { critical: 3, warning: 2, info: 1 } as const;
  let worst: 'info' | 'warning' | 'critical' = 'info';
  for (const a of openAlerts) {
    const rule = ruleMap.get(a.rule_id);
    if (rule && (order[rule.severity] ?? 0) > (order[worst] ?? 0)) worst = rule.severity;
  }
  return worst;
}

const C = {
  card:    '#161b22',
  border:  '#21262d',
  hover:   '#1c2128',
  accent:  '#00d4aa',
  textPri: '#e6edf3',
  textSec: '#7d8590',
  metric:  '#0d1117',
};

export function EquipmentCard({ equipment, latestReadings, openAlerts, alertRules }: Props) {
  const status = worstSeverity(openAlerts, alertRules);

  return (
    <Link to={`/equipment/${equipment.id}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
      <div
        style={{
          background: C.card,
          border: `1px solid ${C.border}`,
          borderRadius: 12,
          overflow: 'hidden',
          transition: 'border-color 0.15s, background 0.15s',
          cursor: 'pointer',
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = C.accent;
          (e.currentTarget as HTMLDivElement).style.background = C.hover;
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = C.border;
          (e.currentTarget as HTMLDivElement).style.background = C.card;
        }}
      >
        {/* Card header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 16px',
          borderBottom: `1px solid ${C.border}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: 'rgba(0,212,170,0.1)',
              border: '1px solid rgba(0,212,170,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <IconActivity size={16} color={C.accent} />
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600, color: C.textPri }}>{equipment.name}</div>
              {equipment.location && (
                <div style={{ fontSize: 11, color: C.textSec, marginTop: 1 }}>{equipment.location}</div>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <StatusBadge severity={status} />
            <IconChevronRight size={14} color={C.textSec} />
          </div>
        </div>

        {/* Metrics grid */}
        <div style={{ padding: 14 }}>
          {latestReadings.length === 0 ? (
            <p style={{ fontSize: 12, color: C.textSec, textAlign: 'center', padding: '12px 0' }}>
              No readings yet
            </p>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: latestReadings.length >= 3 ? '1fr 1fr' : `repeat(${latestReadings.length}, 1fr)`,
              gap: 8,
            }}>
              {latestReadings.map((r) => (
                <div key={r.tag_id} style={{
                  background: C.metric,
                  borderRadius: 8,
                  padding: '10px 12px',
                  border: `1px solid ${C.border}`,
                }}>
                  <div style={{ fontSize: 10, color: C.textSec, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>
                    {r.tag_name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: C.textPri, fontVariantNumeric: 'tabular-nums' }}>
                      {r.value != null ? r.value.toFixed(2) : '—'}
                    </span>
                    {r.unit && <span style={{ fontSize: 10, color: C.textSec }}>{r.unit}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {openAlerts.length > 0 && (
            <div style={{
              marginTop: 10,
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 10px',
              background: 'rgba(255,68,68,0.08)',
              border: '1px solid rgba(255,68,68,0.2)',
              borderRadius: 7,
              fontSize: 11,
              color: '#ff8888',
            }}>
              <StatusBadge severity="critical" dot />
              {openAlerts.length} active alert{openAlerts.length > 1 ? 's' : ''}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
