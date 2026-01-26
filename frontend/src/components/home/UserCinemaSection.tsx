"use client";

/**
 * User AI Cinema & Animation Section - Stitch V2 Style (Dark Mode)
 *
 * Based on Stitch design:
 * - Short films created with next-gen multimodal models
 * - Video cards with duration, category badges
 * - Creator info with avatar, name, views and likes
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
  category: string;
  categoryColor: string;
  creator: {
    name: string;
    avatarUrl: string;
  };
  views: string;
  likePercent: number;
}

const CINEMA_CARDS: CinemaCard[] = [
  {
    id: "neon-horizon",
    title: "네온 호라이즌",
    description:
      "잠들지 않는 도시를 헤매는 안드로이드가 존재하지 않았을지도 모를 과거의 기억을 찾아 나섭니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAwyZBDD7Rq4xTppWZ5aAUrjShF5mzTZtow9OgCYcgGoi6u9oqfzUAbk5pl6WDXKtfDz0cFqTXEKP_NU2cmhVehZ60Hd4RQ5GXj_6xbjCi0z3Lmc-RReksa6p5UwPzdD7Ft2pvyjuAzzJYGJj5tWOlKLHx37zxy3XXdW8C-hGFVpElTQINY4MnvmuYPXHuuartUGmRuFPuFbiizvAidvlhF1Y5WTkd88CK_0eG93kKp1A9qaTSgqqjqYLcRbUS1FGlMkSqAZwq3OTw",
    duration: "3:00",
    category: "SHORT",
    categoryColor: "bg-[var(--bg-primary)]",
    creator: {
      name: "Alex Chen",
      avatarUrl:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuAihzfhGiK-cuyzA7vJ5LoaYLBNwFq9NbSV8MnnXnPBSTJ0XUOVFxAumhkmxbgCj4hsOOIShlq-BklMirnrDFvYeTvnB3PUVYLmx1lWT8zTuEA4uf4IkrxVHaLHnmrzuZVJDuP0wUmowLewq6h6_O5wuJXN4AWq2iiKk1VfwulRt0WdAN-X7cztQf_UHxYLYAg5QEuRhgMoAvRpKYCwNaXCkHnFyBAowBERxVKP441K3b-5P2142Vd1HTvNi5yNOK1cT0dcJPjt21M",
    },
    views: "12.4k",
    likePercent: 98,
  },
  {
    id: "echoes-of-light",
    title: "빛의 메아리",
    description:
      "AI가 생성한 풍경과 신스웨이브 사운드트랙이 동기화된 추상적 시각 여행입니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAAHexhqEvSDEKOwXWqDlj0I2qe43rx05pv-9SDHALDu3vcE2-6-wjEIffYnmRfK22BJB-JIfAZdlB08PJCrm5aGNnbRfJf-1hISk9cUkkD36LUHXODE-0D-Pqrc1yJjb7ZgnAaGlIWlV-WiW8b9m2LbNjdkOR4Pl0kRz7uZIT-VXMgDVeHYeuxHQrdGY1JMYBYERqO5Rajtc9hpGkrphxiYvusC00q_2WD1BH520cw4qYW1PFZg5LO7zn_Z78TxwwZU4dpL0-QX38",
    duration: "3:42",
    category: "MUSIC VIDEO",
    categoryColor: "bg-purple-500",
    creator: {
      name: "Sarah Void",
      avatarUrl:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuC5QaTGBVcDFzYQmvqdFxg5zg8m7N76grsISsepxva09mAhxwyLWx9xtuTAlX5Rgu3X5zt05t2thp0sLSZUolkH-Tq9Or8bYlIDDmY6s7fFTFgEIy6u_lnBrDDSc-c68xgfCfjX3SjKQdC3CFai9FTXRaQRx39qkjsI0YaYN8_jPaOT2nxeAMsgUn1zS6Y2sHLtm7oa_YNmKKwrRMpyK96vIbkDXJO376o0-Kc4tPYcbuenE8_odv9PdmwC3wLF_Dy5w0FmwdoGNHM",
    },
    views: "8.2k",
    likePercent: 95,
  },
  {
    id: "last-signal",
    title: "마지막 신호",
    description:
      "심우주 탐험가들이 인류의 우주에 대한 이해를 바꿀 메시지를 수신합니다.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuDxZKoOnHrh27hFb_pgPcDA6fUOKEs9LFs56daf8zcRdBONS9MNs-l0SL7oqdPP6uHt6s6iTXZigBSK8ufIb3ZlHO9Y9nSwQKtGpOMF5nijYmQxlg-ahC-9n4O2hSj2e0T9FdL8kcdhoD4Yf5q96HKrYv5xCidAml-imtFxN7x33dB8qdeA2N22tD7p-AScU973ZCNEOmHF0VrGXrQO40w1U6gA_Yrk2RG0Zk-8TlNOuFQqoSAuiaE-U9h_jMcw-KB4vq4m7qFqtV8",
    duration: "2:15",
    category: "SCI-FI",
    categoryColor: "bg-blue-500",
    creator: {
      name: "Markus R",
      avatarUrl:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuC6b3ip4oErhG2Efqh1VP4CnsF8DNDXTHVDyiJbdyPkqM_1VxeXfbKPTckgY4ZmC79l8Q2QEfq2mBFpJxjI3_w77ujigw0bWEzHA0BCWXK_YAUoWcz8ew_W6cgiEBDA7hDBOrVkIRRUAou57o4XE0YPCTs8Zl2ch-vECEmpEnN6CyG1Csc2RY7_kZjpqikh1lWYmcCSle-YBZFZrwVmaNUPJKTYluiiXL0WUUrTLVJTbDj8MtEelovfcFLjEhkwNddL_Bug5Pxf8es",
    },
    views: "5.7k",
    likePercent: 91,
  },
];

export function UserCinemaSection() {
  return (
    <section className="py-20 px-6 md:px-16 bg-[var(--bg-base)]">
      <div className="max-w-7xl mx-auto">
        {/* Header - Stitch Style */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="flex items-end justify-between mb-8"
        >
          <div className="border-l-4 border-[var(--border-primary)] pl-4">
            <h3 className="text-2xl font-bold text-white">
              유저 AI 시네마
            </h3>
            <p className="text-gray-400 text-sm mt-1">
              차세대 멀티모달 모델로 제작된 숏폼 영상들
            </p>
          </div>
          <a
            href="/singularity"
            className="group text-gray-400 hover:text-[var(--fg-primary)] text-sm font-medium hidden md:flex items-center gap-1 transition-colors"
          >
            12개의 숏폼 모두 보기
            <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </a>
        </motion.div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {CINEMA_CARDS.map((card, index) => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group cursor-pointer"
            >
              {/* Thumbnail */}
              <div className="relative rounded-3xl overflow-hidden aspect-video shadow-lg mb-4">
                {/* Category Badge */}
                <span
                  className={cn(
                    "absolute top-4 left-4 z-10",
                    "text-[10px] font-bold px-2 py-1 rounded-full text-white",
                    card.categoryColor
                  )}
                >
                  {card.category}
                </span>

                {/* Duration */}
                <span className="absolute bottom-4 right-4 z-10 bg-black/50 backdrop-blur-md text-white text-xs font-medium px-2 py-1 rounded-md">
                  {card.duration}
                </span>

                {/* Image */}
                <img
                  src={card.thumbnailUrl}
                  alt={card.title}
                  className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-700"
                />

                {/* Gradient overlay on hover */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                {/* Play button on hover */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="w-12 h-12 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center text-white border border-white/30">
                    <Play className="w-5 h-5 fill-white" />
                  </div>
                </div>
              </div>

              {/* Content */}
              <h4 className="font-bold text-lg text-white group-hover:text-[var(--fg-primary)] transition-colors">
                {card.title}
              </h4>
              <p className="text-sm text-gray-400 line-clamp-2 mt-1 mb-3">
                {card.description}
              </p>

              {/* Footer - Creator info */}
              <div className="flex items-center justify-between text-xs text-gray-500 border-t border-gray-800 pt-3">
                <div className="flex items-center gap-2">
                  <img
                    src={card.creator.avatarUrl}
                    alt={card.creator.name}
                    className="w-6 h-6 rounded-full object-cover"
                  />
                  <span className="font-medium text-gray-300">
                    {card.creator.name}
                  </span>
                </div>
                <div className="flex gap-3">
                  <span className="flex items-center gap-1">
                    <Eye className="w-4 h-4" />
                    {card.views}
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="w-4 h-4" />
                    {card.likePercent}%
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Mobile view all link */}
        <div className="flex md:hidden justify-center mt-6">
          <a
            href="/singularity"
            className="text-[var(--fg-primary)] text-sm font-medium flex items-center gap-2"
          >
            12개의 숏폼 모두 보기
            <ChevronRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    </section>
  );
}

export default UserCinemaSection;
