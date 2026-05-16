export interface AnalysisResponse {
    match_score: number;
    missing_keywords: string[];
    tips: string[];
}

export interface AnalysisError {
    error: string;
}

export interface AnalysisData {
    match_score: number;
    missing_keywords: string[];
    tips: string[];
}
export interface HistoryRecord {
    filename: string;
    timestamp: string;
    ip?: string;
}
export type Status = "idle" | "loading" | "done" | "error";


// types/index.ts — append below existing types

// ── Video analysis types ───────────────────────────────────────────────────

export interface FillerWords {
    um: number;
    uh: number;
    like: number;
    'you know': number;
    so: number;
}

export interface VideoAnalysis {
    filler_words: FillerWords;
    pace_wpm: number;
    clarity_score: number;
    tips: string[];
}

export interface JobResult {
    transcript: string;
    duration_seconds: number;
    analysis: VideoAnalysis;
}

export interface JobStatusResponse {
    task_id: string;
    status: 'pending' | 'processing' | 'completed' | 'failed' | 'retrying';
    result: JobResult | { error: string } | null;
}

export interface PresignResponse {
    upload_url: string;
    object_key: string;
    expires_in: number;
    max_bytes: number;
}

export type VideoPageStatus =
    | 'idle'
    | 'uploading'       // PUT to S3 in progress
    | 'queued'          // task_id received, polling not started
    | 'processing'      // worker picked up task
    | 'completed'
    | 'failed';

// ── Auth types ─────────────────────────────────────────────────────────────

export interface AuthTokenResponse {
    access_token: string;
    token_type: string;
}

export interface UserProfile {
    id: number;
    email: string;
    tier: 'free' | 'premium';
    premium_expires_at: string | null;
}