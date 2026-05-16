import React from 'react';

const SkeletonPanel: React.FC = () => {
    const shimmerStyle = {
        background: "var(--border-hi)",
        borderRadius: "8px",
        animation: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
    };

    return (
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12 }}>
            {/* Header Skeleton */}
            <div style={{ padding: "24px 28px", display: "flex", gap: 24, borderBottom: "1px solid var(--border)" }}>
                <div style={{ ...shimmerStyle, width: 128, height: 128, borderRadius: "50%" }} />
                <div style={{ display: "flex", flexDirection: "column", gap: 12, justifyContent: "center", flex: 1 }}>
                    <div style={{ ...shimmerStyle, height: 28, width: "60%" }} />
                    <div style={{ ...shimmerStyle, height: 16, width: "80%" }} />
                    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                        <div style={{ ...shimmerStyle, height: 24, width: 100, borderRadius: 12 }} />
                        <div style={{ ...shimmerStyle, height: 24, width: 120, borderRadius: 12 }} />
                    </div>
                </div>
            </div>

            {/* Body Skeleton */}
            <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 16 }}>
                <div style={{ ...shimmerStyle, height: 20, width: "30%" }} />
                <div style={{ ...shimmerStyle, height: 60, width: "100%" }} />
                <div style={{ ...shimmerStyle, height: 60, width: "100%" }} />
            </div>
        </div>
    );
};

export default SkeletonPanel;