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

export type Status = "idle" | "loading" | "done" | "error";