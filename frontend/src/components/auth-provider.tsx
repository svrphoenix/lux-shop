"use client";

import {
  clearSession,
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
    window.addEventListener("hop-and-barley-auth-changed", handleAuthChanged);
    return () => window.removeEventListener("hop-and-barley-auth-changed", handleAuthChanged);
  }, []);

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
