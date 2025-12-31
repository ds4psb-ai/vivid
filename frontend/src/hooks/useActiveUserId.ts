"use client";

import { useMemo } from "react";
import { useSession } from "@/hooks/useSession";

/**
 * Returns the authenticated user's ID from session.
 * Returns null if not authenticated - pages should show login prompt.
 */
export const useActiveUserId = () => {
  const { session, isLoading, error, refresh } = useSession(true);
  const userId = useMemo(() => {
    return session?.user?.user_id || null;
  }, [session?.user?.user_id]);

  return { userId, session, isLoading, error, refresh, isAuthenticated: !!userId };
};
