'use client';

import { useEffect, useState } from 'react';

/**
 * Hook to detect user's prefers-reduced-motion setting.
 * Use this to conditionally disable or simplify animations
 * for users who prefer reduced motion.
 * 
 * @example
 * ```tsx
 * const reducedMotion = useReducedMotion();
 * 
 * return (
 *   <motion.div
 *     initial={reducedMotion ? false : { opacity: 0 }}
 *     animate={{ opacity: 1 }}
 *   />
 * );
 * ```
 */
export function useReducedMotion(): boolean {
    const [reducedMotion, setReducedMotion] = useState(false);

    useEffect(() => {
        // Check if matchMedia is available (client-side only)
        if (typeof window === 'undefined' || !window.matchMedia) {
            return;
        }

        const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
        setReducedMotion(mql.matches);

        const handler = (e: MediaQueryListEvent) => {
            setReducedMotion(e.matches);
        };

        mql.addEventListener('change', handler);
        return () => mql.removeEventListener('change', handler);
    }, []);

    return reducedMotion;
}

/**
 * Helper to get animation initial state based on reduced motion preference.
 * Returns `false` (no initial animation) if reduced motion is preferred.
 */
export function getInitial<T>(initial: T, reducedMotion: boolean): T | false {
    return reducedMotion ? false : initial;
}
