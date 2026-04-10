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
        <span style={{ /* ... use your existing inline styles here ... */ }}>
            {label}
        </span>
    );
};
export default Chip;