"use client";

import {
  clearSession,
  getCurrentUser,
  getStoredUser,
  login as requestLogin,
  register as requestRegister,
  saveUser,
} from "@/lib/client-api";
import type { User } from "@/lib/types";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import Link from "next/link";

type Credentials = { username: string; password: string };
type Registration = Credentials & {
  email: string;
  first_name: string;
  last_name: string;
  password_confirm: string;
};

type AuthContextValue = {
  user: User | null;
  isReady: boolean;
  login: (credentials: Credentials) => Promise<void>;
  register: (data: Registration) => Promise<void>;
  updateUser: (user: User) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [sessionNotice, setSessionNotice] = useState<string | null>(null);
  const lastUserRefresh = useRef(0);
  const userRefreshInProgress = useRef(false);

  const refreshUser = useCallback(async (force = false) => {
    if (!getStoredUser()) {
      return;
    }
    if (
      userRefreshInProgress.current ||
      (!force && Date.now() - lastUserRefresh.current < 30 * 60 * 1000)
    ) {
      return;
    }

    userRefreshInProgress.current = true;
    try {
      const refreshedUser = await getCurrentUser();
      saveUser(refreshedUser);
      setUser(refreshedUser);
      lastUserRefresh.current = Date.now();
    } catch (error) {
      console.error("Unable to refresh the current user profile.", error);
    } finally {
      userRefreshInProgress.current = false;
    }
  }, []);

  useEffect(() => {
    const syncUser = () => {
      setUser(getStoredUser());
      setIsReady(true);
    };
    const handleAuthChanged = (event: Event) => {
      syncUser();
      if (event instanceof CustomEvent) {
        const message = event.detail?.message;
        setSessionNotice(typeof message === "string" ? message : null);
      }
    };
    syncUser();
    const initialRefresh = window.setTimeout(() => {
      void refreshUser(true);
    }, 0);
    window.addEventListener("hop-and-barley-auth-changed", handleAuthChanged);
    const refreshOnReturn = () => {
      if (document.visibilityState === "visible") {
        void refreshUser();
      }
    };
    const refreshInterval = window.setInterval(() => {
      void refreshUser();
    }, 30 * 60 * 1000);
    window.addEventListener("focus", refreshOnReturn);
    document.addEventListener("visibilitychange", refreshOnReturn);
    return () => {
      window.removeEventListener("hop-and-barley-auth-changed", handleAuthChanged);
      window.removeEventListener("focus", refreshOnReturn);
      document.removeEventListener("visibilitychange", refreshOnReturn);
      window.clearTimeout(initialRefresh);
      window.clearInterval(refreshInterval);
    };
  }, [refreshUser]);

  const login = useCallback(async (credentials: Credentials) => {
    setUser(await requestLogin(credentials.username, credentials.password));
  }, []);
  const register = useCallback(async (data: Registration) => {
    setUser(await requestRegister(data));
  }, []);
  const updateUser = useCallback((updatedUser: User) => {
    saveUser(updatedUser);
    setUser(updatedUser);
  }, []);
  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, isReady, login, register, updateUser, logout }),
    [isReady, login, logout, register, updateUser, user],
  );
  return (
    <AuthContext.Provider value={value}>
      {sessionNotice ? (
        <div className="session-notice" role="status">
          <span>{sessionNotice}</span>
          <Link href="/login">Sign in</Link>
          <button
            aria-label="Dismiss session message"
            onClick={() => setSessionNotice(null)}
            type="button"
          >
            ×
          </button>
        </div>
      ) : null}
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}
