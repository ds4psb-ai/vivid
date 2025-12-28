"use client";

import { useMemo } from "react";
import { useSession } from "@/hooks/useSession";
import { isAdminModeEnabled } from "@/lib/admin";

export const useAdminAccess = (requireAuth: boolean = true) => {
  const { session, isLoading, error, refresh } = useSession(requireAuth);
  const role = session?.user?.role || null;
  const isAdmin = useMemo(() => isAdminModeEnabled(role), [role]);

  return { session, isLoading, error, refresh, isAdmin };
};
