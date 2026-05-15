"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/lib/types";

interface AuthStore {
  token: string | null;
  user: User | null;
  squadAccountNumber: string | null;
  squadBankName: string | null;
  qrCode: string | null;
  // transient — used across auth steps (not persisted)
  pendingPhone: string;
  pendingTempToken: string;   // short-lived token after OTP verify, used for /register

  setToken: (token: string) => void;
  setUser: (user: User) => void;
  setSquadAccount: (number: string | null, bank: string | null) => void;
  setQrCode: (qr: string | null) => void;
  setPendingPhone: (phone: string) => void;
  setPendingTempToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      squadAccountNumber: null,
      squadBankName: null,
      qrCode: null,
      pendingPhone: "",
      pendingTempToken: "",

      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      setSquadAccount: (squadAccountNumber, squadBankName) =>
        set({ squadAccountNumber, squadBankName }),
      setQrCode: (qrCode) => set({ qrCode }),
      setPendingPhone: (pendingPhone) => set({ pendingPhone }),
      setPendingTempToken: (pendingTempToken) => set({ pendingTempToken }),

      logout: () =>
        set({
          token: null,
          user: null,
          squadAccountNumber: null,
          squadBankName: null,
          qrCode: null,
          pendingPhone: "",
          pendingTempToken: "",
        }),
    }),
    {
      name: "econet-auth",
      partialize: (s) => ({
        token: s.token,
        user: s.user,
        squadAccountNumber: s.squadAccountNumber,
        squadBankName: s.squadBankName,
        qrCode: s.qrCode,
      }),
    }
  )
);
