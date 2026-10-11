"use client";

import { useQuery } from "@tanstack/react-query";

import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";

export function useMe() {
  return useQuery<User, ApiError>({
    queryKey: ["me"],
    queryFn: () => api.get<User>("/auth/me"),
    retry: false,
    staleTime: 60_000,
  });
}
