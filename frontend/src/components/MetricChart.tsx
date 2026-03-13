import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { AlertRule, Reading, Tag } from '../types';

interface Props {
  tag: Tag;
  readings: Reading[];
  rules: AlertRule[];
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ff4444',
  warning:  '#ffd700',
  info:     '#0084ff',
};

// One distinct color per chart line
const LINE_COLOR = '#00d4aa';

const C = {
  card:    '#161b22',
  border:  '#21262d',
  grid:    '#1c2128',
  textSec: '#7d8590',
  textPri: '#e6edf3',
};

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function MetricChart({ tag, readings, rules }: Props) {
  const data = readings.map((r) => ({ time: r.timestamp, value: r.value }));

  return (
    <div style={{
      background: C.card,
      border: `1px solid ${C.border}`,
      borderRadius: 10,
      overflow: 'hidden',
    }}>
      {/* Chart header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: `1px solid ${C.border}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 3, height: 16, background: LINE_COLOR, borderRadius: 2, display: 'inline-block' }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: C.textPri }}>{tag.name}</span>
          {tag.unit && <span style={{ fontSize: 11, color: C.textSec }}>({tag.unit})</span>}
        </div>
        <span style={{ fontSize: 11, color: C.textSec, fontVariantNumeric: 'tabular-nums' }}>
          {readings.length} pts
        </span>
      </div>

      {/* Chart body */}
      <div style={{ padding: '12px 4px 8px 0' }}>
        {data.length === 0 ? (
          <div style={{
            height: 160,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            color: C.textSec, gap: 6,
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <span style={{ fontSize: 12 }}>No data in this range</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={data} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
              <XAxis
                dataKey="time"
                tickFormatter={fmtTime}
                tick={{ fill: C.textSec, fontSize: 10 }}
                axisLine={{ stroke: C.border }}
                tickLine={{ stroke: C.border }}
                minTickGap={48}
              />
              <YAxis
                tick={{ fill: C.textSec, fontSize: 10 }}
                axisLine={{ stroke: C.border }}
                tickLine={{ stroke: C.border }}
              />
              <Tooltip
                contentStyle={{
                  background: '#0d1117',
                  border: `1px solid ${C.border}`,
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: C.textSec, fontSize: 11 }}
                labelFormatter={(v) => new Date(v as string).toLocaleString()}
                formatter={(v: unknown) => [`${(v as number).toFixed(4)}${tag.unit ? ` ${tag.unit}` : ''}`, tag.name]}
              />
              {rules.map((rule) => (
                <ReferenceLine
                  key={rule.id}
                  y={rule.threshold}
                  stroke={SEVERITY_COLORS[rule.severity] ?? C.textSec}
                  strokeDasharray="5 3"
                  strokeWidth={1.5}
                  label={{
                    value: `${rule.operator} ${rule.threshold}`,
                    fill: SEVERITY_COLORS[rule.severity] ?? C.textSec,
                    fontSize: 10,
                    position: 'insideTopRight',
                  }}
                />
              ))}
              <Line
                type="monotone"
                dataKey="value"
                stroke={LINE_COLOR}
                strokeWidth={1.5}
                dot={false}
                activeDot={{ r: 4, fill: LINE_COLOR, strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
