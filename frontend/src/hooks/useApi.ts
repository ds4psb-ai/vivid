/**
 * useApi Hook
 * 
 * React hook for data fetching with:
 * - Loading state
 * - Error handling
 * - Auto-refetch
 * - Type safety
 */

import { useState, useEffect, useCallback } from "react";
import { api, ApiError } from "@/lib/api-client";

export interface UseApiOptions {
    /** Skip initial fetch */
    skip?: boolean;
    /** Dependencies that trigger refetch */
    deps?: any[];
}

export interface UseApiResult<T> {
    data: T | null;
    loading: boolean;
    error: ApiError | null;
    refetch: () => Promise<void>;
}

/**
 * Data fetching hook
 * 
 * @example
 * const { data, loading, error, refetch } = useApi<User[]>("/api/v1/users");
 */
export function useApi<T>(
    endpoint: string,
    options: UseApiOptions = {}
): UseApiResult<T> {
    const { skip = false, deps = [] } = options;

    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(!skip);
    const [error, setError] = useState<ApiError | null>(null);

    const fetchData = useCallback(async () => {
        if (skip) return;

        setLoading(true);
        setError(null);

        const result = await api.get<T>(endpoint);

        if (result.ok) {
            setData(result.data);
        } else {
            setError(result.error);
        }

        setLoading(false);
    }, [endpoint, skip]);

    useEffect(() => {
        fetchData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [fetchData, ...deps]);

    return { data, loading, error, refetch: fetchData };
}

/**
 * Mutation hook for POST/PUT/DELETE
 * 
 * @example
 * const { mutate, loading, error } = useMutation<Response>("/api/v1/users", "POST");
 * await mutate({ name: "John" });
 */
export function useMutation<T, B = any>(
    endpoint: string,
    method: "POST" | "PUT" | "DELETE" = "POST"
) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<ApiError | null>(null);

    const mutate = useCallback(
        async (body?: B): Promise<T | null> => {
            setLoading(true);
            setError(null);

            let result;
            switch (method) {
                case "POST":
                    result = await api.post<T>(endpoint, body);
                    break;
                case "PUT":
                    result = await api.put<T>(endpoint, body);
                    break;
                case "DELETE":
                    result = await api.delete<T>(endpoint);
                    break;
            }

            setLoading(false);

            if (result.ok) {
                return result.data;
            } else {
                setError(result.error);
                return null;
            }
        },
        [endpoint, method]
    );

    return { mutate, loading, error };
}

export default useApi;
