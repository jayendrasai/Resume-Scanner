import axios from 'axios';
import { getGuestId } from '../utils/auth';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Content-Type': 'multipart/form-data',
        'X-Guest-ID': getGuestId(),
    },
});


api.interceptors.request.use((config) => {
    config.headers['X-Guest-ID'] = getGuestId();

    console.log("UUID: ", getGuestId());
    return config;
});

export default api;