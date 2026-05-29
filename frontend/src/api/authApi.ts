import axios from 'axios';
import { getToken } from '../utils/auth';

const authApi = axios.create({
    baseURL: import.meta.env.DEV ? import.meta.env.VITE_API_URL ?? '' : '',
});

authApi.interceptors.request.use((config) => {
    const token = getToken();
    if (token) config.headers['Authorization'] = `Bearer ${token}`;
    return config;
});

// ── Auth ───────────────────────────────────────────────────────────────────

export const register = async (email: string, password: string): Promise<string> => {
    const res = await authApi.post<{ access_token: string }>('/v1/auth/register', {
        email, password
    });
    return res.data.access_token;
};

export const login = async (email: string, password: string): Promise<string> => {
    const res = await authApi.post<{ access_token: string }>('/v1/auth/login', {
        email, password
    });
    return res.data.access_token;
};

export const refreshToken = async (): Promise<string> => {
    const res = await authApi.post<{ access_token: string }>('/v1/auth/refresh');
    return res.data.access_token;
};

export interface UserProfile {
    id: number;
    email: string;
    tier: 'free' | 'premium';
    premium_expires_at: string | null;
}

export const getMe = async (): Promise<UserProfile> => {
    const res = await authApi.get<UserProfile>('/v1/auth/me');
    return res.data;
};

// ── Billing ────────────────────────────────────────────────────────────────

export interface OrderResponse {
    order_id: string;
    amount_inr_paise: number;
    currency: string;
    key_id: string;
}

export interface PassStatus {
    tier: string;
    premium_expires_at: string | null;
    razorpay_order_id: string | null;
}

export const createOrder = async (): Promise<OrderResponse> => {
    const res = await authApi.post<OrderResponse>('/v1/billing/create-order');
    return res.data;
};

export const getBillingStatus = async (): Promise<PassStatus> => {
    const res = await authApi.get<PassStatus>('/v1/billing/status');
    return res.data;
};