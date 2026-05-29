import { useCallback, useState } from 'react';
import { validateVideoFile } from '../../api/videoApi';

interface VideoDropZoneProps {
    onFileSelect: (file: File) => void;
    disabled?: boolean;
}

export const VideoDropZone = ({ onFileSelect, disabled }: VideoDropZoneProps) => {
    const [isDragging, setIsDragging] = useState(false);
    const [validationError, setError] = useState<string | null>(null);

    const handleFile = useCallback((file: File) => {
        const err = validateVideoFile(file);
        if (err) { setError(err); return; }
        setError(null);
        onFileSelect(file);
    }, [onFileSelect]);

    const onDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (disabled) return;
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    }, [disabled, handleFile]);

    const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
    };

    return (
        <div
            className="fade-up-2"
            onDrop={onDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => document.getElementById("video-upload")?.click()}
            style={{
                border: `1.5px dashed ${isDragging ? "var(--accent2)" : "var(--border-hi)"}`,
                borderRadius: 12,
                padding: "32px 24px",
                display: "flex", flexDirection: "column", alignItems: "center", gap: 12,
                cursor: disabled ? "not-allowed" : "pointer",
                background: isDragging ? "rgba(74, 240, 200, .04)" : "var(--surface)",
                transition: "all .2s ease",
                opacity: disabled ? 0.5 : 1,
                position: "relative"
            }}
        >
            <input
                id="video-upload"
                type="file"
                accept=".mp4,.webm,.mov"
                style={{ display: "none" }}
                onChange={onInputChange}
                disabled={disabled}
            />

            {/* <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <rect x="6" y="8" width="24" height="20" rx="2" stroke="var(--muted)" strokeWidth="1.5" />
                <path d="M14 18l8 5v-10l-8 5z" stroke="var(--accent2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg> */}
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <rect x="6" y="8" width="24" height="20" rx="2" stroke="var(--muted)" strokeWidth="1.5" />
                <path d="M22 18l-8 5v-10l8 5z" stroke="var(--accent2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <div style={{ textAlign: "center" }}>
                <div style={{ fontFamily: "var(--font-head)", fontWeight: 600 }}>Drop your interview video</div>
                <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 4 }}>or click to browse · MP4, WebM, MOV</div>
            </div>

            {validationError && (
                <p style={{
                    marginTop: 16,
                    color: "var(--danger)",
                    fontSize: 13,
                    fontFamily: "var(--font-mono)",
                    pointerEvents: "none"
                }}>
                    {validationError}
                </p>
            )}
        </div>
    );
};