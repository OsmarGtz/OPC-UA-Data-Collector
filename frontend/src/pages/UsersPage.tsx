import { type CSSProperties, type FormEvent, useState } from 'react';
import { ChangePasswordModal } from '../components/ChangePasswordModal';
import { IconClose, IconPlus, IconUsers } from '../components/Icons';
import { useAuth } from '../context/AuthContext';
import { useCreateUser, useDeleteUser, useUpdateUser, useUsers } from '../hooks/useUsers';
import type { User } from '../types';

const C = {
  card:    '#161b22',
  inner:   '#0d1117',
  border:  '#21262d',
  accent:  '#00d4aa',
  textPri: '#e6edf3',
  textSec: '#7d8590',
  rowHov:  '#1c2128',
};

export function UsersPage() {
  const { auth } = useAuth();
  const { data: users = [], isLoading } = useUsers();
  const [showCreate, setShowCreate] = useState(false);

  if (auth.role !== 'admin') {
    return (
      <div style={{ padding: 48, textAlign: 'center', color: C.textSec, fontSize: 14 }}>
        Access denied — admin role required.
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: C.textPri, margin: 0 }}>User Management</h1>
          <p style={{ fontSize: 13, color: C.textSec, marginTop: 4 }}>
            {users.length} user{users.length !== 1 ? 's' : ''} registered
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '8px 16px', fontSize: 13, fontWeight: 600,
            borderRadius: 8, border: 'none',
            background: C.accent, color: C.inner, cursor: 'pointer',
          }}
        >
          <IconPlus size={14} color={C.inner} />
          New User
        </button>
      </div>

      {/* Table */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ padding: 40, textAlign: 'center', color: C.textSec, fontSize: 13 }}>Loading users…</div>
        ) : (
          <UserTable users={users} currentUsername={auth.username ?? ''} />
        )}
      </div>

      {showCreate && <CreateUserModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function UserTable({ users, currentUsername }: { users: User[]; currentUsername: string }) {
  const { mutate: updateUser, isPending: isUpdating } = useUpdateUser();
  const { mutate: deleteUser, isPending: isDeleting  } = useDeleteUser();
  const [confirmDelete,  setConfirmDelete]  = useState<number | null>(null);
  const [changePwTarget, setChangePwTarget] = useState<User | null>(null);

  if (users.length === 0) {
    return (
      <div style={{ padding: '48px 0', textAlign: 'center', color: C.textSec, fontSize: 14 }}>
        <IconUsers size={28} color={C.accent} />
        <p style={{ marginTop: 10 }}>No users yet.</p>
      </div>
    );
  }

  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: `1px solid ${C.border}` }}>
              {['Username', 'Email', 'Role', 'Status', 'Password', 'Delete'].map((h) => (
                <th key={h} style={TH}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isSelf = u.username === currentUsername;
              return (
                <tr
                  key={u.id}
                  style={{ borderBottom: `1px solid ${C.border}` }}
                  onMouseEnter={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = C.rowHov)}
                  onMouseLeave={(e) => ((e.currentTarget as HTMLTableRowElement).style.background = 'transparent')}
                >
                  {/* Username */}
                  <td style={{ ...TD, color: C.textPri, fontWeight: 500 }}>
                    {u.username}
                    {isSelf && <span style={{ marginLeft: 6, fontSize: 10, color: C.textSec, fontWeight: 400 }}>(you)</span>}
                  </td>

                  {/* Email */}
                  <td style={{ ...TD, color: C.textSec }}>{u.email}</td>

                  {/* Role */}
                  <td style={TD}>
                    <select
                      value={u.role}
                      disabled={isUpdating}
                      onChange={(e) => updateUser({ id: u.id, data: { role: e.target.value as User['role'] } })}
                      style={{
                        background: C.inner,
                        color: u.role === 'admin' ? '#ffa500' : u.role === 'engineer' ? C.accent : C.textSec,
                        border: `1px solid ${C.border}`, borderRadius: 6,
                        padding: '3px 8px', fontSize: 12, cursor: 'pointer',
                      }}
                    >
                      <option value="operator">operator</option>
                      <option value="engineer">engineer</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>

                  {/* Active toggle */}
                  <td style={TD}>
                    <button
                      disabled={isSelf || isUpdating}
                      onClick={() => updateUser({ id: u.id, data: { is_active: !u.is_active } })}
                      style={{
                        padding: '3px 10px', fontSize: 11, fontWeight: 600,
                        borderRadius: 5, cursor: isSelf ? 'not-allowed' : 'pointer',
                        border: u.is_active ? '1px solid rgba(0,212,170,0.3)' : '1px solid rgba(255,68,68,0.3)',
                        background: u.is_active ? 'rgba(0,212,170,0.08)' : 'rgba(255,68,68,0.08)',
                        color: u.is_active ? C.accent : '#ff6666',
                        opacity: isSelf ? 0.4 : 1,
                      }}
                    >
                      {u.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </td>

                  {/* Change password */}
                  <td style={TD}>
                    <button
                      onClick={() => setChangePwTarget(u)}
                      style={GHOST_BTN}
                    >
                      Set Password
                    </button>
                  </td>

                  {/* Delete */}
                  <td style={TD}>
                    {confirmDelete === u.id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 11, color: '#ff6666' }}>Delete?</span>
                        <button
                          onClick={() => { deleteUser(u.id); setConfirmDelete(null); }}
                          disabled={isDeleting}
                          style={{ ...DANGER_BTN, padding: '3px 10px', fontSize: 11 }}
                        >
                          Yes
                        </button>
                        <button onClick={() => setConfirmDelete(null)} style={{ ...SEC_BTN, padding: '3px 10px', fontSize: 11 }}>
                          No
                        </button>
                      </div>
                    ) : (
                      <button
                        disabled={isSelf}
                        onClick={() => setConfirmDelete(u.id)}
                        style={{
                          ...DANGER_BTN, padding: '3px 12px', fontSize: 11,
                          opacity: isSelf ? 0.3 : 1, cursor: isSelf ? 'not-allowed' : 'pointer',
                        }}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {changePwTarget && (
        <ChangePasswordModal
          targetUserId={changePwTarget.id}
          targetUsername={changePwTarget.username}
          onClose={() => setChangePwTarget(null)}
        />
      )}
    </>
  );
}

function CreateUserModal({ onClose }: { onClose: () => void }) {
  const { mutateAsync, isPending, isError, error } = useCreateUser();
  const [username, setUsername] = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [role,     setRole]     = useState<User['role']>('operator');

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await mutateAsync({ username, email, password, role });
    onClose();
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div style={{ width: 420, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 28, boxShadow: '0 24px 64px rgba(0,0,0,0.6)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: C.textPri, margin: 0 }}>New User</h2>
            <p style={{ fontSize: 12, color: C.textSec, marginTop: 3 }}>Create a new account</p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: C.textSec, cursor: 'pointer', padding: 4, display: 'flex' }}>
            <IconClose size={16} />
          </button>
        </div>

        <form onSubmit={(e) => void handleSubmit(e)}>
          <Field label="Username">
            <input style={INPUT} value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus placeholder="e.g. johndoe" />
          </Field>
          <div style={{ marginTop: 14 }}>
            <Field label="Email">
              <input style={INPUT} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="e.g. john@example.com" />
            </Field>
          </div>
          <div style={{ marginTop: 14 }}>
            <Field label="Password">
              <input style={INPUT} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Min. 6 characters" />
            </Field>
          </div>
          <div style={{ marginTop: 14 }}>
            <Field label="Role">
              <select style={INPUT} value={role} onChange={(e) => setRole(e.target.value as User['role'])}>
                <option value="operator">Operator — read-only access</option>
                <option value="engineer">Engineer — full access</option>
                <option value="admin">Admin — user management</option>
              </select>
            </Field>
          </div>

          {isError && (
            <div style={{ marginTop: 14, padding: '9px 12px', background: 'rgba(255,68,68,0.1)', border: '1px solid rgba(255,68,68,0.25)', borderRadius: 8, fontSize: 13, color: '#ff8888' }}>
              {error instanceof Error ? error.message : 'Failed to create user'}
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={SEC_BTN}>Cancel</button>
            <button type="submit" disabled={isPending} style={PRI_BTN}>
              {isPending ? 'Creating…' : 'Create User'}
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

const TH: CSSProperties = {
  textAlign: 'left', padding: '10px 16px',
  fontSize: 11, fontWeight: 600,
  color: C.textSec, textTransform: 'uppercase', letterSpacing: '0.07em',
};
const TD: CSSProperties = { padding: '12px 16px', color: C.textSec, verticalAlign: 'middle' };
const INPUT: CSSProperties = {
  width: '100%', padding: '9px 11px', fontSize: 13,
  borderRadius: 7, border: `1px solid ${C.border}`,
  background: C.inner, color: C.textPri, outline: 'none', boxSizing: 'border-box',
};
const PRI_BTN: CSSProperties = {
  padding: '9px 22px', fontSize: 13, fontWeight: 600,
  borderRadius: 8, border: 'none', background: C.accent, color: C.inner, cursor: 'pointer',
};
const SEC_BTN: CSSProperties = {
  padding: '9px 16px', fontSize: 13,
  borderRadius: 8, border: `1px solid ${C.border}`, background: C.inner, color: C.textSec, cursor: 'pointer',
};
const DANGER_BTN: CSSProperties = {
  padding: '5px 14px', fontSize: 12, fontWeight: 600,
  borderRadius: 6, border: '1px solid rgba(255,68,68,0.3)',
  background: 'rgba(255,68,68,0.08)', color: '#ff6666', cursor: 'pointer',
};
const GHOST_BTN: CSSProperties = {
  padding: '3px 10px', fontSize: 11, fontWeight: 500,
  borderRadius: 6, border: `1px solid ${C.border}`,
  background: 'transparent', color: C.textSec, cursor: 'pointer',
};
