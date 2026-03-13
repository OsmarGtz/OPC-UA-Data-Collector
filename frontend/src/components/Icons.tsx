/** Inline SVG icon set — 24×24, 1.5px stroke, no fill. */

interface IconProps {
  size?: number;
  color?: string;
  strokeWidth?: number;
}

const base = (size: number, color: string, sw: number) => ({
  width: size,
  height: size,
  display: 'block' as const,
  color,
  stroke: 'currentColor',
  fill: 'none',
  strokeWidth: sw,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
});

export function IconGrid({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

/** Circuit board / microchip icon — used as the app logo mark. */
export function IconCircuitBoard({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      {/* Chip body */}
      <rect x="7" y="7" width="10" height="10" rx="1.5" />
      {/* Inner core */}
      <rect x="10" y="10" width="4" height="4" rx="0.5" />
      {/* Top pins */}
      <line x1="10" y1="7" x2="10" y2="3" />
      <line x1="14" y1="7" x2="14" y2="3" />
      {/* Bottom pins */}
      <line x1="10" y1="17" x2="10" y2="21" />
      <line x1="14" y1="17" x2="14" y2="21" />
      {/* Left pins */}
      <line x1="7" y1="10" x2="3" y2="10" />
      <line x1="7" y1="14" x2="3" y2="14" />
      {/* Right pins */}
      <line x1="17" y1="10" x2="21" y2="10" />
      <line x1="17" y1="14" x2="21" y2="14" />
    </svg>
  );
}

export function IconBell({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  );
}

export function IconLogout({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

export function IconUser({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

export function IconActivity({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

export function IconRefresh({ size = 16, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  );
}

export function IconChevronRight({ size = 16, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

export function IconPlus({ size = 16, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  );
}

export function IconAlertTriangle({ size = 14, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

export function IconCheckCircle({ size = 14, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

export function IconUsers({ size = 20, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}

export function IconClose({ size = 14, color = 'currentColor', strokeWidth = 1.5 }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" style={base(size, color, strokeWidth)}>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
