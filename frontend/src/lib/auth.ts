"use client";

import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

/** True when the user holds `permission` through any of their roles. */
export function can(user: User | undefined, permission: string): boolean {
  return !!user?.permissions.includes(permission);
}

/** True for anyone who may see the admin area (holds at least one permission). */
export function isStaff(user: User | undefined): boolean {
  return !!user && user.permissions.length > 0;
}

export function useMe() {
  return useQuery<User, ApiError>({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/auth/me"),
    retry: false,
    staleTime: 60_000,
  });
}
