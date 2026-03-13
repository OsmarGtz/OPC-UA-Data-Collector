import type { CSSProperties } from 'react';
import { Link } from 'react-router-dom';
import type { Alert, AlertRule } from '../types';
import { IconAlertTriangle, IconCheckCircle } from './Icons';
import { StatusBadge } from './StatusBadge';

interface Props {
  alerts: Alert[];
  rules: AlertRule[];
  onAcknowledge?: (alertId: number) => void;
  isAcknowledging?: boolean;
}

function alertStatus(alert: Alert): 'open' | 'acknowledged' | 'resolved' {
  if (alert.resolved_at)     return 'resolved';
  if (alert.acknowledged_at) return 'acknowledged';
  return 'open';
}

const STATUS_CFG = {
  open:         { color: '#ff4444', Icon: IconAlertTriangle },
  acknowledged: { color: '#ffd700', Icon: IconAlertTriangle },
  resolved:     { color: '#00d4aa', Icon: IconCheckCircle  },
};

const C = {
  border:  '#21262d',
  rowHov:  '#1c2128',
  textPri: '#e6edf3',
  textSec: '#7d8590',
  accent:  '#00d4aa',
};

export function AlertsTable({ alerts, rules, onAcknowledge, isAcknowledging }: Props) {
  const ruleMap = new Map(rules.map((r) => [r.id, r]));

  if (alerts.length === 0) {
    return (
      <div style={{ color: C.textSec, textAlign: 'center', padding: '48px 0', fontSize: 14 }}>
        <IconCheckCircle size={28} color={C.accent} />
        <p style={{ marginTop: 10 }}>No alerts to display.</p>
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${C.border}` }}>
            {['Status', 'Severity', 'Equipment', 'Rule', 'Value', 'Fired At', 'Resolved / Ack\'d', ''].map((h) => (
              <th key={h} style={TH}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => {
            const rule   = ruleMap.get(alert.rule_id);
            const status = alertStatus(alert);
            const { color, Icon } = STATUS_CFG[status];

            return (
              <tr
                key={alert.id}
                style={{ borderBottom: `1px solid ${C.border}` }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = C.rowHov)}
                onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = 'transparent')}
              >
                {/* Status */}
                <td style={TD}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, color }}>
                    <Icon size={13} color={color} />
                    <span style={{ textTransform: 'capitalize', fontSize: 12, fontWeight: 500 }}>{status}</span>
                  </div>
                </td>

                {/* Severity */}
                <td style={TD}>
                  {rule ? <StatusBadge severity={rule.severity} /> : <span style={{ color: C.textSec }}>—</span>}
                </td>

                {/* Equipment — name + location */}
                <td style={TD}>
                  {alert.equipment_name ? (
                    <div>
                      <Link
                        to={`/equipment/${alert.equipment_id}`}
                        style={{ color: C.textPri, textDecoration: 'none', fontWeight: 500 }}
                        onMouseEnter={(e) => (e.currentTarget.style.color = C.accent)}
                        onMouseLeave={(e) => (e.currentTarget.style.color = C.textPri)}
                      >
                        {alert.equipment_name}
                      </Link>
                      {alert.equipment_location && (
                        <div style={{ fontSize: 11, color: C.textSec, marginTop: 2 }}>
                          {alert.equipment_location}
                        </div>
                      )}
                    </div>
                  ) : (
                    <span style={{ color: C.textSec }}>—</span>
                  )}
                </td>

                {/* Rule name */}
                <td style={{ ...TD, color: C.textPri }}>{rule?.name ?? `Rule #${alert.rule_id}`}</td>

                {/* Triggering value */}
                <td style={{ ...TD, fontVariantNumeric: 'tabular-nums' }}>
                  {alert.triggering_value.toFixed(3)}
                  {alert.tag_unit && (
                    <span style={{ color: C.textSec, fontSize: 11, marginLeft: 3 }}>{alert.tag_unit}</span>
                  )}
                </td>

                {/* Fired at */}
                <td style={{ ...TD, color: C.textSec, fontSize: 12 }}>
                  {new Date(alert.fired_at).toLocaleString()}
                </td>

                {/* Resolved / Ack'd */}
                <td style={{ ...TD, color: C.textSec, fontSize: 12 }}>
                  {alert.resolved_at
                    ? new Date(alert.resolved_at).toLocaleString()
                    : alert.acknowledged_at
                      ? new Date(alert.acknowledged_at).toLocaleString()
                      : '—'}
                </td>

                {/* Action */}
                <td style={TD}>
                  {status === 'open' && onAcknowledge && (
                    <button
                      onClick={() => onAcknowledge(alert.id)}
                      disabled={isAcknowledging}
                      style={{
                        padding: '4px 12px', fontSize: 11, fontWeight: 600,
                        borderRadius: 6,
                        border: '1px solid rgba(255,215,0,0.3)',
                        background: 'rgba(255,215,0,0.08)',
                        color: '#ffd700',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      Acknowledge
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const TH: CSSProperties = {
  textAlign: 'left',
  padding: '10px 16px',
  fontSize: 11,
  fontWeight: 600,
  color: '#7d8590',
  textTransform: 'uppercase',
  letterSpacing: '0.07em',
  whiteSpace: 'nowrap',
};

const TD: CSSProperties = {
  padding: '12px 16px',
  color: '#7d8590',
  verticalAlign: 'middle',
};
