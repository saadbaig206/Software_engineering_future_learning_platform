"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { AuthTokens, User, UserRole } from "../lib/types";
import { getUserProfile, loginUser as apiLoginUser } from "../lib/api";

export interface AccessibilitySettings {
  contrastMode: "normal" | "high";
  fontSize: "normal" | "large" | "xlarge";
  reduceMotion: boolean;
  autoCaptions: boolean;
}

interface AuthContextType {
  user: User | null;
  tokens: { access: string; refresh: string } | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  a11y: AccessibilitySettings;
  updateA11y: (settings: Partial<AccessibilitySettings>) => void;
}

const defaultA11y: AccessibilitySettings = {
  contrastMode: "normal",
  fontSize: "normal",
  reduceMotion: false,
  autoCaptions: true,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<{ access: string; refresh: string } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [a11y, setA11y] = useState<AccessibilitySettings>(defaultA11y);

  // Initialize auth & accessibility from localStorage
  useEffect(() => {
    if (typeof window === "undefined") return;

    // Load accessibility settings
    try {
      const savedA11y = localStorage.getItem("fl_a11y_settings");
      if (savedA11y) {
        const parsed = JSON.parse(savedA11y);
        setA11y(parsed);
        applyA11yToDOM(parsed);
      }
    } catch (e) {
      console.warn("Failed to load accessibility preferences", e);
    }

    // Load auth tokens
    const access = localStorage.getItem("fl_access_token");
    const refresh = localStorage.getItem("fl_refresh_token");
    if (access && refresh) {
      setTokens({ access, refresh });
      getUserProfile()
        .then((profile) => setUser(profile))
        .catch(() => {
          localStorage.removeItem("fl_access_token");
          localStorage.removeItem("fl_refresh_token");
          setTokens(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const applyA11yToDOM = (settings: AccessibilitySettings) => {
    const root = document.documentElement;
    root.setAttribute("data-contrast", settings.contrastMode);
    root.setAttribute("data-font-size", settings.fontSize);
    root.setAttribute("data-reduce-motion", String(settings.reduceMotion));
  };

  const updateA11y = (newSettings: Partial<AccessibilitySettings>) => {
    setA11y((prev) => {
      const updated = { ...prev, ...newSettings };
      if (typeof window !== "undefined") {
        localStorage.setItem("fl_a11y_settings", JSON.stringify(updated));
        applyA11yToDOM(updated);
      }
      return updated;
    });
  };

  const login = async (email: string, password: string) => {
    const data = await apiLoginUser({ email, password });
    localStorage.setItem("fl_access_token", data.access);
    localStorage.setItem("fl_refresh_token", data.refresh);
    setTokens({ access: data.access, refresh: data.refresh });
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("fl_access_token");
    localStorage.removeItem("fl_refresh_token");
    setTokens(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const profile = await getUserProfile();
      setUser(profile);
    } catch (e) {
      console.error("Failed to refresh user profile", e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tokens,
        isLoading,
        login,
        logout,
        refreshUser,
        a11y,
        updateA11y,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
