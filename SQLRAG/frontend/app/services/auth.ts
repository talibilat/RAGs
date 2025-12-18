import { User } from "./api";

const KEY_TOKEN = "sqlrag_token";
const KEY_USER = "sqlrag_user";

export function setSession(token: string, user: User) {
    if (typeof window !== "undefined") {
        localStorage.setItem(KEY_TOKEN, token);
        localStorage.setItem(KEY_USER, JSON.stringify(user));
    }
}

export function getSession() {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem(KEY_TOKEN);
        const userStr = localStorage.getItem(KEY_USER);
        if (token && userStr) {
            return { token, user: JSON.parse(userStr) as User };
        }
    }
    return null;
}

export function clearSession() {
    if (typeof window !== "undefined") {
        localStorage.removeItem(KEY_TOKEN);
        localStorage.removeItem(KEY_USER);
    }
}
