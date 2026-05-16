import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '../api/videoApi';
import type { JobStatusResponse, VideoPageStatus } from '../types';

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATES = new Set(['completed', 'failed']);

interface UseJobPollerReturn {
    status: VideoPageStatus;
    result: JobStatusResponse['result'];
    error: string | null;
    startPolling: (taskId: string) => void;
    reset: () => void;
}

export const useJobPoller = (): UseJobPollerReturn => {
    const [status, setStatus] = useState<VideoPageStatus>('idle');
    const [result, setResult] = useState<JobStatusResponse['result']>(null);
    const [error, setError] = useState<string | null>(null);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const taskIdRef = useRef<string | null>(null);

    const stopPolling = useCallback(() => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }, []);

    const poll = useCallback(async () => {
        if (!taskIdRef.current) return;
        try {
            const data = await getJobStatus(taskIdRef.current);

            // Map backend status to VideoPageStatus
            if (data.status === 'pending' || data.status === 'retrying') {
                setStatus('processing');
            } else if (data.status === 'processing') {
                setStatus('processing');
            } else if (data.status === 'completed') {
                setStatus('completed');
                setResult(data.result);
                stopPolling();
            } else if (data.status === 'failed') {
                setStatus('failed');
                const errResult = data.result as { error: string } | null;
                setError(errResult?.error ?? 'Analysis failed. Please try again.');
                stopPolling();
            }
        } catch (err: unknown) {
            // Network error during polling — don't fail immediately,
            // let the next poll attempt before giving up
            console.error('[useJobPoller] Poll error:', err);
        }
    }, [stopPolling]);

    const startPolling = useCallback((taskId: string) => {
        stopPolling();
        taskIdRef.current = taskId;
        setStatus('queued');
        setError(null);
        setResult(null);

        // Immediate first poll — don't wait 3s
        poll();
        intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    }, [poll, stopPolling]);

    const reset = useCallback(() => {
        stopPolling();
        taskIdRef.current = null;
        setStatus('idle');
        setResult(null);
        setError(null);
    }, [stopPolling]);

    // Cleanup on unmount
    useEffect(() => {
        return () => stopPolling();
    }, [stopPolling]);

    return { status, result, error, startPolling, reset };
};