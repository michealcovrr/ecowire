export interface User {
  user_id: string;
  phone_number: string;
  full_name: string | null;
  kyc_tier: number;
  kyc_status: string;
  active_role: string | null;
  preferred_language: string;
  onboarding_channel: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  error: string | null;
}

export interface SendOtpResponse {
  sent: boolean;
}

export interface VerifyOtpResponse {
  exists: boolean;
  // existing user — full login
  token?: string;
  user?: User;
  squad_account_number?: string | null;
  squad_bank_name?: string | null;
  qr_code?: string | null;
  // new user — proceed to KYC
  temp_token?: string;
}

export interface AuthSuccessResponse {
  token: string;
  user: User;
  squad_account_number: string | null;
  squad_bank_name: string | null;
  qr_code: string | null;
}
