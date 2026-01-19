"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, FileText, Shield } from "lucide-react";

export default function TermsPage() {
  return (
    <Suspense
      fallback={<div className="min-h-screen bg-[#0F0F1A] flex items-center justify-center text-white">Loading...</div>}
    >
      <TermsContentPage />
    </Suspense>
  );
}

function TermsContentPage() {
  const searchParams = useSearchParams();
  const urlTab = searchParams.get("tab");
  const resolvedTab =
    urlTab === "terms" || urlTab === "privacy" || urlTab === "refund" ? urlTab : null;
  const [manualTab, setManualTab] = useState<"terms" | "privacy" | "refund" | null>(null);
  const activeTab = manualTab ?? resolvedTab ?? "terms";

  return (
    <div className="min-h-screen bg-[#0F0F1A] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#0F0F1A]/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">홈으로 돌아가기</span>
          </Link>
          <div className="flex items-center gap-2">
            <span className="text-white font-bold">Crebit</span>
            <span className="text-slate-500">·</span>
            <span className="text-white font-bold">Policy Center</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-center mb-2">서비스 약관 및 정책</h1>
        <p className="text-slate-400 text-center mb-12">
          이용약관 · 개인정보처리방침 · 환불정책
        </p>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 p-1 rounded-xl bg-white/5 border border-white/10">
          <button
            onClick={() => setManualTab("terms")}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
              activeTab === "terms"
                ? "bg-violet-500 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <FileText className="w-4 h-4 inline mr-2" />
            이용약관
          </button>
          <button
            onClick={() => setManualTab("privacy")}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
              activeTab === "privacy"
                ? "bg-violet-500 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Shield className="w-4 h-4 inline mr-2" />
            개인정보처리방침
          </button>
          <button
            onClick={() => setManualTab("refund")}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${
              activeTab === "refund"
                ? "bg-[#FF0045] text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            환불정책
          </button>
        </div>

        {/* Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="prose prose-invert prose-sm max-w-none"
        >
          {activeTab === "terms" && <TermsContent />}
          {activeTab === "privacy" && <PrivacyContent />}
          {activeTab === "refund" && <RefundContent />}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-xs text-slate-500">
        <p>© 2026 Crebit. All rights reserved.</p>
        <p className="mt-2">문의: support@crebit.ai</p>
      </footer>
    </div>
  );
}

function TermsContent() {
  return (
    <div className="space-y-8 text-slate-300">
      <section>
        <h2 className="text-xl font-bold text-white mb-4">제1조 (목적)</h2>
        <p>
          이 약관은 주식회사 페이지아카데미(이하 &quot;회사&quot;)가 제공하는 Crebit ATC 프로그램(이하 &quot;서비스&quot;)의
          이용조건 및 절차, 회사와 회원 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.
        </p>
        <p className="mt-2 text-sm text-slate-400">
          본 프로그램은 주식회사 아캐인(Arkain)이 기획・제작하고, 주식회사 페이지아카데미가 학원업 등록 사업자로서
          운영・판매합니다. 결제는 페이지아카데미 명의의 NICE Payments를 통해 처리됩니다.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제2조 (용어의 정의)</h2>
        <ul className="list-disc list-inside space-y-2">
          <li><strong>&quot;회원&quot;</strong>이란 본 약관에 동의하고 서비스 이용 계약을 체결한 자를 말합니다.</li>
          <li><strong>&quot;서비스&quot;</strong>란 회사가 제공하는 Crebit ATC 교육 프로그램과 관련 서비스를 말합니다.</li>
          <li><strong>&quot;콘텐츠&quot;</strong>란 강의 자료, 템플릿, 제작 가이드 등 프로그램 내 제공되는 모든 자료를 말합니다.</li>
          <li><strong>&quot;결과물&quot;</strong>이란 프로그램 과정에서 제작되는 영상 및 산출물을 말합니다.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제3조 (서비스 내용)</h2>
        <div className="bg-white/5 rounded-xl p-5 border border-white/10">
          <h3 className="font-bold text-white mb-3">Crebit ATC 1기 프로그램</h3>
          <ul className="space-y-2 text-sm">
            <li>• 오프라인 도제식 소수 정예 교육 (성수동 스튜디오)</li>
            <li>• 3개월(12주) 집중 과정, 트랙별 주 1~3회 운영</li>
            <li>• Basic / Pro 트랙 운영 (세부 일정은 안내 페이지 기준)</li>
            <li>• 실습 기반 제작, 멘토 디렉팅, 피드백 반복</li>
            <li>• 결과물 전면 공개 + 포트폴리오 제작</li>
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제4조 (이용계약의 성립)</h2>
        <p>이용계약은 회원이 본 약관에 동의하고, 결제를 완료한 시점에 성립됩니다.</p>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제5조 (서비스 이용 기간)</h2>
        <ul className="list-disc list-inside space-y-2">
          <li>프로그램 일정에 따름 (1기: 2026년 2월 3일 개강, 3개월)</li>
          <li>일정 및 장소는 운영 상황에 따라 변경될 수 있음</li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제6조 (저작권 및 사용 제한)</h2>
        <p>
          서비스 내 모든 콘텐츠에 대한 저작권은 회사 및 제작사(주식회사 아캐인)에 있으며,
          회원은 개인 학습 목적으로만 이용할 수 있습니다.
        </p>
        <div className="mt-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          ⚠️ 콘텐츠의 복제, 배포, 전송, 2차 가공 및 상업적 이용은 엄격히 금지됩니다.
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제7조 (결과물 공개 동의)</h2>
        <p>
          본 프로그램은 결과물 공개를 원칙으로 합니다. 회원은 프로그램 과정에서 제작된 결과물이
          Crebit, 페이지아카데미, 아캐인 채널에 공개될 수 있음에 동의합니다.
        </p>
        <p className="mt-2 text-sm text-slate-400">
          공개 시 이름 또는 크리에이터 핸들이 함께 표시될 수 있으며, 별도 보상은 제공되지 않습니다.
          동의하지 않는 경우 신청이 제한됩니다.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">제8조 (면책 및 책임 제한)</h2>
        <ul className="list-disc list-inside space-y-2 text-sm">
          <li>회사는 프로그램 참여를 통해 특정 성과나 수익을 보장하지 않습니다.</li>
          <li>천재지변, 시스템 장애 등 불가항력으로 인한 중단에 대해 책임지지 않습니다.</li>
          <li>회원의 귀책사유로 인한 이용 장애에 대해 책임지지 않습니다.</li>
        </ul>
      </section>

      <section className="text-sm text-slate-500">
        <p>시행일: 2026년 1월 19일</p>
        <p>최종 수정일: 2026년 1월 19일</p>
      </section>
    </div>
  );
}

function PrivacyContent() {
  return (
    <div className="space-y-8 text-slate-300">
      <section>
        <h2 className="text-xl font-bold text-white mb-4">1. 수집하는 개인정보 항목</h2>
        <div className="bg-white/5 rounded-xl p-5 border border-white/10">
          <h3 className="font-bold text-white mb-3">필수 수집 항목</h3>
          <ul className="space-y-2 text-sm">
            <li>• <strong>이름:</strong> 수강생 식별 및 수료증 발급</li>
            <li>• <strong>이메일:</strong> 프로그램 안내 및 공지</li>
            <li>• <strong>연락처:</strong> 일정/변경 안내 및 고객 상담</li>
            <li>• <strong>포트폴리오 링크:</strong> 프로그램 관리 및 결과물 정리</li>
            <li>• <strong>결제정보:</strong> 수강료 결제 처리 (나이스페이먼츠 위탁)</li>
          </ul>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-bold text-white mb-4">2. 개인정보 수집 및 이용 목적</h2>
        <ul className="list-disc list-inside space-y-2 text-sm">
          <li>프로그램 운영 및 수강생 관리</li>
          <li>결제 처리 및 환불</li>
          <li>공지사항 전달 및 고객 문의 대응</li>
          <li>성과 분석 및 서비스 개선</li>
        </ul>
      </section>
    </div>
  );
}

function RefundContent() {
  return (
    <div className="space-y-8 text-slate-300">
      <section>
        <h2 className="text-xl font-bold text-white mb-4">환불 규정</h2>
        <p className="text-sm text-slate-400">
          환불 규정은 결제일 기준으로 적용되며, 서비스 진행 단계에 따라 환불 금액이 달라질 수 있습니다.
          자세한 환불 문의는 support@crebit.ai로 요청해 주세요.
        </p>
      </section>
    </div>
  );
}
