"use client";

import { useMemo } from "react";
import { useSession } from "@/hooks/useSession";

export const useActiveUserId = (fallback = "demo-user") => {
  const { session, isLoading, error, refresh } = useSession(true);
  const userId = useMemo(() => {
    return session?.user?.user_id || process.env.NEXT_PUBLIC_USER_ID || fallback;
  }, [session?.user?.user_id, fallback]);

  return { userId, session, isLoading, error, refresh };
};
