import React from 'react';
import { HistoryRecord } from '../types';

interface HistorySidebarProps {
    isOpen: boolean;
    onClose: () => void;
    history: HistoryRecord[];
}

const HistorySidebar: React.FC<HistorySidebarProps> = ({ isOpen, onClose, history }) => {
    if (!isOpen) return null;

    return (
        <>
            {/* Overlay */}
            <div
                onClick={onClose}
                style={{ position: "fixed", inset: 0, background: "rgba(11, 12, 15, 0.8)", zIndex: 40 }}
            />

            {/* Sidebar */}
            <div style={{
                position: "fixed", top: 0, right: 0, bottom: 0, width: 320,
                background: "var(--surface)", borderLeft: "1px solid var(--border)",
                zIndex: 50, padding: 24, overflowY: "auto",
                animation: "fadeUp 0.3s ease forwards" // Reusing your existing animation
            }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                    <h2 style={{ fontFamily: "var(--font-head)", fontSize: 18, fontWeight: 700 }}>Recent Scans</h2>
                    <button onClick={onClose} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: 20 }}>×</button>
                </div>

                {history.length === 0 ? (
                    <p style={{ color: "var(--muted)", fontSize: 13 }}>No recent scans found in this session.</p>
                ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {history.map((record, idx) => (
                            <div key={idx} style={{ padding: 16, background: "var(--bg)", border: "1px solid var(--border-hi)", borderRadius: 8 }}>
                                <div style={{ color: "var(--accent2)", fontSize: 13, fontWeight: 600, marginBottom: 4, wordBreak: "break-all" }}>
                                    {record.filename}
                                </div>
                                <div style={{ color: "var(--muted)", fontSize: 11 }}>
                                    {new Date(record.timestamp).toLocaleString()}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </>
    );
};

export default HistorySidebar;