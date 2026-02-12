import type { Metadata } from "next";
import ADStudioPanel from "@/components/dimension/ADStudioPanel";

export const metadata: Metadata = {
  title: "AD Studio | Crebit",
  description: "조감독 AI — 레퍼런스 분석에서 시네마틱 프롬프트 자동 생성",
};

export default function ADStudioPage() {
  return <ADStudioPanel />;
}
