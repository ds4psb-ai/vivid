/**
 * Centralized animation constants and variants.
 * Use these for consistent timing and easing across the app.
 */

// ============================================
// Timing Constants (in seconds)
// ============================================
export const TIMING = {
    instant: 0.1,
    fast: 0.2,
    normal: 0.3,
    slow: 0.5,
    verySlow: 0.8,
} as const;

// ============================================
// Spring Configurations
// ============================================
export const SPRING = {
    default: { type: 'spring' as const, stiffness: 300, damping: 30 },
    bouncy: { type: 'spring' as const, stiffness: 400, damping: 25 },
    smooth: { type: 'spring' as const, stiffness: 200, damping: 35 },
    gentle: { type: 'spring' as const, stiffness: 120, damping: 20 },
} as const;

// ============================================
// Stagger Delays
// ============================================
export const STAGGER = {
    fast: 0.05,
    normal: 0.1,
    slow: 0.15,
    verySlow: 0.2,
} as const;

// ============================================
// Reusable Variants
// ============================================
export const VARIANTS = {
    // Fade
    fadeIn: {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
    },

    // Slide Up
    slideUp: {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -10 },
    },

    // Slide Down
    slideDown: {
        initial: { opacity: 0, y: -20 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: 10 },
    },

    // Scale
    scale: {
        initial: { opacity: 0, scale: 0.9 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 0.95 },
    },

    // Scale Up (for modals)
    scaleUp: {
        initial: { opacity: 0, scale: 0.8 },
        animate: { opacity: 1, scale: 1 },
        exit: { opacity: 0, scale: 0.9 },
    },

    // Stagger Container
    staggerContainer: {
        animate: {
            transition: { staggerChildren: STAGGER.normal },
        },
    },

    // Stagger Item (use with staggerContainer)
    staggerItem: {
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
    },
} as const;

// ============================================
// Transition Presets
// ============================================
export const TRANSITION = {
    fast: { duration: TIMING.fast, ease: 'easeOut' },
    normal: { duration: TIMING.normal, ease: 'easeOut' },
    slow: { duration: TIMING.slow, ease: 'easeInOut' },
    spring: SPRING.default,
    springBouncy: SPRING.bouncy,
} as const;

// ============================================
// Easing Functions
// ============================================
export const EASING = {
    easeOut: [0.0, 0.0, 0.2, 1],
    easeIn: [0.4, 0.0, 1, 1],
    easeInOut: [0.4, 0.0, 0.2, 1],
    anticipate: [0.36, 0, 0.66, -0.56],
} as const;
