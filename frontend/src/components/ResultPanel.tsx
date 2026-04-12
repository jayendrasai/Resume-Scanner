import React from 'react';
import ScoreRing from './ui/ScoreRing';
import Chip from './ui/Chip';
import TipCard from './TipCard';
import { AnalysisData } from '../types';

interface ResultPanelProps {
    data: AnalysisData;
}

const ResultPanel: React.FC<ResultPanelProps> = ({ data }) => {
    const { match_score, missing_keywords = [], tips = [] } = data;

    return (
        <div style={{ animation: "fadeUp .5s ease both" }}>
            {/* Header row */}
            <div style={{
                display: "flex", alignItems: "center", gap: 24,
                padding: "24px 28px",
                background: "var(--surface)",
                borderRadius: "12px 12px 0 0",
                borderBottom: "1px solid var(--border)",
            }}>
                <ScoreRing score={match_score} />
                {/* <ScoreRing score={Math.round(match_score * 100)} /> */}
                <div>
                    <div style={{ fontFamily: "var(--font-head)", fontSize: 22, fontWeight: 700, marginBottom: 6 }}>
                        Resume Analysis Complete
                    </div>
                    <div style={{ fontSize: 12, color: "var(--muted)" }}>
                        {match_score >= 70
                            ? "Strong match — minor refinements advised."
                            : match_score >= 45
                                ? "Moderate match — targeted improvements recommended."
                                : "Low match — significant alignment work needed."}
                    </div>
                    <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
                        <Chip
                            label={`${missing_keywords.length} missing keywords`}
                            variant={missing_keywords.length > 5 ? "danger" : "warn"}
                        />
                        <Chip label={`${tips.length} improvement tips`} />
                    </div>
                </div>
            </div>

            {/* Missing keywords */}
            {missing_keywords.length > 0 && (
                <div style={{
                    padding: "20px 28px",
                    borderBottom: "1px solid var(--border)",
                    background: "var(--surface)",
                }}>
                    <div style={{ fontSize: 11, letterSpacing: "0.12em", color: "var(--muted)", marginBottom: 12, fontWeight: 600 }}>
                        MISSING KEYWORDS
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap" }}>
                        {missing_keywords.map((kw, i) => (
                            <Chip key={i} label={kw} variant="warn" />
                        ))}
                    </div>
                </div>
            )}

            {/* Tips */}
            {tips.length > 0 && (
                <div style={{
                    padding: "20px 28px",
                    background: "var(--surface)",
                    borderRadius: "0 0 12px 12px",
                }}>
                    <div style={{ fontSize: 11, letterSpacing: "0.12em", color: "var(--muted)", marginBottom: 16, fontWeight: 600 }}>
                        IMPROVEMENT TIPS
                    </div>
                    {tips.map((tip, i) => <TipCard key={i} tip={tip} idx={i} />)}
                </div>
            )}
        </div>
    );
};

export default ResultPanel;