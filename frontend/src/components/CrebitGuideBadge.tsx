"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import Image from "next/image";

export function CrebitGuideBadge() {
    const [isHovered, setIsHovered] = useState(false);

    return (
        <div className="fixed bottom-8 right-8 z-50 flex items-center gap-3 pointer-events-auto">
            {/* Tooltip Label */}
            <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{
                    opacity: isHovered ? 1 : 0,
                    x: isHovered ? 0 : 10,
                    scale: isHovered ? 1 : 0.95
                }}
                className="px-4 py-2 rounded-xl bg-black/60 backdrop-blur-md border border-white/10 shadow-lg text-sm text-[var(--lusion-off-white)] font-medium whitespace-nowrap"
            >
                <span className="text-[var(--lusion-green)] mr-2">●</span>
                Crebit Guide Active
            </motion.div>

            {/* Floating Badge */}
            <motion.div
                onHoverStart={() => setIsHovered(true)}
                onHoverEnd={() => setIsHovered(false)}
                whileHover={{ scale: 1.1 }}
                animate={{
                    y: [0, -6, 0]
                }}
                transition={{
                    y: {
                        duration: 4,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }
                }}
                className="relative group cursor-pointer"
            >
                {/* Glow Layer */}
                <div className="absolute inset-0 rounded-full bg-[var(--lusion-blue)] opacity-20 blur-xl group-hover:opacity-40 transition-opacity duration-500" />

                {/* Icon Container - Glassmorphic Circle */}
                <div className="relative h-14 w-14 rounded-full border border-white/10 bg-white/5 backdrop-blur-md shadow-2xl flex items-center justify-center overflow-hidden transition-colors duration-300 group-hover:border-[var(--lusion-green)]/30 group-hover:bg-black/40">
                    {/* Crebit Rabbit Icon - Using Mask for localized color control of the JPEG if needed, but for now just fitting the image cleanly or using blend mode */}
                    <div className="relative h-full w-full bg-black flex items-center justify-center">
                        {/* 
                   Ideally we use a transparent PNG/SVG. 
                   Since we have a JPG (crebit_logo.jpg), we use mix-blend-screen if it's black BG 
                   or just crop it circular. Assuming black background based on poster.
                */}
                        <Image
                            src="/images/crebit_logo.jpg"
                            alt="Crebit Guide"
                            fill
                            sizes="56px"
                            className="object-cover opacity-90 transition-opacity duration-300 group-hover:opacity-100"
                            style={{ mixBlendMode: "screen" }}
                        />
                    </div>
                </div>

                {/* Status Dot */}
                <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-[var(--lusion-green)] border-2 border-black shadow-[0_0_10px_var(--lusion-green)] animate-pulse" />
            </motion.div>
        </div>
    );
}
