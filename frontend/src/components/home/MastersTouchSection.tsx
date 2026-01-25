"use client";

/**
 * Masters Touch Section - Stitch V2 Neon Red Design
 *
 * 2x2 grid of legendary director style cards
 * Deep charcoal theme with image backgrounds
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

export interface Director {
  id: string;
  name: string;
  imageUrl: string;
  tags: string[];
}

interface MastersTouchProps {
  directors?: Director[];
  onDirectorClick?: (id: string) => void;
}

// Default director data matching stitch_ui_1 design
const DEFAULT_DIRECTORS: Director[] = [
  {
    id: "bong",
    name: "봉준호",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCHBkCVLu4gK7o35kot3bwTgivm14nWF98-E0-SoeOg8WkLKDk0CBxOoqnjtTKUy682LFG8PBbgTg0KQp2pY9zCZDJFgB-8Ef8t_sNTfupaRNqzvCWOE_nkO1QMIh6KlVBB-lYvcoeo1stW7xD5uqnhwXeaFAEXdD9S8p_YKN43bOtweZKv1sUheFQtQwLnA8zxunJv-J5odTRTPqiM1UPEHSMn9RExOtAeLp_sCMqDz00ro8jPXUVWeEa_axlWwyYfsd5p1GqjWpg",
    tags: ["사회 풍자", "장르 변주"],
  },
  {
    id: "nolan",
    name: "크리스토퍼 놀란",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuA8YO4HXXbuj0LnXEoM2M5bwlM_jBPp-pWIweJWYz5_JZi6_i_2BZF4foIbtnc_1WKH3DrvElM1JjhllluvdFjirGpbWwxJnMXfhK_fgFNl5Nt3BoZxfKL5wzo5n-pXFU8xXUsBskYR-5_kWaVp_iFdPJQUjhOkUqUIqPLwtRQQNJ-89krp9Ebk1LzR7CdJcu9nsJLGm8CQJdTAGKhvs7Prj0XSTrlJA56P2UiZZQs1TtuJvUOs9Es_jw5bn9-NnPwwMwN3vXAxfUs",
    tags: ["IMAX 스케일", "비선형 시간"],
  },
  {
    id: "villeneuve",
    name: "드니 빌뇌브",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuBx4IrQIbEnZnKNonjTXDNu-7soh4DLurYYtCdUzwvRFkQfgDpSx-Q-VS834w9guA5-WwfQx0espNjionrOFYqw5neVSqGRJL2vDKzKlB75yKY6B96J6edssQt4v25XrPMI0cTyb7JjNHjQJatCnFaP4_63xniMG6zFaaHInK0otHAQ81vrHp98msB6Cdhh4kY233-aXb7-m-sILfOnxNqJSN-AEx5oBb95WDIyrK63ANULbPATwOIilX5I7WeXedmoDlh4dzmXy3Q",
    tags: ["압도적 비주얼", "철학적 SF"],
  },
  {
    id: "wong",
    name: "왕가위",
    imageUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAO2vYTJ8rgb3wxJ6AlhglSanKMSt8jzWltA3EMRpBesvIXjmmMyBmC6ZJIynsFDjyCKh4L8rvhHPrWSRzAWPdAM4nddWMdD4Y7SnmCC1HVLWGy_sxbysuOb1IyFvSQrDTn4gRrgPFP5jUkL47wnN7jJRTjbSB4qiZOm_0z5ZI9z2h_-MFIeBc9WZIW6EX5mINSv58T-tNJ0adxtFgeIbW52YPRhGUFOBvZmSOfmEas-jCzzRu7XmPB0NPbI79BVdpNomAClpUMHbA",
    tags: ["네온 색감", "스텝 프린팅"],
  },
];

export function MastersTouchSection({
  directors = DEFAULT_DIRECTORS,
  onDirectorClick,
}: MastersTouchProps) {
  return (
    <section className="relative z-20 px-6 md:px-16 py-24 bg-[#050505]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-10 border-l-4 border-[#FF003C] pl-6">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white mb-2">
            거장의 <span className="text-gray-500">터치</span>
          </h2>
          <p className="text-gray-400 text-sm max-w-xl">
            전설적인 감독들의 시그니처 스타일을 AI로 재현하여 당신의 스토리에 깊이를 더하세요.
          </p>
        </div>

        {/* Directors Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {directors.map((director, index) => (
            <motion.div
              key={director.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="group relative h-64 md:h-80 rounded-2xl overflow-hidden cursor-pointer"
              onClick={() => onDirectorClick?.(director.id)}
            >
              {/* Background Image */}
              <img
                alt={director.name}
                className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 filter brightness-75 group-hover:brightness-100"
                src={director.imageUrl}
              />

              {/* Gradient Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />

              {/* Content */}
              <div className="absolute bottom-0 left-0 p-8 w-full">
                <h3 className="text-2xl md:text-3xl font-bold text-white mb-3">
                  {director.name}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {director.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 rounded-full text-xs text-gray-200"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Hover Arrow */}
              <div className="absolute top-6 right-6 w-8 h-8 rounded-full border border-white/30 flex items-center justify-center bg-black/30 backdrop-blur opacity-0 group-hover:opacity-100 transition-opacity">
                <ArrowUpRight className="w-4 h-4 text-white" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default MastersTouchSection;
