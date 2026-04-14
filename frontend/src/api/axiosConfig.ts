import axios from 'axios';
import { getGuestId } from '../utils/auth';

//for docker running locally
// const BASE = import.meta.env.VITE_API_URL;


const BASE = import.meta.env.DEV
    ? import.meta.env.VITE_API_URL
    : "";
// console.log("BASE: ", BASE);
const api = axios.create({
    baseURL: BASE,
    headers: {
        'Content-Type': 'multipart/form-data',
        'X-Guest-ID': getGuestId(),
    },
});


api.interceptors.request.use((config) => {
    config.headers['X-Guest-ID'] = getGuestId();

    // console.log("UUID: ", getGuestId());
    return config;
});

export default api;