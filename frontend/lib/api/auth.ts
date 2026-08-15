import { apiRequest } from "./client";

export type CurrentUser = { id: number; first_name: string; last_name: string; email: string | null; phone_number: string | null };

export function currentUser(signal?: AbortSignal) {
  return apiRequest<CurrentUser>("/api/v1/auth/profile/", { cache: "no-store", signal });
}

export function logout() {
  return apiRequest<null>("/api/v1/auth/logout/", { method: "POST" });
}

export function login(body: unknown) { return apiRequest<unknown>("/api/v1/auth/login/", { method: "POST", body }); }
export function register(body: unknown) { return apiRequest<unknown>("/api/v1/auth/register/", { method: "POST", body }); }
export function googleSignIn(credential: string) { return apiRequest<unknown>("/api/v1/auth/google/", { method: "POST", body: { credential } }); }
export function requestOtp(body: unknown) { return apiRequest<unknown>("/api/v1/auth/otp/request/", { method: "POST", body }); }
export function verifyOtp<T = Record<string, unknown>>(body: unknown) { return apiRequest<T>("/api/v1/auth/otp/verify/", { method: "POST", body }); }
export function forgotPassword<T = Record<string, unknown>>(body: unknown) { return apiRequest<T>("/api/v1/auth/password/forgot/", { method: "POST", body }); }
export function resetPassword<T = { detail: string }>(body: unknown) { return apiRequest<T>("/api/v1/auth/password/reset/", { method: "POST", body }); }
export function changePassword<T = { detail: string }>(body: unknown) { return apiRequest<T>("/api/v1/auth/password/change/", { method: "POST", body }); }
export function updateProfile<T>(body: unknown) { return apiRequest<T>("/api/v1/auth/profile/", { method: "PATCH", body }); }
export function getAddresses<T>() { return apiRequest<T>("/api/v1/auth/addresses/", { cache: "no-store" }); }
export function addAddress<T>(body: unknown) { return apiRequest<T>("/api/v1/auth/addresses/", { method: "POST", body }); }
export function removeAddress(id: number) { return apiRequest<null>(`/api/v1/auth/addresses/${id}/`, { method: "DELETE" }); }
