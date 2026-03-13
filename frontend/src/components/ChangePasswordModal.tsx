import { type CSSProperties, type FormEvent, useState } from 'react';
import { useAdminSetPassword, useChangeSelfPassword } from '../hooks/useUsers';
import { IconClose } from './Icons';

const C = {
  bg:      'rgba(0,0,0,0.65)',
  card:    '#161b22',
  inner:   '#0d1117',
  border:  '#21262d',
  accent:  '#00d4aa',
  textPri: '#e6edf3',
  textSec: '#7d8590',
};

interface SelfProps {
  /** Changing own password — no targetUserId needed */
  targetUserId?: undefined;
  targetUsername?: undefined;
  onClose: () => void;
}

interface AdminProps {
  /** Admin changing another user's password */
  targetUserId: number;
  targetUsername: string;
  onClose: () => void;
}

type Props = SelfProps | AdminProps;

export function ChangePasswordModal({ targetUserId, targetUsername, onClose }: Props) {
  const isAdminChanging = targetUserId !== undefined;

  const selfMutation  = useChangeSelfPassword();
  const adminMutation = useAdminSetPassword();

  const isPending = selfMutation.isPending || adminMutation.isPending;
  const isError   = selfMutation.isError   || adminMutation.isError;
  const error     = selfMutation.error     ?? adminMutation.error;

  const [currentPw, setCurrentPw] = useState('');
  const [newPw,     setNewPw]     = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [matchErr,  setMatchErr]  = useState('');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setMatchErr('');
    if (newPw !== confirmPw) {
      setMatchErr('New passwords do not match.');
      return;
    }
    if (newPw.length < 6) {
      setMatchErr('Password must be at least 6 characters.');
      return;
    }
    if (isAdminChanging) {
      await adminMutation.mutateAsync({ id: targetUserId, password: newPw });
    } else {
      await selfMutation.mutateAsync({ current: currentPw, next: newPw });
    }
    onClose();
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: C.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200 }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div style={{ width: 400, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 28, boxShadow: '0 24px 64px rgba(0,0,0,0.6)' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: C.textPri, margin: 0 }}>Change Password</h2>
            <p style={{ fontSize: 12, color: C.textSec, marginTop: 3 }}>
              {isAdminChanging ? `Setting password for ${targetUsername}` : 'Update your password'}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: C.textSec, cursor: 'pointer', padding: 4, display: 'flex' }}>
            <IconClose size={16} />
          </button>
        </div>

        <form onSubmit={(e) => void handleSubmit(e)}>
          {/* Current password — only required when changing own */}
          {!isAdminChanging && (
            <div style={{ marginBottom: 14 }}>
              <Field label="Current Password">
                <input
                  style={INPUT}
                  type="password"
                  value={currentPw}
                  onChange={(e) => setCurrentPw(e.target.value)}
                  required
                  autoFocus
                  placeholder="••••••••"
                />
              </Field>
            </div>
          )}

          <div style={{ marginBottom: 14 }}>
            <Field label="New Password">
              <input
                style={INPUT}
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                required
                autoFocus={isAdminChanging}
                placeholder="Min. 6 characters"
              />
            </Field>
          </div>

          <div>
            <Field label="Confirm New Password">
              <input
                style={INPUT}
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                required
                placeholder="••••••••"
              />
            </Field>
          </div>

          {(matchErr || isError) && (
            <div style={{ marginTop: 14, padding: '9px 12px', background: 'rgba(255,68,68,0.1)', border: '1px solid rgba(255,68,68,0.25)', borderRadius: 8, fontSize: 13, color: '#ff8888' }}>
              {matchErr || (error instanceof Error ? error.message : 'Failed to change password')}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={SEC_BTN}>Cancel</button>
            <button type="submit" disabled={isPending} style={PRI_BTN}>
              {isPending ? 'Saving…' : 'Change Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: C.textSec, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>
        {label}
      </label>
      {children}
    </div>
  );
}

const INPUT: CSSProperties = {
  width: '100%', padding: '9px 11px', fontSize: 13,
  borderRadius: 7, border: `1px solid ${C.border}`,
  background: C.inner, color: C.textPri, outline: 'none',
  boxSizing: 'border-box',
};

const PRI_BTN: CSSProperties = {
  padding: '9px 22px', fontSize: 13, fontWeight: 600,
  borderRadius: 8, border: 'none',
  background: C.accent, color: C.inner, cursor: 'pointer',
};

const SEC_BTN: CSSProperties = {
  padding: '9px 16px', fontSize: 13,
  borderRadius: 8, border: `1px solid ${C.border}`,
  background: C.inner, color: C.textSec, cursor: 'pointer',
};
