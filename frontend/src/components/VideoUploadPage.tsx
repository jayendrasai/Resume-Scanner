import { useState, useCallback } from 'react';
import { GlobalStyle } from '../styles/GlobalStyles';
import { VideoDropZone } from './ui/VideoDropZone';
import { VideoResultsPanel } from './ui/VideoResultsPanel';
import SceletonPanel from './ui/SceletonPanel';
import { useJobPoller } from '../hooks/useJobPoller';
import {
    getPresignedUrl,
    uploadToS3,
    confirmUpload,
} from '../api/videoApi';
import type { JobResult, VideoPageStatus } from '../types';

export const VideoUploadPage = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploadProgress, setProgress] = useState(0);
    const [pageStatus, setPageStatus] = useState<VideoPageStatus>('idle');
    const [submitError, setSubmitError] = useState<string | null>(null);

    const { status: pollStatus, result, error: pollError,
        startPolling, reset: resetPoller } = useJobPoller();

    const effectiveStatus: VideoPageStatus =
        pageStatus === 'uploading' ? 'uploading' : pollStatus;

    const handleSubmit = useCallback(async () => {
        if (!file) return;
        setSubmitError(null);
        setPageStatus('uploading');
        setProgress(0);

        try {
            // Step 1: get presigned URL
            const { upload_url, object_key } = await getPresignedUrl(file.name);

            // Step 2: PUT directly to S3 with progress
            await uploadToS3(upload_url, file, setProgress);

            // Step 3: confirm + enqueue Celery task
            const taskId = await confirmUpload(object_key);

            // Step 4: start polling
            setPageStatus('queued');
            startPolling(taskId);

        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : 'Upload failed.';
            // Surface 403 clearly — most likely free user hitting premium gate
            if (typeof err === 'object' && err !== null && 'response' in err) {
                const axiosErr = err as { response?: { status?: number } };
                if (axiosErr.response?.status === 403) {
                    setSubmitError(
                        'Video analysis requires a premium subscription. Please upgrade.'
                    );
                    setPageStatus('idle');
                    return;
                }
            }
            setSubmitError(msg);
            setPageStatus('idle');
        }
    }, [file, startPolling]);

    const handleReset = useCallback(() => {
        setFile(null);
        setProgress(0);
        setPageStatus('idle');
        setSubmitError(null);
        resetPoller();
    }, [resetPoller]);

    // ── Render: results ─────────────────────────────────────────────────
    if (effectiveStatus === 'completed' && result) {
        return (
            <VideoResultsPanel
                result={result as JobResult}
                onReset={handleReset}
            />
        );
    }

    // ── Render: processing skeleton ─────────────────────────────────────
    if (effectiveStatus === 'processing' || effectiveStatus === 'queued') {
        return (
            <div style={{ position: "relative", zIndex: 1, maxWidth: 840, margin: "0 auto", padding: "40px 20px 80px" }}>
                <div className="flex flex-col items-center gap-6 w-full mx-auto">
                    <SceletonPanel />
                    <p style={{ color: "var(--muted)", fontSize: 14, animation: "pulse 2s infinite" }}>
                        {effectiveStatus === 'queued'
                            ? 'Upload complete — queuing analysis...'
                            : 'Extracting audio and analysing your interview...'}
                    </p>
                </div>
            </div>
        );
    }

    // ── Render: upload form ─────────────────────────────────────────────
    return (
        <>
            <GlobalStyle />
            <div style={{ position: "relative", zIndex: 1, maxWidth: 840, margin: "0 auto", padding: "40px 20px 80px" }}>
                {/* ── Header Section ── */}
                <header className="fade-up" style={{ marginBottom: 48, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                    <div>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
                            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--accent2)", boxShadow: "0 0 10px var(--accent2)" }} />
                            <span style={{ fontSize: 11, color: "var(--muted)", letterSpacing: "0.14em" }}>AI INTERVIEW COACH v0.1</span>
                        </div>
                        <h1 style={{ fontFamily: "var(--font-head)", fontSize: "clamp(32px, 5vw, 52px)", fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.02em" }}>
                            Speak with confidence.<br />
                            <span style={{ color: "var(--accent2)" }}>Master your delivery</span> first.
                        </h1>



                    </div>
                </header>

                <div style={{ display: "grid", gap: 16 }}>
                    {(submitError || pollError || effectiveStatus === 'failed') && (
                        <div style={{
                            color: "var(--danger)",
                            background: "rgba(240, 74, 106, 0.1)",
                            padding: "12px 16px",
                            borderRadius: 10,
                            border: "1px solid rgba(240, 74, 106, 0.3)",
                            fontSize: 13,
                            fontFamily: "var(--font-mono)"
                        }}>
                            ⚠️ {submitError ?? pollError ?? "Analysis failed. Please try again with a different video."}
                        </div>
                    )}

                    <VideoDropZone
                        onFileSelect={setFile}
                        disabled={effectiveStatus === 'uploading'}
                    />

                    {file && effectiveStatus !== 'uploading' && (
                        <div style={{
                            display: "flex", alignItems: "center", justifyContent: "space-between",
                            background: "var(--surface)", borderRadius: 10, padding: "14px 16px",
                            border: "1.5px solid var(--border-hi)"
                        }}>
                            <span style={{ color: "var(--text)", fontSize: 13, fontFamily: "var(--font-mono)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "70%" }}>
                                {file.name}
                            </span>
                            <span style={{ color: "var(--muted)", fontSize: 12, fontFamily: "var(--font-mono)" }}>
                                {(file.size / 1024 / 1024).toFixed(1)} MB
                            </span>
                        </div>
                    )}

                    {effectiveStatus === 'uploading' && (
                        <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "14px 16px", background: "var(--surface)", borderRadius: 10, border: "1.5px solid var(--border-hi)" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--muted)", fontFamily: "var(--font-mono)" }}>
                                <span>Uploading to secure storage...</span>
                                <span>{uploadProgress}%</span>
                            </div>
                            <div style={{ width: "100%", background: "var(--border)", borderRadius: 4, height: 6 }}>
                                <div
                                    style={{ background: "var(--accent2)", height: 6, borderRadius: 4, transition: "all 0.3s", width: `${uploadProgress}%` }}
                                />
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleSubmit}
                        disabled={!file || effectiveStatus === 'uploading'}
                        style={{
                            padding: "16px 28px",
                            borderRadius: 10,
                            background: (!file || effectiveStatus === 'uploading') ? "var(--border)" : "var(--accent2)",
                            color: (!file || effectiveStatus === 'uploading') ? "var(--muted)" : "#0b0c0f",
                            fontFamily: "var(--font-head)",
                            fontWeight: 700,
                            cursor: (!file || effectiveStatus === 'uploading') ? "not-allowed" : "pointer",
                            transition: "all 0.2s"
                        }}
                    >
                        {effectiveStatus === 'uploading'
                            ? `Uploading... ${uploadProgress}%`
                            : (file ? "→ Analyse Interview" : "Upload Video to continue")}
                    </button>
                </div>
            </div>

        </>
    );
};