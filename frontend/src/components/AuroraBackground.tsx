"use client";

import { useEffect, useRef, useCallback } from "react";

// Simple throttle implementation
function throttle<T extends (...args: Parameters<T>) => void>(
    fn: T,
    delay: number
): (...args: Parameters<T>) => void {
    let lastCall = 0;
    return (...args: Parameters<T>) => {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            fn(...args);
        }
    };
}

export function AuroraBackground() {
    const containerRef = useRef<HTMLDivElement>(null);

    // Mouse move effect with throttle (50ms = 20fps, enough for smooth effect)
    useEffect(() => {
        const handleMouseMove = throttle((e: MouseEvent) => {
            if (!containerRef.current) return;
            const { clientX, clientY } = e;
            const { innerWidth, innerHeight } = window;

            const x = (clientX / innerWidth) * 100;
            const y = (clientY / innerHeight) * 100;

            containerRef.current.style.setProperty("--mouse-x", `${x}%`);
            containerRef.current.style.setProperty("--mouse-y", `${y}%`);
        }, 50);

        window.addEventListener("mousemove", handleMouseMove);
        return () => window.removeEventListener("mousemove", handleMouseMove);
    }, []);

    return (
        <div
            ref={containerRef}
            className="fixed inset-0 z-[-1] overflow-hidden bg-black pointer-events-none"
            aria-hidden="true"
        >
            {/* Deep Space Base */}
            <div className="absolute inset-0 bg-[#000000] opacity-100" />

            {/* Aurora Orbs - Optimized blur values for GPU performance */}
            {/* Orb 1: Lusion Blue/Purple - Top Left */}
            <div className="absolute -top-[20%] -left-[10%] w-[60vw] h-[60vw] 
        bg-[radial-gradient(circle_at_center,var(--lusion-dark-blue)_0%,transparent_70%)] 
        opacity-40 blur-[60px] animate-aurora-drift-slow mix-blend-screen"
            />

            {/* Orb 2: Lusion Violet - Center/Right Bottom */}
            <div className="absolute top-[30%] right-[0%] w-[50vw] h-[50vw] 
        bg-[radial-gradient(circle_at_center,var(--lusion-purple)_0%,transparent_70%)] 
        opacity-30 blur-[60px] animate-aurora-drift-medium mix-blend-screen"
                style={{ animationDelay: "-5s" }}
            />

            {/* Orb 3: Lusion Green/Blue - Interactive Mouse Follower */}
            <div
                className="absolute w-[40vw] h-[40vw] 
        bg-[radial-gradient(circle_at_center,rgba(26,47,251,0.3)_0%,transparent_70%)] 
        opacity-40 blur-[50px] transition-transform duration-[1500ms] ease-out mix-blend-screen"
                style={{
                    left: "var(--mouse-x, 50%)",
                    top: "var(--mouse-y, 50%)",
                    transform: "translate(-50%, -50%)",
                    willChange: "left, top"
                }}
            />

            {/* Noise Overlay for Texture - disabled (file not found) */}
            {/* <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay" /> */}

            {/* Vignette */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,#000000_100%)] opacity-80" />
        </div>
    );
}
