import { useState } from 'react';
import { login, register } from '../api/authApi';
import { saveToken } from '../utils/auth';

interface AuthPageProps {
    onAuth: () => void;
}

type AuthTab = 'login' | 'register';
type FieldError = { email?: string; password?: string; confirm?: string; general?: string };

const inputStyle: React.CSSProperties = {
    width: '100%',
    background: 'var(--bg)',
    border: '1px solid var(--border-hi)',
    borderRadius: '8px',
    padding: '10px 14px',
    color: 'var(--text)',
    fontFamily: 'var(--font-mono)',
    fontSize: '13px',
    outline: 'none',
    transition: 'border-color 0.2s',
};

const labelStyle: React.CSSProperties = {
    fontSize: '11px',
    color: 'var(--muted)',
    fontFamily: 'var(--font-mono)',
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    marginBottom: '6px',
    display: 'block',
};

export const AuthPage = ({ onAuth }: AuthPageProps) => {
    const [tab, setTab] = useState<AuthTab>('login');
    const [email, setEmail] = useState('');
    const [password, setPass] = useState('');
    const [confirm, setConfirm] = useState('');
    const [errors, setErrors] = useState<FieldError>({});
    const [loading, setLoading] = useState(false);
    const [focusedField, setFocused] = useState<string | null>(null);

    const validate = (): boolean => {
        const errs: FieldError = {};
        if (!email.includes('@')) errs.email = 'Enter a valid email address';
        if (password.length < 6) errs.password = 'Password must be at least 6 characters';
        if (tab === 'register' && password !== confirm)
            errs.confirm = 'Passwords do not match';
        setErrors(errs);
        return Object.keys(errs).length === 0;
    };

    const handleSubmit = async () => {
        if (!validate()) return;
        setLoading(true);
        setErrors({});
        try {
            const token = tab === 'login'
                ? await login(email, password)
                : await register(email, password);
            saveToken(token);
            onAuth();
        } catch (err: unknown) {
            const status = (err as { response?: { status?: number } })
                ?.response?.status;
            if (status === 401 || status === 422) {
                setErrors({ general: 'Invalid email or password.' });
            } else if (status === 409) {
                setErrors({ general: 'An account with this email already exists.' });
            } else {
                setErrors({ general: 'Something went wrong. Please try again.' });
            }
        } finally {
            setLoading(false);
        }
    };

    const switchTab = (t: AuthTab) => {
        setTab(t);
        setErrors({});
        setPass('');
        setConfirm('');
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            position: 'relative',
            zIndex: 1,
        }}>
            <div className="fade-up" style={{
                width: '100%',
                maxWidth: '400px',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '16px',
                padding: '32px',
            }}>

                {/* Logo mark */}
                <div style={{ marginBottom: '28px' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        marginBottom: '8px',
                    }}>
                        <span style={{
                            width: '28px', height: '28px',
                            background: 'var(--accent)',
                            borderRadius: '6px',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                <path d="M2 3h10M2 7h6M2 11h8" stroke="#0b0c0f"
                                    strokeWidth="1.8" strokeLinecap="round" />
                            </svg>
                        </span>
                        <span style={{
                            fontFamily: 'var(--font-head)',
                            fontWeight: 700,
                            fontSize: '15px',
                            color: 'var(--text)',
                            letterSpacing: '-0.01em',
                        }}>
                            Resume Scanner
                        </span>
                    </div>
                    <p style={{
                        fontSize: '12px',
                        color: 'var(--muted)',
                        fontFamily: 'var(--font-mono)',
                    }}>
                        {tab === 'login'
                            ? 'Sign in to access your account'
                            : 'Create an account to get started'}
                    </p>
                </div>

                {/* Tab switcher */}
                <div style={{
                    display: 'flex',
                    background: 'var(--bg)',
                    borderRadius: '8px',
                    padding: '3px',
                    marginBottom: '24px',
                    border: '1px solid var(--border)',
                }}>
                    {(['login', 'register'] as AuthTab[]).map(t => (
                        <button key={t} onClick={() => switchTab(t)} style={{
                            flex: 1,
                            padding: '7px',
                            borderRadius: '6px',
                            border: 'none',
                            cursor: 'pointer',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '12px',
                            fontWeight: tab === t ? 600 : 400,
                            background: tab === t ? 'var(--border-hi)' : 'transparent',
                            color: tab === t ? 'var(--text)' : 'var(--muted)',
                            transition: 'all 0.2s',
                        }}>
                            {t === 'login' ? 'Sign in' : 'Register'}
                        </button>
                    ))}
                </div>

                {/* Fields */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

                    {/* Email */}
                    <div>
                        <label style={labelStyle}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            onFocus={() => setFocused('email')}
                            onBlur={() => setFocused(null)}
                            placeholder="you@example.com"
                            style={{
                                ...inputStyle,
                                borderColor: errors.email
                                    ? 'var(--danger)'
                                    : focusedField === 'email'
                                        ? 'var(--accent)'
                                        : 'var(--border-hi)',
                            }}
                        />
                        {errors.email && (
                            <p style={{
                                fontSize: '11px', color: 'var(--danger)',
                                marginTop: '4px', fontFamily: 'var(--font-mono)'
                            }}>
                                {errors.email}
                            </p>
                        )}
                    </div>

                    {/* Password */}
                    <div>
                        <label style={labelStyle}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={e => setPass(e.target.value)}
                            onFocus={() => setFocused('password')}
                            onBlur={() => setFocused(null)}
                            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                            placeholder="••••••••"
                            style={{
                                ...inputStyle,
                                borderColor: errors.password
                                    ? 'var(--danger)'
                                    : focusedField === 'password'
                                        ? 'var(--accent)'
                                        : 'var(--border-hi)',
                            }}
                        />
                        {errors.password && (
                            <p style={{
                                fontSize: '11px', color: 'var(--danger)',
                                marginTop: '4px', fontFamily: 'var(--font-mono)'
                            }}>
                                {errors.password}
                            </p>
                        )}
                    </div>

                    {/* Confirm password — register only */}
                    {tab === 'register' && (
                        <div>
                            <label style={labelStyle}>Confirm Password</label>
                            <input
                                type="password"
                                value={confirm}
                                onChange={e => setConfirm(e.target.value)}
                                onFocus={() => setFocused('confirm')}
                                onBlur={() => setFocused(null)}
                                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                                placeholder="••••••••"
                                style={{
                                    ...inputStyle,
                                    borderColor: errors.confirm
                                        ? 'var(--danger)'
                                        : focusedField === 'confirm'
                                            ? 'var(--accent)'
                                            : 'var(--border-hi)',
                                }}
                            />
                            {errors.confirm && (
                                <p style={{
                                    fontSize: '11px', color: 'var(--danger)',
                                    marginTop: '4px', fontFamily: 'var(--font-mono)'
                                }}>
                                    {errors.confirm}
                                </p>
                            )}
                        </div>
                    )}

                    {/* General error */}
                    {errors.general && (
                        <div style={{
                            background: 'rgba(240,74,106,0.08)',
                            border: '1px solid rgba(240,74,106,0.3)',
                            borderRadius: '8px',
                            padding: '10px 14px',
                            fontSize: '12px',
                            color: 'var(--danger)',
                            fontFamily: 'var(--font-mono)',
                        }}>
                            {errors.general}
                        </div>
                    )}

                    {/* Submit */}
                    <button
                        onClick={handleSubmit}
                        disabled={loading}
                        style={{
                            width: '100%',
                            padding: '11px',
                            borderRadius: '8px',
                            border: 'none',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            background: loading ? 'var(--border-hi)' : 'var(--accent)',
                            color: loading ? 'var(--muted)' : '#0b0c0f',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '13px',
                            fontWeight: 600,
                            transition: 'all 0.2s',
                            marginTop: '4px',
                        }}
                    >
                        {loading
                            ? 'Please wait...'
                            : tab === 'login' ? 'Sign in' : 'Create account'}
                    </button>

                </div>

                {/* Footer note */}
                <p style={{
                    marginTop: '20px',
                    fontSize: '11px',
                    color: 'var(--muted)',
                    textAlign: 'center',
                    fontFamily: 'var(--font-mono)',
                    lineHeight: 1.6,
                }}>
                    {tab === 'login'
                        ? "Don't have an account? Click Register above."
                        : 'Already have an account? Click Sign in above.'}
                </p>
            </div>
        </div>
    );
};