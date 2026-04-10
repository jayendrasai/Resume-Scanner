import React from 'react';

interface TipCardProps {
    tip: string;
    idx: number;
}

const TipCard: React.FC<TipCardProps> = ({ tip, idx }) => {
    return (
        <div style={{
            display: "flex",
            gap: "16px",
            padding: "16px",
            marginBottom: "12px",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "rgba(0,0,0,0.02)"
        }}>
            <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                width: "28px",
                height: "28px",
                borderRadius: "50%",
                background: "var(--border)",
                fontSize: "12px",
                fontWeight: "bold",
                color: "var(--muted)"
            }}>
                {idx + 1}
            </div>
            <div style={{
                fontSize: "14px",
                lineHeight: "1.5",
                paddingTop: "4px"
            }}>
                {tip}
            </div>
        </div>
    );
};

export default TipCard;
