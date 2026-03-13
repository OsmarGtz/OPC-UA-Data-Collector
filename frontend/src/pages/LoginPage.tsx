import { type CSSProperties, FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError } from '../api/client';
import { IconCircuitBoard } from '../components/Icons';
import { useAuth } from '../context/AuthContext';

const C = {
  bg:      '#0d1117',
  card:    '#161b22',
  border:  '#21262d',
  accent:  '#00d4aa',
  textPri: '#e6edf3',
  textSec: '#7d8590',
  input:   '#0d1117',
};

export function LoginPage() {
  const { login }    = useAuth();
  const navigate     = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error,    setError]    = useState<string | null>(null);
  const [loading,  setLoading]  = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: C.bg,
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>
      {/* Background grid pattern */}
      <div style={{ position: 'absolute', inset: 0, opacity: 0.03, backgroundImage: 'radial-gradient(circle, #fff 1px, transparent 1px)', backgroundSize: '28px 28px', pointerEvents: 'none' }} />

      <div style={{ width: 380, position: 'relative' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 52, height: 52, borderRadius: 14,
            background: C.accent,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 16,
            boxShadow: `0 0 28px rgba(0,212,170,0.35)`,
          }}>
            <IconCircuitBoard size={28} color="#0d1117" strokeWidth={2} />
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: C.textPri }}>OPC-UA Dashboard</div>
          <div style={{ fontSize: 13, color: C.textSec, marginTop: 4 }}>Industrial Data Collector</div>
        </div>

        {/* Card */}
        <div style={{
          background: C.card,
          border: `1px solid ${C.border}`,
          borderRadius: 14,
          padding: 32,
        }}>
          <form onSubmit={(e) => void handleSubmit(e)}>
            <div style={{ marginBottom: 18 }}>
              <label style={LABEL}>Username</label>
              <input
                style={INPUT}
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required autoFocus
                placeholder="Enter username"
              />
            </div>

            <div style={{ marginBottom: 6 }}>
              <label style={LABEL}>Password</label>
              <input
                style={INPUT}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div style={{
                marginTop: 16,
                padding: '10px 14px',
                background: 'rgba(255,68,68,0.1)',
                border: '1px solid rgba(255,68,68,0.25)',
                borderRadius: 8,
                fontSize: 13,
                color: '#ff8888',
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 24, width: '100%',
                padding: '11px 0', fontSize: 14, fontWeight: 600,
                borderRadius: 9, border: 'none',
                background: loading ? 'rgba(0,212,170,0.4)' : C.accent,
                color: loading ? C.textSec : '#0d1117',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

const LABEL: CSSProperties = {
  display: 'block',
  fontSize: 11, fontWeight: 600,
  color: '#7d8590',
  marginBottom: 7,
  textTransform: 'uppercase',
  letterSpacing: '0.07em',
};

const INPUT: CSSProperties = {
  width: '100%',
  padding: '10px 13px',
  fontSize: 14,
  borderRadius: 8,
  border: '1px solid #21262d',
  background: '#0d1117',
  color: '#e6edf3',
  outline: 'none',
};
