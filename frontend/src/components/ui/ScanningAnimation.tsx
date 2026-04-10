import React from 'react';

const ScanningAnimation: React.FC = () => {
    return (
        <div style={{
            position: "relative", overflow: "hidden",
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: "40px 28px",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 20,
        }}>
            {/* Scan line */}
            <div style={{
                position: "absolute", left: 0, right: 0, height: 2,
                background: "linear-gradient(90deg, transparent, var(--accent2), transparent)",
                animation: "scan-line 1.6s linear infinite",
                opacity: 0.6,
            }} />

            {/* Doc icon */}
            <div style={{ position: "relative" }}>
                <div style={{
                    position: "absolute", inset: -12, borderRadius: "50%",
                    border: "2px solid var(--accent2)",
                    animation: "pulse-ring 1.8s ease infinite",
                }} />
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <rect x="8" y="4" width="26" height="34" rx="3" stroke="var(--accent2)" strokeWidth="1.5" />
                    <path d="M34 4l6 6v28a2 2 0 01-2 2H10" stroke="var(--accent2)" strokeWidth="1.5" />
                    <path d="M34 4v6h6" stroke="var(--accent2)" strokeWidth="1.5" />
                    <line x1="14" y1="16" x2="28" y2="16" stroke="var(--accent2)" strokeWidth="1.2" strokeLinecap="round" />
                    <line x1="14" y1="21" x2="30" y2="21" stroke="var(--accent2)" strokeWidth="1.2" strokeLinecap="round" />
                    <line x1="14" y1="26" x2="24" y2="26" stroke="var(--accent2)" strokeWidth="1.2" strokeLinecap="round" />
                </svg>
            </div>

            <div style={{ textAlign: "center" }}>
                <div style={{ fontFamily: "var(--font-head)", fontSize: 16, fontWeight: 700, marginBottom: 6, color: "var(--accent2)" }}>
                    Analyzing with Llama-3.3-70b
                    <span style={{ animation: "blink 1s step-end infinite" }}>_</span>
                </div>
                <div style={{ fontSize: 11, color: "var(--muted)" }}>Extracting signals · Matching keywords · Generating tips</div>
            </div>
        </div>
    );
};

export default ScanningAnimation;