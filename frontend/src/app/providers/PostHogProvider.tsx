'use client'

import posthog from 'posthog-js'
import { PostHogProvider as PHProvider, usePostHog } from 'posthog-js/react'
import { useEffect } from 'react'

/**
 * PostHog Analytics Provider
 * 
 * Features enabled:
 * - Autocapture (clicks, inputs)
 * - Pageviews
 * - Page leave tracking
 * - Session replay
 * - Debug mode in development
 */
export function PostHogProvider({ children }: { children: React.ReactNode }) {
    useEffect(() => {
        if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_POSTHOG_KEY) {
            posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
                api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com',
                // 2025-11-30 defaults for optimal tracking
                capture_pageview: true,
                capture_pageleave: true,
                // Session replay config
                session_recording: {
                    maskAllInputs: false,
                    maskInputOptions: {
                        password: true,
                    },
                },
                // Debug in development
                loaded: (posthog) => {
                    if (process.env.NODE_ENV === 'development') {
                        posthog.debug()
                    }
                },
            })
        }
    }, [])

    return <PHProvider client={posthog}>{children}</PHProvider>
}

// Re-export hook for easy access
export { usePostHog }
