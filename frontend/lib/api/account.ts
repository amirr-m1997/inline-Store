import { apiRequest } from "./client";

export function getProfile<T>() { return apiRequest<T>("/api/v1/auth/profile/", { cache: "no-store" }); }
export function updateProfile<T>(body: unknown) { return apiRequest<T>("/api/v1/auth/profile/", { method: "PATCH", body }); }
export function getAddresses<T>() { return apiRequest<T>("/api/v1/auth/addresses/", { cache: "no-store" }); }
export function createAddress<T>(body: unknown) { return apiRequest<T>("/api/v1/auth/addresses/", { method: "POST", body }); }
export function deleteAddress(id: number) { return apiRequest<null>(`/api/v1/auth/addresses/${id}/`, { method: "DELETE" }); }
