"use client";

/**
 * Human Cloud CTA Section - Stitch V2 Neon Red Design
 *
 * Professional creator marketplace CTA
 * 12-column grid with creator cards
 */

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Star, ArrowRight } from "lucide-react";

export interface Creator {
  id: string;
  initial: string;
  name: string;
  specialty: string;
  specialtyColor: "primary" | "blue" | "green";
  rating: number;
  description: string;
}

interface HumanCloudCTAProps {
  creators?: Creator[];
  onStartMatching?: () => void;
  onCreatorClick?: (id: string) => void;
}

// Default creator data matching stitch_ui_2 design
const DEFAULT_CREATORS: Creator[] = [
  {
    id: "kim-minjun",
    initial: "K",
    name: "김민준",
    specialty: "영상 편집",
    specialtyColor: "primary",
    rating: 4.9,
    description:
      "10년 경력의 시네마틱 편집 전문가입니다. SF 및 판타지 장르의 컷 편집과 색보정에 특화되어 있습니다.",
  },
  {
    id: "park-seoyeon",
    initial: "P",
    name: "박서연",
    specialty: "애니메이터",
    specialtyColor: "blue",
    rating: 5.0,
    description:
      "3D 캐릭터 리깅 및 모션 캡처 데이터 클린업 전문입니다. 자연스러운 움직임을 만들어 드립니다.",
  },
  {
    id: "lee-jinwoo",
    initial: "L",
    name: "이진우",
    specialty: "사운드 디자인",
    specialtyColor: "green",
    rating: 4.8,
    description:
      "돌비 애트모스 믹싱 및 현장감 넘치는 SFX 제작. 영상의 몰입도를 높이는 사운드스케이프를 디자인합니다.",
  },
];

const SPECIALTY_COLORS = {
  primary: "text-[#FF003C] bg-[#FF003C]/10",
  blue: "text-blue-400 bg-blue-400/10",
  green: "text-green-400 bg-green-400/10",
};

export function HumanCloudCTA({
  creators = DEFAULT_CREATORS,
  onStartMatching,
  onCreatorClick,
}: HumanCloudCTAProps) {
  return (
    <section className="relative z-20 px-6 md:px-16 py-24 bg-[#0F0F0F] border-t border-white/5">
      {/* Background Blur Effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-0 w-[500px] h-[500px] bg-[#FF003C]/5 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-16 relative z-10">
        {/* Left Column - Text Content */}
        <div className="lg:col-span-4 flex flex-col justify-center">
          {/* Badge */}
          <div className="flex items-center gap-2 mb-4">
            <span className="w-2 h-2 bg-[#FF003C] rounded-full animate-pulse" />
            <span className="text-[#FF003C] text-xs font-bold tracking-widest uppercase">
              Human Cloud
            </span>
          </div>

          {/* Title */}
          <h2 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight text-white">
            프로에게 <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500">
              의뢰하기
            </span>
          </h2>

          {/* Description */}
          <p className="text-gray-400 font-light break-keep mb-8 text-lg">
            AI의 속도와 인간 전문가의 섬세함을 결합하여 프로젝트의 완성도를 극대화하세요.
            검증된 전문가들이 대기 중입니다.
          </p>

          {/* CTA Button */}
          <Link
            href="/humancloud"
            className="px-8 py-4 bg-white text-black font-bold uppercase tracking-wider hover:bg-gray-200 transition-colors rounded-lg w-full md:w-auto flex items-center justify-center gap-2 group"
            onClick={onStartMatching}
          >
            <span>전문가 매칭 시작</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Right Column - Creator Cards */}
        <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {creators.slice(0, 2).map((creator, index) => (
            <motion.div
              key={creator.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-[#050505] p-6 rounded-xl border border-white/10 hover:border-[#FF003C]/50 transition-all group hover:-translate-y-1 duration-300 shadow-lg"
              onClick={() => onCreatorClick?.(creator.id)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-white text-xl font-bold border border-white/10">
                    {creator.initial}
                  </div>
                  <div>
                    <h4 className="text-lg font-bold text-white">{creator.name}</h4>
                    <span
                      className={`text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wider ${
                        SPECIALTY_COLORS[creator.specialtyColor]
                      }`}
                    >
                      {creator.specialty}
                    </span>
                  </div>
                </div>
                <div className="flex items-center text-yellow-500 gap-1 bg-yellow-500/10 px-2 py-1 rounded">
                  <Star className="w-3.5 h-3.5 fill-current" />
                  <span className="font-bold text-xs">{creator.rating}</span>
                </div>
              </div>

              <p className="text-sm text-gray-400 mb-6 line-clamp-2 h-10">
                {creator.description}
              </p>

              <button className="w-full py-3 border border-white/20 rounded-lg text-sm font-bold text-white uppercase hover:bg-white hover:text-black transition-all">
                의뢰 시작하기
              </button>
            </motion.div>
          ))}

          {/* Full Width Third Card */}
          {creators[2] && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-[#050505] p-6 rounded-xl border border-white/10 hover:border-[#FF003C]/50 transition-all group hover:-translate-y-1 duration-300 shadow-lg md:col-span-2"
              onClick={() => onCreatorClick?.(creators[2].id)}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center text-white text-xl font-bold border border-white/10">
                    {creators[2].initial}
                  </div>
                  <div>
                    <h4 className="text-lg font-bold text-white">{creators[2].name}</h4>
                    <span
                      className={`text-[10px] px-2 py-1 rounded font-bold uppercase tracking-wider ${
                        SPECIALTY_COLORS[creators[2].specialtyColor]
                      }`}
                    >
                      {creators[2].specialty}
                    </span>
                  </div>
                </div>
                <div className="flex items-center text-yellow-500 gap-1 bg-yellow-500/10 px-2 py-1 rounded">
                  <Star className="w-3.5 h-3.5 fill-current" />
                  <span className="font-bold text-xs">{creators[2].rating}</span>
                </div>
              </div>

              <p className="text-sm text-gray-400 mb-6 line-clamp-2">
                {creators[2].description}
              </p>

              <button className="w-full py-3 border border-white/20 rounded-lg text-sm font-bold text-white uppercase hover:bg-white hover:text-black transition-all">
                의뢰 시작하기
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </section>
  );
}

export default HumanCloudCTA;
