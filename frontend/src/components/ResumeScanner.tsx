import React, { useState, useRef, useCallback } from "react";
import axios from "axios";
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
            const response = await axios.post<AnalysisData>("/analyze", formData);
            setResult(response.data);
            setStatus("done");
        } catch (err: any) {
            const msg = err.response?.status === 429
                ? "Rate limit reached — try again in a minute."
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
                        {/* Drop Zone Logic */}
                        <div
                            onDrop={handleDrop}
                            onClick={() => fileRef.current?.click()}
                            className="fade-up-2"
                            style={{ /* ... your existing drop zone styles ... */ }}
                        >
                            <input ref={fileRef} type="file" accept=".pdf" style={{ display: "none" }}
                                onChange={(e) => setFile(e.target.files?.[0] || null)} />
                            {/* ... file status JSX ... */}
                        </div>

                        <textarea
                            value={jd}
                            onChange={(e) => setJd(e.target.value)}
                            style={{ /* ... your existing textarea styles ... */ }}
                        />

                        <button onClick={handleSubmit} disabled={!canSubmit} style={{ /* ... styles ... */ }}>
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