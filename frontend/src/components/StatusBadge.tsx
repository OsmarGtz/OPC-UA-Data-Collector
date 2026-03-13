import type { Severity } from '../types';

interface Props {
  severity: Severity | 'normal';
  dot?: boolean;   // show dot-only variant
}

const CONFIG = {
  normal:   { label: 'Normal',   color: '#00d4aa', bg: 'rgba(0,212,170,0.12)',   border: 'rgba(0,212,170,0.25)' },
  info:     { label: 'Info',     color: '#0084ff', bg: 'rgba(0,132,255,0.12)',   border: 'rgba(0,132,255,0.25)' },
  warning:  { label: 'Warning',  color: '#ffd700', bg: 'rgba(255,215,0,0.12)',   border: 'rgba(255,215,0,0.25)' },
  critical: { label: 'Critical', color: '#ff4444', bg: 'rgba(255,68,68,0.12)',   border: 'rgba(255,68,68,0.25)' },
};

export function StatusBadge({ severity, dot = false }: Props) {
  const cfg = CONFIG[severity] ?? CONFIG.normal;

  if (dot) {
    return (
      <span style={{
        display: 'inline-block',
        width: 8, height: 8,
        borderRadius: '50%',
        background: cfg.color,
        boxShadow: `0 0 6px ${cfg.color}`,
        flexShrink: 0,
      }} />
    );
  }

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      padding: '2px 9px',
      borderRadius: 99,
      fontSize: 11,
      fontWeight: 600,
      background: cfg.bg,
      color: cfg.color,
      border: `1px solid ${cfg.border}`,
      letterSpacing: '0.03em',
      flexShrink: 0,
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: cfg.color, display: 'inline-block' }} />
      {cfg.label}
    </span>
  );
}
