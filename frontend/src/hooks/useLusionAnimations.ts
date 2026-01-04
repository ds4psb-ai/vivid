"use client";

import { useEffect, useRef, useCallback } from "react";

/**
 * Lusion-style Animation Hooks
 * Based on lusion.co design patterns
 */

// ─── Parallax Scroll Hook ───
export function useParallaxScroll() {
    useEffect(() => {
        const handleScroll = () => {
            const scrollY = window.scrollY;
            document.documentElement.style.setProperty("--scroll-y", `${scrollY}px`);
        };

        window.addEventListener("scroll", handleScroll, { passive: true });
        handleScroll(); // Initial call

        return () => window.removeEventListener("scroll", handleScroll);
    }, []);
}

// ─── Smooth Scroll with Inertia (Lenis-like) ───
interface LenisOptions {
    duration?: number;
    easing?: (t: number) => number;
    smoothWheel?: boolean;
}

export function useSmoothScroll(options: LenisOptions = {}) {
    const {
        duration = 1.2,
        easing = (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        smoothWheel = true
    } = options;

    useEffect(() => {
        if (!smoothWheel) return;

        let targetScroll = window.scrollY;
        let currentScroll = window.scrollY;
        let animationId: number | null = null;

        const handleWheel = (e: WheelEvent) => {
            e.preventDefault();
            targetScroll = Math.max(0, targetScroll + e.deltaY);
            targetScroll = Math.min(
                document.documentElement.scrollHeight - window.innerHeight,
                targetScroll
            );
        };

        const animate = () => {
            const diff = targetScroll - currentScroll;
            currentScroll += diff * (1 / (duration * 60));

            if (Math.abs(diff) > 0.1) {
                window.scrollTo(0, currentScroll);
                animationId = requestAnimationFrame(animate);
            } else {
                window.scrollTo(0, targetScroll);
            }
        };

        const startAnimation = () => {
            if (!animationId) {
                animationId = requestAnimationFrame(animate);
            }
        };

        document.addEventListener("wheel", handleWheel, { passive: false });
        window.addEventListener("wheel", startAnimation, { passive: true });

        // Add lenis class for CSS compatibility
        document.documentElement.classList.add("lenis", "lenis-smooth");

        return () => {
            document.removeEventListener("wheel", handleWheel);
            window.removeEventListener("wheel", startAnimation);
            document.documentElement.classList.remove("lenis", "lenis-smooth");
            if (animationId) cancelAnimationFrame(animationId);
        };
    }, [duration, smoothWheel]);
}

// ─── Staggered Reveal on Scroll (Intersection Observer) ───
export function useStaggerReveal(containerRef: React.RefObject<HTMLElement | null>) {
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const staggerItems = container.querySelectorAll("[data-stagger]");

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry, index) => {
                    if (entry.isIntersecting) {
                        const element = entry.target as HTMLElement;
                        const delay = (element.dataset.staggerDelay
                            ? parseFloat(element.dataset.staggerDelay)
                            : index * 0.1);

                        setTimeout(() => {
                            element.classList.add("is-revealed");
                        }, delay * 1000);

                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: "0px 0px -50px 0px"
            }
        );

        staggerItems.forEach((item) => observer.observe(item));

        return () => observer.disconnect();
    }, [containerRef]);
}

// ─── Magnetic Button Effect ───
export function useMagneticButton(ref: React.RefObject<HTMLElement | null>) {
    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        const handleMouseMove = (e: MouseEvent) => {
            const rect = element.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;

            const deltaX = (e.clientX - centerX) * 0.2;
            const deltaY = (e.clientY - centerY) * 0.2;

            element.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
        };

        const handleMouseLeave = () => {
            element.style.transform = "translate(0, 0)";
            element.style.transition = "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)";
        };

        const handleMouseEnter = () => {
            element.style.transition = "transform 0.1s ease-out";
        };

        element.addEventListener("mousemove", handleMouseMove);
        element.addEventListener("mouseleave", handleMouseLeave);
        element.addEventListener("mouseenter", handleMouseEnter);

        return () => {
            element.removeEventListener("mousemove", handleMouseMove);
            element.removeEventListener("mouseleave", handleMouseLeave);
            element.removeEventListener("mouseenter", handleMouseEnter);
        };
    }, [ref]);
}

// ─── Combined Lusion Animations Hook ───
export function useLusionAnimations(options?: {
    parallax?: boolean;
    smoothScroll?: boolean;
    smoothScrollDuration?: number;
}) {
    const {
        parallax = true,
        smoothScroll = false, // Disabled by default (can cause issues)
        smoothScrollDuration = 1.2
    } = options || {};

    // Parallax
    useEffect(() => {
        if (!parallax) return;

        const handleScroll = () => {
            document.documentElement.style.setProperty(
                "--scroll-y",
                `${window.scrollY}px`
            );
        };

        window.addEventListener("scroll", handleScroll, { passive: true });
        handleScroll();

        return () => window.removeEventListener("scroll", handleScroll);
    }, [parallax]);

    // Note: Smooth scroll is opt-in due to potential UX issues
    useSmoothScroll({
        smoothWheel: smoothScroll,
        duration: smoothScrollDuration
    });
}

export default useLusionAnimations;
