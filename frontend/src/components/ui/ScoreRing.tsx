import React from 'react';

const ScoreRing: React.FC<{ score: number }> = ({ score }) => {
    const r = 46;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    const color = score >= 70 ? "var(--accent)" : score >= 45 ? "var(--warn)" : "var(--danger)";

    return (
        <div style={{ position: "relative", width: 128, height: 128, flexShrink: 0 }}>
            <svg width="128" height="128" viewBox="0 0 128 128" style={{ transform: "rotate(-90deg)" }}>
                <circle cx="64" cy="64" r={r} fill="none" stroke="var(--border-hi)" strokeWidth="8" />
                <circle
                    cx="64" cy="64" r={r}
                    fill="none"
                    stroke={color}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={circ}
                    strokeDashoffset={offset}
                    style={{ animation: "score-fill 1.2s .3s cubic-bezier(.22,1,.36,1) both", transition: "stroke-dashoffset 1s ease" }}
                />
            </svg>
            <div style={{
                position: "absolute", inset: 0,
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center"
            }}>
                <span style={{ fontFamily: "var(--font-head)", fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{score}</span>
                <span style={{ fontSize: 10, color: "var(--muted)", letterSpacing: "0.12em", marginTop: 2 }}>MATCH</span>
            </div>
        </div>
    );
};
export default ScoreRing;