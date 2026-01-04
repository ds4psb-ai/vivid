'use client';

import { motion } from 'framer-motion';

/**
 * Template component for route-level enter animations.
 * Remounts on every navigation, triggering animations.
 */
export default function Template({ children }: { children: React.ReactNode }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{ height: '100%' }}
        >
            {children}
        </motion.div>
    );
}
