

import { v4 as uuidv4 } from 'uuid';

export const getGuestId = (): string => {
    const EXPIRY_TIME = 3 * 60 * 60 * 1000; // 3 hours
    const now = new Date().getTime();

    const stored = localStorage.getItem('guest_id_data');

    if (stored) {
        const { id, expiry } = JSON.parse(stored);
        if (now < expiry) {
            return id;
        }
    }

    const newId = uuidv4();
    const newExpiry = now + EXPIRY_TIME;

    localStorage.setItem(
        'guest_id_data',
        JSON.stringify({ id: newId, expiry: newExpiry })
    );

    return newId;
};

// utils/auth.ts — append below existing getGuestId

const TOKEN_KEY = 'auth_token';

export const saveToken = (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token);
};

export const getToken = (): string | null => {
    return localStorage.getItem(TOKEN_KEY);
};

export const removeToken = (): void => {
    localStorage.removeItem(TOKEN_KEY);
};

export const isAuthenticated = (): boolean => {
    const token = getToken();
    if (!token) return false;
    try {
        // Decode payload — check expiry without a library
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp * 1000 > Date.now();
    } catch {
        return false;
    }
};

export const getTier = (): string | null => {
    const token = getToken();
    if (!token) return null;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.tier ?? null;
    } catch {
        return null;
    }
};