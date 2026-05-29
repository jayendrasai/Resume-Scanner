import { useEffect, useState } from 'react';
import { getMe, getBillingStatus, createOrder } from '../api/authApi';
import { saveToken, removeToken, refreshToken } from '../utils/auth';
import type { UserProfile, PassStatus } from '../api/authApi';




interface AccountPageProps {
    onSignOut: () => void;
}

const sectionStyle: React.CSSProperties = {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: '12px',
    padding: '20px 24px',
};

const rowStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
};

const mutedLabel: React.CSSProperties = {
    fontSize: '11px',
    color: 'var(--muted)',
    fontFamily: 'var(--font-mono)',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
};

const valueStyle: React.CSSProperties = {
    fontSize: '13px',
    color: 'var(--text)',
    fontFamily: 'var(--font-mono)',
};

const formatExpiry = (iso: string | null): string => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', {
        day: 'numeric', month: 'short', year: 'numeric'
    });
};

const daysRemaining = (iso: string | null): number => {
    if (!iso) return 0;
    const diff = new Date(iso).getTime() - Date.now();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
};

export const AccountPage = ({ onSignOut }: AccountPageProps) => {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [billing, setBilling] = useState<PassStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [upgrading, setUpgrading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const [prof, bill] = await Promise.all([getMe(), getBillingStatus()]);
                setProfile(prof);
                setBilling(bill);
            } catch {
                setError('Failed to load account data.');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const handleUpgrade = async () => {
        setUpgrading(true);
        setError(null);

        try {
            const order = await createOrder();

            const options = {
                key: import.meta.env.VITE_RAZORPAY_KEY_ID,
                amount: order.amount_inr_paise,
                currency: order.currency,
                name: "Your App Name",
                description: "30-Day Premium Pass",
                order_id: order.order_id,
                handler: async function (response: any) {
                    console.log("Payment successful!", response.razorpay_payment_id);

                    // --- POLLING LOGIC STARTS HERE ---
                    let attempts = 0;
                    const maxAttempts = 10; // Poll up to 10 times (30 seconds total)
                    let isUpgraded = false;

                    while (attempts < maxAttempts) {
                        try {
                            const status = await getBillingStatus();
                            console.log(`Poll attempt ${attempts + 1}:`, status);

                            if (status.tier === 'premium') {
                                // Success! The webhook has finished processing.

                                // 1. Update the billing state with the new expiration data
                                setBilling(status);

                                // 2. Update the profile state so `isPremium` turns true instantly
                                setProfile(prev => prev ? { ...prev, tier: 'premium' } : null);

                                // Optional: If you prefer to fetch a perfectly fresh profile from the backend:
                                // const freshProfile = await getMe();
                                // setProfile(freshProfile);

                                isUpgraded = true;
                                break; // Exit the while loop immediately
                            }
                        } catch (err) {
                            console.error("Polling check failed", err);
                        }

                        // Wait 3 seconds before asking the server again
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        attempts++;
                    }

                    // Fallback if the webhook is heavily delayed
                    if (!isUpgraded) {
                        console.warn("Webhook is taking longer than expected.");
                        // Optional fallback UI notification could go here
                    }
                    // --- POLLING LOGIC ENDS HERE ---
                },
                theme: {
                    color: "#3399cc",
                },
            };

            const rzp = new (window as any).Razorpay(options);

            rzp.on('payment.failed', function (response: any) {
                setError(`Payment failed: ${response.error.description}`);
            });

            rzp.open();

        } catch (err) {
            setError('Could not initiate payment. Please try again.');
        } finally {
            setUpgrading(false);
        }
    };

    const handleSignOut = () => {
        removeToken();
        onSignOut();
    };

    if (loading) {
        return (
            <div style={{
                display: 'flex', justifyContent: 'center',
                alignItems: 'center', minHeight: '300px',
            }}>
                <span style={{
                    fontSize: '12px', color: 'var(--muted)',
                    fontFamily: 'var(--font-mono)',
                    animation: 'pulse 1.5s ease infinite',
                }}>
                    Loading account...
                </span>
            </div>
        );
    }

    const isPremium = profile?.tier === 'premium';
    const days = daysRemaining(billing?.premium_expires_at ?? null);

    return (
        <div className="fade-up" style={{
            maxWidth: '480px',
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            padding: '0 16px',
            position: 'relative',
            zIndex: 1,
        }}>

            {/* Header */}
            <div style={{ ...rowStyle, marginBottom: '4px' }}>
                <div>
                    <h2 style={{
                        fontFamily: 'var(--font-head)',
                        fontWeight: 700,
                        fontSize: '18px',
                        color: 'var(--text)',
                        letterSpacing: '-0.02em',
                    }}>
                        Account
                    </h2>
                    <p style={{
                        fontSize: '12px', color: 'var(--muted)',
                        fontFamily: 'var(--font-mono)', marginTop: '2px',
                    }}>
                        {profile?.email}
                    </p>
                </div>
                <button onClick={handleSignOut} style={{
                    padding: '7px 14px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-hi)',
                    background: 'transparent',
                    color: 'var(--muted)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                }}>
                    Sign out
                </button>
            </div>

            {/* Plan status */}
            <div style={{
                ...sectionStyle,
                border: isPremium
                    ? '1px solid rgba(200,240,74,0.25)'
                    : '1px solid var(--border)',
            }}>
                <div style={rowStyle}>
                    <div>
                        <span style={mutedLabel}>Current plan</span>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            marginTop: '6px',
                        }}>
                            <span style={{
                                fontFamily: 'var(--font-head)',
                                fontWeight: 700,
                                fontSize: '20px',
                                color: isPremium ? 'var(--accent)' : 'var(--text)',
                            }}>
                                {isPremium ? 'Premium' : 'Free'}
                            </span>
                            {isPremium && (
                                <span style={{
                                    fontSize: '10px',
                                    background: 'rgba(200,240,74,0.12)',
                                    color: 'var(--accent)',
                                    border: '1px solid rgba(200,240,74,0.25)',
                                    borderRadius: '20px',
                                    padding: '2px 8px',
                                    fontFamily: 'var(--font-mono)',
                                }}>
                                    active
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Days remaining ring — premium only */}
                    {isPremium && (
                        <div style={{ textAlign: 'right' }}>
                            <span style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: '28px',
                                fontWeight: 600,
                                color: days <= 5
                                    ? 'var(--danger)'
                                    : days <= 10
                                        ? 'var(--warn)'
                                        : 'var(--accent2)',
                            }}>
                                {days}
                            </span>
                            <p style={{ ...mutedLabel, marginTop: '2px' }}>
                                days left
                            </p>
                        </div>
                    )}
                </div>

                {isPremium && (
                    <p style={{
                        marginTop: '12px',
                        fontSize: '11px',
                        color: 'var(--muted)',
                        fontFamily: 'var(--font-mono)',
                        borderTop: '1px solid var(--border)',
                        paddingTop: '12px',
                    }}>
                        Access expires {formatExpiry(billing?.premium_expires_at ?? null)}
                    </p>
                )}
            </div>

            {/* Free tier — upgrade CTA */}
            {!isPremium && (
                <div style={{
                    ...sectionStyle,
                    border: '1px solid rgba(74,240,200,0.2)',
                    background: 'rgba(74,240,200,0.03)',
                }}>
                    <p style={{
                        fontFamily: 'var(--font-head)',
                        fontWeight: 600,
                        fontSize: '14px',
                        color: 'var(--text)',
                        marginBottom: '8px',
                    }}>
                        Upgrade to Premium
                    </p>
                    <p style={{
                        fontSize: '12px',
                        color: 'var(--muted)',
                        fontFamily: 'var(--font-mono)',
                        lineHeight: 1.6,
                        marginBottom: '16px',
                    }}>
                        Unlock video interview coaching, unlimited scans,
                        and AI communication analysis. ₹2 for 30 days.
                    </p>

                    {/* Feature list */}
                    {[
                        'Unlimited resume scans',
                        'Video interview analysis',
                        'Filler word detection',
                        'Speaking pace feedback',
                        'AI-powered tips',
                    ].map(f => (
                        <div key={f} style={{
                            display: 'flex', alignItems: 'center',
                            gap: '8px', marginBottom: '6px',
                        }}>
                            <span style={{ color: 'var(--accent2)', fontSize: '12px' }}>✦</span>
                            <span style={{
                                fontSize: '12px', color: 'var(--muted)',
                                fontFamily: 'var(--font-mono)',
                            }}>
                                {f}
                            </span>
                        </div>
                    ))}

                    <button
                        onClick={handleUpgrade}
                        disabled={upgrading}
                        style={{
                            width: '100%',
                            marginTop: '16px',
                            padding: '11px',
                            borderRadius: '8px',
                            border: 'none',
                            cursor: upgrading ? 'not-allowed' : 'pointer',
                            background: upgrading
                                ? 'var(--border-hi)'
                                : 'var(--accent2)',
                            color: upgrading ? 'var(--muted)' : '#0b0c0f',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '13px',
                            fontWeight: 600,
                            transition: 'all 0.2s',
                        }}
                    >
                        {upgrading ? 'Redirecting to payment...' : 'Get Premium — ₹2'}
                    </button>
                </div>
            )}

            {/* Premium — renew CTA if expiring soon */}
            {isPremium && days <= 7 && (
                <div style={{
                    ...sectionStyle,
                    border: '1px solid rgba(240,168,74,0.3)',
                    background: 'rgba(240,168,74,0.04)',
                }}>
                    <p style={{
                        fontSize: '12px',
                        color: 'var(--warn)',
                        fontFamily: 'var(--font-mono)',
                        marginBottom: '12px',
                        lineHeight: 1.6,
                    }}>
                        ⚠ Your pass expires in {days} day{days !== 1 ? 's' : ''}.
                        Renew now to avoid interruption.
                    </p>
                    <button
                        onClick={handleUpgrade}
                        disabled={upgrading}
                        style={{
                            width: '100%',
                            padding: '10px',
                            borderRadius: '8px',
                            border: '1px solid rgba(240,168,74,0.4)',
                            background: 'transparent',
                            color: 'var(--warn)',
                            fontFamily: 'var(--font-mono)',
                            fontSize: '13px',
                            fontWeight: 600,
                            cursor: upgrading ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s',
                        }}
                    >
                        {upgrading ? 'Redirecting...' : 'Renew Pass — ₹2'}
                    </button>
                </div>
            )}

            {/* Account info */}
            <div style={sectionStyle}>
                <p style={{ ...mutedLabel, marginBottom: '14px' }}>Account details</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={rowStyle}>
                        <span style={mutedLabel}>Email</span>
                        <span style={valueStyle}>{profile?.email}</span>
                    </div>
                    <div style={{ height: '1px', background: 'var(--border)' }} />
                    <div style={rowStyle}>
                        <span style={mutedLabel}>User ID</span>
                        <span style={{ ...valueStyle, color: 'var(--muted)' }}>
                            #{profile?.id}
                        </span>
                    </div>
                    <div style={{ height: '1px', background: 'var(--border)' }} />
                    <div style={rowStyle}>
                        <span style={mutedLabel}>Member since</span>
                        <span style={{ ...valueStyle, color: 'var(--muted)' }}>
                            Phase 2
                        </span>
                    </div>
                </div>
            </div>

            {error && (
                <div style={{
                    background: 'rgba(240,74,106,0.08)',
                    border: '1px solid rgba(240,74,106,0.3)',
                    borderRadius: '8px',
                    padding: '10px 14px',
                    fontSize: '12px',
                    color: 'var(--danger)',
                    fontFamily: 'var(--font-mono)',
                }}>
                    {error}
                </div>
            )}
        </div>
    );
};