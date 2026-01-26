"use client";

/**
 * User AI Cinema & Animation Section
 *
 * Based on stitch_crebit_cinematic_home_page design:
 * - Short films created with next-gen multimodal models
 * - Video cards with duration, category badges
 * - Creator info with views and likes
 */

import { motion } from "framer-motion";
import { Play, Eye, ThumbsUp, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface CinemaCard {
  id: string;
  title: string;
  description: string;
  thumbnailUrl: string;
  duration: string;
  aiModel: string;
  category: string;
  categoryColor: string;
  creator: {
    name: string;
    role: string;
    avatarUrl: string;
  };
  views: string;
  likePercent: number;
}

const CINEMA_CARDS: CinemaCard[] = [
  {
    id: "neon-horizon",
    title: "Neon Horizon",
    description:
      "A lone android wanders through a sleepless city searching for memories of a past life that may never have existed.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuC_e1scUFUTR2NLXpSpe4EJt2tqPDXC8fyV-plg-y5Yd0IkBQCer51Ui582xP0v4Bo0P3BEHYgpdQFqyJt_nouFmytpqwpl74NAr_rYVPtvgxEhR04GrT6CEzaqhqrQYHMIIqit6_862R4ULQmIjY94WmoEpVpt4SrXBMs_owOkDZVp5_lPjzSdKn7WyAof6oiaWCJ-o3gbK02oQHD6HaQZbsmrPjgZriGCmwC4f5dYDeQA-uiKeCmCjnA3_kU7mU0e-lQr8L_I5sD5",
    duration: "3:00",
    aiModel: "Sora AI",
    category: "Short",
    categoryColor: "bg-pink-500",
    creator: {
      name: "Alex Chen",
      role: "Director",
      avatarUrl:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuDosR4Wu2AuHrMHJPg8gIyMtKmO2EHr9PC9B2dChRlx_cVYaccv2vDLOfqPKl-KoYqWWjqdI8jqXKl8pKgvByR6Ob9Co-m3r59pV8dPV6I92kk38JeoPST7JJkjWNclPl-Krwd_YKsI3Xg_xobs-2yrUzR4TZvfy0fuuhbFWiFA-j2OHPtZFHubzO9LAlAlN-RbwEYOkxwcDf55vWF7wdt40ZGpanQY6Pu2RFt4Iwws4wEe2WhWWYs8sZDbnu1EyFtrcJPbzpLhg9XA",
    },
    views: "12.4k",
    likePercent: 98,
  },
  {
    id: "echoes-of-light",
    title: "Echoes of Light",
    description:
      "An abstract visual journey synchronizing AI-generated landscapes with a deep synth-wave soundtrack.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuB-eGJ4MAKZM7yiqnLeAsypwBS-y8hl8piZ9YFUl2rbaE6pXxouwnqWl1nAP0j5OWowrRZCOMxKitXb6hH1_J1lABtlZQ9yJ7u_VkWvzNTv0vB3RxbUQygYDKmSk81PAH-wHdNEh4eFmHtvbWJ5q99Ay-37sjOqaiLQJJQWm3xqLs5fXe8yNak5KC6MKNPt9rq28WFseyq9rgvubW2-lMqSz-Ck2hwXw8y6nA4bx12GT2ZTpKQvY8rZTb-IZG0LygHTkEWkGICbHaaQ",
    duration: "3:42",
    aiModel: "Runway Gen-3",
    category: "Music Video",
    categoryColor: "bg-purple-500",
    creator: {
      name: "Sarah Void",
      role: "Visualist",
      avatarUrl:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuAGbUdJDhKnB18n8tTyMuM9JJNkUo5HRjH9CNYL87ee3p_IW2GzqNKKeyXrGjJQBR8ZYfbWFA3BfFcIM0n7o_gSQKR0hFsOFPfwQ0FVfCSgjst7e-FsmsrHc0ihFVgRcV0CgwLWqcVXF7FeqyOwZ3fkGRVN5F2qkyeKv036YNyeVwePTqPpWDNqWibLZnjf9-EdWYuSxQyoeW5U41Z1Ce-i80y1ufcC91emNFrY7mLZ6digcbq1r4efaKrTJ46zqbCSOWWlLOQ4jPJM",
    },
    views: "8.2k",
    likePercent: 95,
  },
  {
    id: "last-signal",
    title: "The Last Signal",
    description:
      "Deep space explorers intercept a message that changes humanity's understanding of the cosmos.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCXvikCvs3oiB_LvHppoHUX-yM54FDueCL9eHx9eRqYhpuK4ExYKYf3z0lnjj4NzmyxoCz9SjSuh6Ds0iNF8RC5AW6JpkdTp5VJZtvQ-jkG2HXQ5TzAaenbOzoK1HSNKsj1sq9wQcVh1uZ6SqFPpCVZ6k_JCLvBfXYtXTKYe42qsNe935aUVCsZecMCStQHnmF7WiHsEQZW5bs4tmMFjH_LnK-NXBt2_hMUdTgZB1v7R_2ODYueHLtfM9KmksE6OSp-lxA2D9lwXFzA",
    duration: "2:15",
    aiModel: "Pika Art",
    category: "Sci-Fi",
    categoryColor: "bg-blue-500",
    creator: {
      name: "Markus R",
      role: "Editor",
      avatarUrl:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuA0wbsu1KZqcl7B1wGrcsxFAx-c-BL0A34_e5aPDW_3cHmM6jiGf5G-5GfaeS7wIBXiOgb2rtjcYWD02cfrU7CDnyHvvr2PZ_3095lczBG9OwY1zQJdj3cpKgD_RzUi4Gs-C6N6M6j6gRYnGHIPPf6dmuzOlLxBHTQgY9TV_9KeqYnQbkwmh1AISZNK47V9L2TjvORr_YRQVcIJq-uxfwLlQ8DtviF3h4PgwM-APP9qI9U_m7X80nNjf2F0iD7DkNEGbTYCalvIZQ-p",
    },
    views: "5.7k",
    likePercent: 91,
  },
];

export function UserCinemaSection() {
  return (
    <section className="py-20 px-6 md:px-16 bg-[var(--bg-base)]">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex items-end justify-between mb-10 border-b border-white/5 pb-4"
        >
          <div>
            <h3 className="text-2xl md:text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <span className="w-1 h-6 bg-pink-500 rounded-full shadow-[0_0_10px_#EC4899]" />
              User AI Cinema & Animation
            </h3>
            <p className="text-gray-400 text-sm pl-4">
              Short films created with next-gen multimodal models.
            </p>
          </div>
          <a
            href="/singularity"
            className="group text-gray-300 hover:text-pink-400 text-sm font-medium hidden md:flex items-center gap-2 transition-colors"
          >
            View all 12 shorts
            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </a>
        </motion.div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {CINEMA_CARDS.map((card, index) => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group relative rounded-2xl overflow-hidden bg-[var(--surface-1)] border border-white/5 hover:border-pink-500/30 transition-all duration-500 cursor-pointer"
            >
              {/* Thumbnail */}
              <div className="relative aspect-video overflow-hidden">
                {/* Badges */}
                <div className="absolute top-3 left-3 z-10 flex gap-2">
                  <span className="bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] font-bold text-white uppercase tracking-wider border border-white/10">
                    {card.aiModel}
                  </span>
                  <span
                    className={cn(
                      "backdrop-blur-md px-2 py-1 rounded text-[10px] font-bold text-white uppercase tracking-wider border border-white/10",
                      card.categoryColor
                    )}
                  >
                    {card.category}
                  </span>
                </div>

                {/* Duration */}
                <div className="absolute bottom-3 right-3 z-10">
                  <span className="bg-black/80 backdrop-blur-md px-2 py-0.5 rounded text-xs font-mono font-medium text-gray-300 border border-white/10">
                    {card.duration}
                  </span>
                </div>

                {/* Image */}
                <img
                  src={card.thumbnailUrl}
                  alt={card.title}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                />

                {/* Gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-40 transition-opacity" />

                {/* Play button on hover */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="w-16 h-16 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center text-white border border-white/20 shadow-[0_0_25px_rgba(236,72,153,0.4)] transform scale-75 group-hover:scale-100 transition-transform">
                    <Play className="w-8 h-8 fill-white" />
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-5">
                <h4 className="font-bold text-white text-xl leading-tight group-hover:text-pink-400 transition-colors mb-2">
                  {card.title}
                </h4>
                <p className="text-gray-400 text-sm line-clamp-2 mb-4">
                  {card.description}
                </p>

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                  {/* Creator */}
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full overflow-hidden border border-white/10 ring-2 ring-black">
                      <img
                        src={card.creator.avatarUrl}
                        alt={card.creator.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-xs text-white font-semibold">
                        {card.creator.name}
                      </span>
                      <span className="text-[10px] text-gray-500 uppercase tracking-wide">
                        {card.creator.role}
                      </span>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-gray-500 text-xs font-medium">
                    <div className="flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer">
                      <Eye className="w-4 h-4" />
                      <span>{card.views}</span>
                    </div>
                    <div className="flex items-center gap-1.5 hover:text-pink-400 transition-colors cursor-pointer">
                      <ThumbsUp className="w-4 h-4" />
                      <span>{card.likePercent}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Mobile view all link */}
        <div className="flex md:hidden justify-center mt-6">
          <a
            href="/singularity"
            className="text-pink-400 text-sm font-medium flex items-center gap-2"
          >
            View all 12 shorts
            <ChevronRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    </section>
  );
}

export default UserCinemaSection;
