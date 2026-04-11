import React from 'react';

interface ChipProps {
    label: string;
    variant?: "default" | "warn" | "danger";
}

const Chip: React.FC<ChipProps> = ({ label, variant = "default" }) => {
    const colors = {
        default: { bg: "rgba(200,240,74,.08)", border: "rgba(200,240,74,.2)", text: "var(--accent)" },
        warn: { bg: "rgba(240,168,74,.08)", border: "rgba(240,168,74,.2)", text: "var(--warn)" },
        danger: { bg: "rgba(240,74,106,.08)", border: "rgba(240,74,106,.18)", text: "var(--danger)" },
    };
    const c = colors[variant];
    return (
        <span style={{
            backgroundColor: c.bg,
            border: `1px solid ${c.border}`,
            color: c.text,
            padding: "0.25rem 0.75rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: 500,
            display: "inline-flex",
            alignItems: "center"
        }}>
            {label}
        </span>
    );
};
export default Chip;