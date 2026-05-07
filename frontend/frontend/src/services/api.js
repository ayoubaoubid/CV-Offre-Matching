import axios from "axios";

export const AUTH_STORAGE_KEY = "auth_tokens";
export const CURRENT_USER_STORAGE_KEY = "current_user";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

API.interceptors.request.use(
  (config) => {
    const rawTokens = localStorage.getItem(AUTH_STORAGE_KEY);
    if (rawTokens) {
      try {
        const tokens = JSON.parse(rawTokens);
        if (tokens?.access) {
          config.headers.Authorization = `Bearer ${tokens.access}`;
        }
      } catch (error) {
        console.warn("Impossible de lire les tokens d'authentification.", error);
      }
    }

    const rawUser = localStorage.getItem(CURRENT_USER_STORAGE_KEY);
    if (rawUser && !config.headers["X-User-Id"]) {
      try {
        const user = JSON.parse(rawUser);
        if (user?.id) {
          config.headers["X-User-Id"] = String(user.id);
        }
      } catch (error) {
        console.warn("Impossible de lire current_user depuis localStorage.", error);
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      localStorage.removeItem(CURRENT_USER_STORAGE_KEY);
    } else if (!error.response) {
      console.error("Erreur reseau: le backend semble injoignable.");
    } else if (error.response.status >= 500) {
      console.error("Erreur serveur cote Django.");
    }
    return Promise.reject(error);
  }
);

export default API;
