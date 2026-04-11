import React, { useState, useRef, useCallback } from "react";
//import axios from "axios";
import api from "../api/axiosConfig";
import { GlobalStyle } from "../styles/GlobalStyles";
import ResultPanel from "./ResultPanel";
import ScanningAnimation from "./ui/ScanningAnimation";
import { AnalysisData, Status } from "../types";

const ResumeScanner: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [jd, setJd] = useState<string>("");
    const [isDragging, setIsDragging] = useState<boolean>(false);
    const [status, setStatus] = useState<Status>("idle");
    const [result, setResult] = useState<AnalysisData | null>(null);
    const [errorMsg, setErrorMsg] = useState<string>("");
    const fileRef = useRef<HTMLInputElement>(null);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const f = e.dataTransfer.files[0];
        if (f?.type === "application/pdf") setFile(f);
    }, []);

    const handleSubmit = async () => {
        if (!file || !jd.trim()) return;
        setStatus("loading");
        setResult(null);
        setErrorMsg("");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("job_description", jd);

        try {
            // Axios Integration
            const response = await api.post<AnalysisData>("/analyze", formData);
            setResult(response.data);
            setStatus("done");
        } catch (err: any) {
            const msg = err.response?.status === 429
                ? "Rate limit reached — try again after 3 hours."
                : err.message;
            setErrorMsg(msg);
            setStatus("error");
        }
    };

    const reset = () => {
        setFile(null); setJd(""); setStatus("idle"); setResult(null); setErrorMsg("");
    };

    const canSubmit = file && jd.trim().length > 20 && status !== "loading";

    return (
        <>
            <GlobalStyle />
            <div style={{ position: "relative", zIndex: 1, maxWidth: 840, margin: "0 auto", padding: "40px 20px 80px" }}>

                {/* Header Section (truncated for brevity - keep your original JSX here) */}

                {(status === "idle" || status === "error") && (
                    <div style={{ display: "grid", gap: 16 }}>

                        {status === "error" && errorMsg && (
                            <div style={{
                                color: "#ff4d4f",
                                background: "rgba(255, 77, 79, 0.1)",
                                padding: "12px 16px",
                                borderRadius: 10,
                                border: "1px solid rgba(255, 77, 79, 0.3)",
                                fontSize: 13,
                                fontFamily: "var(--font-mono)"
                            }}>
                                ⚠️ {errorMsg}
                            </div>
                        )}

                        {/* Drop zone - Visible File Selection Method */}
                        <div
                            className="fade-up-2"
                            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                            onDragLeave={() => setIsDragging(false)}
                            onDrop={handleDrop}
                            onClick={() => fileRef.current?.click()}
                            style={{
                                border: `1.5px dashed ${isDragging ? "var(--accent)" : file ? "var(--accent2)" : "var(--border-hi)"}`,
                                borderRadius: 12,
                                padding: "32px 24px",
                                display: "flex", flexDirection: "column", alignItems: "center", gap: 12,
                                cursor: "pointer",
                                background: isDragging ? "rgba(200,240,74,.04)" : "var(--surface)",
                                transition: "all .2s ease",
                            }}
                        >
                            <input
                                ref={fileRef}
                                type="file"
                                accept=".pdf"
                                style={{ display: "none" }}
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                            />

                            {file ? (
                                <>
                                    {/* Icon when file is selected */}
                                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                                        <circle cx="18" cy="18" r="17" stroke="var(--accent2)" strokeWidth="1.5" />
                                        <path d="M11 18l5 5 9-9" stroke="var(--accent2)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    <div style={{ textAlign: "center" }}>
                                        <div style={{ color: "var(--accent2)", fontFamily: "var(--font-head)", fontWeight: 600 }}>{file.name}</div>
                                        <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 4 }}>
                                            {(file.size / 1024).toFixed(1)} KB · Click to replace
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <>
                                    {/* Icon when empty */}
                                    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                                        <rect x="6" y="4" width="18" height="24" rx="2" stroke="var(--muted)" strokeWidth="1.5" />
                                        <path d="M24 4l6 6v14" stroke="var(--muted)" strokeWidth="1.5" />
                                        <path d="M24 4v6h6" stroke="var(--muted)" strokeWidth="1.5" />
                                        <path d="M18 30v-8M14 26l4-4 4 4" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
                                    </svg>
                                    <div style={{ textAlign: "center" }}>
                                        <div style={{ fontFamily: "var(--font-head)", fontWeight: 600 }}>Drop your résumé PDF</div>
                                        <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 4 }}>or click to browse · PDF only</div>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* JD textarea */}
                        <textarea
                            value={jd}
                            onChange={(e) => setJd(e.target.value)}
                            placeholder="Paste the job description here..."
                            rows={7}
                            style={{
                                width: "100%",
                                background: "var(--surface)",
                                border: `1.5px solid ${jd.length > 20 ? "var(--border-hi)" : "var(--border)"}`,
                                borderRadius: 10,
                                padding: "14px 16px",
                                color: "var(--text)",
                                fontFamily: "var(--font-mono)",
                                fontSize: 13,
                                outline: "none",
                            }}
                        />

                        <button
                            onClick={handleSubmit}
                            disabled={!canSubmit}
                            style={{
                                padding: "16px 28px",
                                borderRadius: 10,
                                background: canSubmit ? "var(--accent)" : "var(--border)",
                                color: canSubmit ? "#0b0c0f" : "var(--muted)",
                                fontFamily: "var(--font-head)",
                                fontWeight: 700,
                                cursor: canSubmit ? "pointer" : "not-allowed",
                            }}
                        >
                            {canSubmit ? "→ Analyze Resume" : "Upload PDF & paste JD to continue"}
                        </button>
                    </div>
                )}

                {status === "loading" && <ScanningAnimation />}
                {status === "done" && result && (
                    <div>
                        <ResultPanel data={result} />
                        <button onClick={reset}>← Analyze another résumé</button>
                    </div>
                )}
            </div>
        </>
    );
};

export default ResumeScanner;