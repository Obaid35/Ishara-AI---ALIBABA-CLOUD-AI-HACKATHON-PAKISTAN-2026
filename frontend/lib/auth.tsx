"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { get, getRefreshToken, post, setTokens } from "./api";
import type { User } from "./types";

interface AuthValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<User>;
  signOut: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthValue>({
  user: null,
  loading: true,
  signIn: async () => {
    throw new Error("AuthProvider missing");
  },
  signOut: async () => {},
  refresh: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setUser(await get<User>("/api/auth/me"));
    } catch {
      // Try the refresh token before giving up — an expired access token is
      // normal, a revoked session is not.
      const token = getRefreshToken();
      if (!token) {
        setUser(null);
        setTokens(null, null);
        return;
      }
      try {
        const data = await post<{ access_token: string; user: User }>(
          "/api/auth/refresh",
          { refresh_token: token },
          false,
        );
        setTokens(data.access_token);
        setUser(data.user);
      } catch {
        setUser(null);
        setTokens(null, null);
      }
    }
  }, []);

  useEffect(() => {
    void refresh().finally(() => setLoading(false));
  }, [refresh]);

  const signIn = useCallback(async (email: string, password: string) => {
    const data = await post<{ access_token: string; refresh_token: string; user: User }>(
      "/api/auth/login",
      { email, password },
      false,
    );
    setTokens(data.access_token, data.refresh_token);
    setUser(data.user);
    return data.user;
  }, []);

  const signOut = useCallback(async () => {
    const token = getRefreshToken();
    try {
      if (token) await post("/api/auth/logout", { refresh_token: token });
    } catch {
      // Signing out locally must succeed even if the server call fails.
    }
    setTokens(null, null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signOut, refresh }),
    [user, loading, signIn, signOut, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
