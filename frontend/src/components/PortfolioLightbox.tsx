"use client";

import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { X } from "lucide-react";

interface PortfolioLightboxProps {
    isOpen: boolean;
    onClose: () => void;
    item: {
        img: string;
        tag: string;
        title: string;
        desc: string;
    } | null;
}

export default function PortfolioLightbox({ isOpen, onClose, item }: PortfolioLightboxProps) {
    if (!item) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 z-[60] bg-black/90 backdrop-blur-md"
                    />

                    {/* Lightbox Content */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed inset-4 z-[70] flex items-center justify-center md:inset-8 lg:inset-16"
                    >
                        <div className="relative w-full max-w-5xl overflow-hidden rounded-2xl bg-[#0a0a0c] shadow-2xl">
                            {/* Close Button */}
                            <button
                                onClick={onClose}
                                className="absolute right-4 top-4 z-10 rounded-full bg-black/50 p-2 text-white backdrop-blur-sm transition-colors hover:bg-black/70"
                                aria-label="닫기"
                            >
                                <X className="h-6 w-6" />
                            </button>

                            {/* Image */}
                            <div className="relative aspect-video w-full">
                                <Image
                                    src={item.img}
                                    alt={item.title}
                                    fill
                                    className="object-cover"
                                    priority
                                />
                                {/* Gradient Overlay */}
                                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#0a0a0c] via-[#0a0a0c]/50 to-transparent p-8 pt-20">
                                    <span className="inline-block rounded bg-[#4200FF] px-2 py-1 text-xs font-bold uppercase tracking-wider text-white">
                                        {item.tag}
                                    </span>
                                    <h2 className="mt-3 text-3xl font-bold text-white">{item.title}</h2>
                                    <p className="mt-2 text-lg text-slate-300">{item.desc}</p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
