import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { IconBell, IconCircuitBoard, IconGrid, IconLogout, IconUser, IconUsers } from './Icons';
import { ChangePasswordModal } from './ChangePasswordModal';

const C = {
  sidebar:  '#090c10',
  bg:       '#0d1117',
  accent:   '#00d4aa',
  border:   '#21262d',
  textSec:  '#7d8590',
};

const NAV_ALL = [
  { to: '/',       label: 'Equipment', Icon: IconGrid  },
  { to: '/alerts', label: 'Alerts',    Icon: IconBell  },
];
const NAV_ADMIN = [
  { to: '/users',  label: 'Users',     Icon: IconUsers },
];

export function Layout() {
  const { auth, logout } = useAuth();
  const navigate = useNavigate();
  const [showChangePw, setShowChangePw] = useState(false);
  const navItems = auth.role === 'admin' ? [...NAV_ALL, ...NAV_ADMIN] : NAV_ALL;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: C.bg, fontFamily: 'system-ui, -apple-system, sans-serif' }}>

      {/* ── Sidebar ───────────────────────────────────────────────────── */}
      <aside style={{
        width: 72,
        background: C.sidebar,
        borderRight: `1px solid ${C.border}`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 20,
        paddingBottom: 20,
        flexShrink: 0,
        position: 'fixed',
        top: 0, left: 0, bottom: 0,
        zIndex: 50,
      }}>

        {/* Logo mark — links to dashboard */}
        <div
          onClick={() => navigate('/')}
          title="OPC-UA Dashboard"
          style={{
            width: 36, height: 36, borderRadius: 8,
            background: C.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 32,
            flexShrink: 0,
            cursor: 'pointer',
          }}
        >
          <IconCircuitBoard size={20} color="#0d1117" strokeWidth={2} />
        </div>

        {/* Nav items */}
        <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, width: '100%' }}>
          {navItems.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              title={label}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 44,
                height: 44,
                borderRadius: 10,
                textDecoration: 'none',
                color:      isActive ? C.accent   : C.textSec,
                background: isActive ? 'rgba(0,212,170,0.12)' : 'transparent',
                border:     isActive ? `1px solid rgba(0,212,170,0.25)` : '1px solid transparent',
                transition: 'all 0.15s',
              })}
            >
              <Icon size={20} />
            </NavLink>
          ))}
        </nav>

        {/* Bottom: user avatar + logout */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => setShowChangePw(true)}
            title={`${auth.username ?? 'User'} · ${auth.role ?? ''} — click to change password`}
            style={{
              width: 34, height: 34, borderRadius: '50%',
              background: '#1c2128', border: `1px solid ${C.border}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: C.textSec, cursor: 'pointer',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = C.accent)}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = C.border)}
          >
            <IconUser size={16} />
          </button>

          <button
            onClick={logout}
            title="Log out"
            style={{
              width: 34, height: 34,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'none', border: 'none',
              color: C.textSec, cursor: 'pointer', borderRadius: 8,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#e6edf3')}
            onMouseLeave={(e) => (e.currentTarget.style.color = C.textSec)}
          >
            <IconLogout size={17} />
          </button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────── */}
      <main style={{ flex: 1, marginLeft: 72, minHeight: '100vh', overflowY: 'auto' }}>
        {/* Top bar */}
        <header style={{
          height: 52,
          background: C.sidebar,
          borderBottom: `1px solid ${C.border}`,
          display: 'flex',
          alignItems: 'center',
          padding: '0 28px',
          gap: 8,
        }}>
          <NavLink
            to="/"
            style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none' }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
          >
            <span style={{ fontSize: 11, fontWeight: 600, color: C.accent, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              OPC-UA
            </span>
            <span style={{ color: C.border, fontSize: 14 }}>|</span>
            <span style={{ fontSize: 12, color: C.textSec }}>Data Collector</span>
          </NavLink>

          <div style={{ flex: 1 }} />

          {/* Live indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: C.accent, display: 'inline-block', boxShadow: `0 0 6px ${C.accent}` }} />
            <span style={{ fontSize: 11, color: C.textSec }}>Live · 10s refresh</span>
          </div>

          <div style={{ marginLeft: 20, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 12, color: C.textSec }}>{auth.username}</span>
            {auth.role && (
              <span style={{
                fontSize: 10, fontWeight: 600, padding: '2px 7px',
                borderRadius: 4, textTransform: 'uppercase', letterSpacing: '0.06em',
                background: auth.role === 'admin'     ? 'rgba(255,165,0,0.12)'
                          : auth.role === 'engineer'  ? 'rgba(0,212,170,0.12)'
                          : 'rgba(125,133,144,0.12)',
                color:      auth.role === 'admin'     ? '#ffa500'
                          : auth.role === 'engineer'  ? C.accent
                          : C.textSec,
                border:     auth.role === 'admin'     ? '1px solid rgba(255,165,0,0.3)'
                          : auth.role === 'engineer'  ? '1px solid rgba(0,212,170,0.25)'
                          : `1px solid ${C.border}`,
              }}>
                {auth.role}
              </span>
            )}
          </div>
        </header>

        <div style={{ padding: '28px 28px' }}>
          <Outlet />
        </div>
      </main>

      {showChangePw && (
        <ChangePasswordModal onClose={() => setShowChangePw(false)} />
      )}
    </div>
  );
}
