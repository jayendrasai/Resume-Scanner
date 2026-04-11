import { v4 as uuidv4 } from 'uuid';

export const getGuestId = (): string => {
    let guestId = localStorage.getItem('guest_id');
    if (!guestId) {
        guestId = uuidv4();
        localStorage.setItem('guest_id', guestId);
    }
    return guestId;
};