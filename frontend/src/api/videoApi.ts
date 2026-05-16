import axios from 'axios';
import { getToken } from '../utils/auth';
import type {
    PresignResponse,
    JobStatusResponse,
} from '../types';

const MAX_FILE_BYTES = 100 * 1024 * 1024; // 100 MB
const ALLOWED_TYPES = ['video/mp4', 'video/webm', 'video/quicktime'];

// Separate axios instance — always sends JWT, never guest_id
const authApi = axios.create({
    baseURL: import.meta.env.DEV ? import.meta.env.VITE_API_URL : '',
});

authApi.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
});

// ── Validation ─────────────────────────────────────────────────────────────

export const validateVideoFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
        return 'Only .mp4, .webm, and .mov files are accepted.';
    }
    if (file.size > MAX_FILE_BYTES) {
        return `File too large. Maximum size is 100 MB (yours: ${(file.size / 1024 / 1024).toFixed(1)} MB).`;
    }
    return null;
};

// ── Step 1: Get presigned URL ──────────────────────────────────────────────

export const getPresignedUrl = async (filename: string): Promise<PresignResponse> => {
    const res = await authApi.post<PresignResponse>('/upload/presign', { filename });
    return res.data;
};

// ── Step 2: PUT directly to S3 ────────────────────────────────────────────

export const uploadToS3 = async (
    uploadUrl: string,
    file: File,
    onProgress: (percent: number) => void
): Promise<void> => {
    await axios.put(uploadUrl, file, {
        headers: { 'Content-Type': 'video/mp4' },
        onUploadProgress: (event) => {
            if (event.total) {
                onProgress(Math.round((event.loaded / event.total) * 100));
            }
        },
    });
};

// ── Step 3: Confirm upload + enqueue job ──────────────────────────────────

export const confirmUpload = async (objectKey: string): Promise<string> => {
    const res = await authApi.post<{ task_id: string; status: string }>(
        '/upload/confirm',
        { object_key: objectKey }
    );
    return res.data.task_id;
};

// ── Step 4: Poll job status ────────────────────────────────────────────────

export const getJobStatus = async (taskId: string): Promise<JobStatusResponse> => {
    const res = await authApi.get<JobStatusResponse>(`/jobs/${taskId}/status`);
    return res.data;
};

// ── Auth calls ─────────────────────────────────────────────────────────────

export const loginUser = async (
    email: string,
    password: string
): Promise<string> => {
    const res = await authApi.post<{ access_token: string }>(
        '/auth/login',
        { email, password }
    );
    return res.data.access_token;
};

export const registerUser = async (
    email: string,
    password: string
): Promise<string> => {
    const res = await authApi.post<{ access_token: string }>(
        '/auth/register',
        { email, password }
    );
    return res.data.access_token;
};