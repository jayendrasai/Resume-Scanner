// import { v4 as uuidv4 } from 'uuid';

// export const getGuestId = (): string => {
//     let guestId = localStorage.getItem('guest_id');
//     if (!guestId) {
//         guestId = uuidv4();
//         localStorage.setItem('guest_id', guestId);
//     }
//     return guestId;
// };

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