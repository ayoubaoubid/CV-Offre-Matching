import { createContext, useEffect, useState } from "react";

import { fetchCurrentUser } from "../services/authService";
import { AUTH_STORAGE_KEY, CURRENT_USER_STORAGE_KEY } from "../services/api";


export const AuthContext = createContext();


export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const rawUser = localStorage.getItem(CURRENT_USER_STORAGE_KEY);
    if (!rawUser) {
      return null;
    }

    try {
      return JSON.parse(rawUser);
    } catch {
      localStorage.removeItem(CURRENT_USER_STORAGE_KEY);
      return null;
    }
  });

  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const refreshUser = async () => {
      if (!localStorage.getItem(AUTH_STORAGE_KEY)) {
        if (isMounted) {
          setAuthReady(true);
        }
        return;
      }

      try {
        const response = await fetchCurrentUser();
        if (!isMounted) {
          return;
        }
        setUser(response.data.user);
        localStorage.setItem(CURRENT_USER_STORAGE_KEY, JSON.stringify(response.data.user));
      } catch {
        if (!isMounted) {
          return;
        }
        setUser(null);
        localStorage.removeItem(CURRENT_USER_STORAGE_KEY);
        localStorage.removeItem(AUTH_STORAGE_KEY);
      } finally {
        if (isMounted) {
          setAuthReady(true);
        }
      }
    };

    refreshUser();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = (payload) => {
    const nextUser = payload?.user ?? payload;
    const nextTokens = payload?.tokens ?? null;

    setUser(nextUser);
    localStorage.setItem(CURRENT_USER_STORAGE_KEY, JSON.stringify(nextUser));
    if (nextTokens) {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextTokens));
    }
  };

  const updateUser = (nextUser) => {
    setUser(nextUser);
    localStorage.setItem(CURRENT_USER_STORAGE_KEY, JSON.stringify(nextUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem(CURRENT_USER_STORAGE_KEY);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  return (
    <AuthContext.Provider value={{ authReady, user, login, updateUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
