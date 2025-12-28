"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, FileText, Shield } from "lucide-react";

export default function CrebitTermsPage() {
    const searchParams = useSearchParams();
    const [activeTab, setActiveTab] = useState<"terms" | "privacy" | "refund">("terms");

    useEffect(() => {
        const tab = searchParams.get("tab");
        if (tab === "terms" || tab === "privacy" || tab === "refund") {
            setActiveTab(tab);
        }
    }, [searchParams]);

    return (
        <div className="min-h-screen bg-[#050505] text-white">
            {/* Header */}
            <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="/crebit" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-4 h-4" />
                        <span className="text-sm">Crebit ATC로 돌아가기</span>
                    </Link>
                    <div className="flex items-center gap-2">
                        <span className="text-white font-bold">Arkain</span>
                        <span className="text-slate-500">×</span>
                        <span className="text-white font-bold">Page Academy</span>
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-bold text-center mb-2">Crebit 약관 및 정책</h1>
                <p className="text-slate-400 text-center mb-12">Crebit ATC 프로그램 이용약관 · 개인정보처리방침 · 환불정책</p>

                {/* Tab Navigation */}
                <div className="flex gap-2 mb-8 p-1 rounded-xl bg-white/5 border border-white/10">
                    <button
                        onClick={() => setActiveTab("terms")}
                        className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${activeTab === "terms" ? "bg-[#4200FF] text-white" : "text-slate-400 hover:text-white"
                            }`}
                    >
                        <FileText className="w-4 h-4 inline mr-2" />
                        이용약관
                    </button>
                    <button
                        onClick={() => setActiveTab("privacy")}
                        className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${activeTab === "privacy" ? "bg-[#4200FF] text-white" : "text-slate-400 hover:text-white"
                            }`}
                    >
                        <Shield className="w-4 h-4 inline mr-2" />
                        개인정보처리방침
                    </button>
                    <button
                        onClick={() => setActiveTab("refund")}
                        className={`flex-1 py-3 px-4 rounded-lg text-sm font-medium transition-all ${activeTab === "refund" ? "bg-[#FF0045] text-white" : "text-slate-400 hover:text-white"
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
                <p>© 2026 Page Academy × Arkain. All rights reserved.</p>
                <p className="mt-2">문의: kaylee@page-academy.com</p>
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
                    이 약관은 주식회사 페이지아카데미(이하 "회사")가 제공하는 Crebit ATC 프로그램(이하 "서비스")의
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
                    <li><strong>"회원"</strong>이란 본 약관에 동의하고 서비스 이용 계약을 체결한 자를 말합니다.</li>
                    <li><strong>"서비스"</strong>란 회사가 제공하는 Crebit ATC 교육 프로그램과 관련 서비스를 말합니다.</li>
                    <li><strong>"콘텐츠"</strong>란 강의 자료, 템플릿, 제작 가이드 등 프로그램 내 제공되는 모든 자료를 말합니다.</li>
                    <li><strong>"결과물"</strong>이란 프로그램 과정에서 제작되는 영상 및 산출물을 말합니다.</li>
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
                <ul className="list-disc list-inside space-y-2">
                    <li>교육 서비스 제공 및 본인 확인</li>
                    <li>수강 진행 관리 및 수료증 발급</li>
                    <li>고객 상담 및 불만 처리</li>
                    <li>서비스 개선을 위한 통계 분석</li>
                    <li>마케팅 및 이벤트 안내 (선택 동의 시)</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">3. 개인정보 보유 및 이용 기간</h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm border border-white/10 rounded-lg overflow-hidden">
                        <thead className="bg-white/5">
                            <tr>
                                <th className="px-4 py-3 text-left">항목</th>
                                <th className="px-4 py-3 text-left">보유 기간</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr className="border-t border-white/10">
                                <td className="px-4 py-3">회원 정보</td>
                                <td className="px-4 py-3">회원 탈퇴 시까지</td>
                            </tr>
                            <tr className="border-t border-white/10">
                                <td className="px-4 py-3">결제 기록</td>
                                <td className="px-4 py-3">5년 (전자상거래법)</td>
                            </tr>
                            <tr className="border-t border-white/10">
                                <td className="px-4 py-3">수강 기록</td>
                                <td className="px-4 py-3">3년</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">4. 개인정보 제3자 제공</h2>
                <p>회사는 원칙적으로 개인정보를 제3자에게 제공하지 않습니다. 다만, 아래의 경우 예외로 합니다:</p>
                <ul className="list-disc list-inside space-y-2 mt-3 text-sm">
                    <li>회원이 사전에 동의한 경우</li>
                    <li>법령에 의해 요구되는 경우</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">5. 개인정보 처리 위탁</h2>
                <div className="bg-white/5 rounded-xl p-5 border border-white/10 text-sm">
                    <table className="w-full">
                        <tbody>
                            <tr>
                                <td className="py-2 font-medium">결제 처리</td>
                                <td className="py-2 text-slate-400">나이스페이먼츠(주)</td>
                            </tr>
                            <tr className="border-t border-white/10">
                                <td className="py-2 font-medium">콘텐츠 제작 및 운영 지원</td>
                                <td className="py-2 text-slate-400">주식회사 아캐인 (Arkain)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">6. 개인정보보호 책임자</h2>
                <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                    <p><strong>성명:</strong> 이용찬</p>
                    <p><strong>직책:</strong> 대표이사</p>
                    <p><strong>이메일:</strong> kaylee@page-academy.com</p>
                </div>
            </section>

            <section className="text-sm text-slate-500">
                <p>시행일: 2026년 1월 19일</p>
            </section>
        </div>
    );
}

function RefundContent() {
    return (
        <div className="space-y-8 text-slate-300">
            <section>
                <h2 className="text-xl font-bold text-white mb-4">환불 정책</h2>
                <p>
                    본 환불 정책은 「학원의 설립・운영 및 과외교습에 관한 법률」 및 「전자상거래법」에 따라 운영됩니다.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">1. 청약 철회 (결제 후 7일 이내)</h2>
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-5">
                    <p className="text-emerald-400 font-medium mb-3">✓ 전액 환불 조건</p>
                    <ul className="space-y-2 text-sm">
                        <li>• 결제 후 7일 이내 환불 요청</li>
                        <li>• <strong>프로그램 진행률 30% 미만</strong></li>
                        <li>• 위 두 조건을 모두 충족 시 전액 환불</li>
                    </ul>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">2. 중도 환불 (결제 후 7일 경과)</h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm border border-white/10 rounded-lg overflow-hidden">
                        <thead className="bg-white/5">
                            <tr>
                                <th className="px-4 py-3 text-left">진행률</th>
                                <th className="px-4 py-3 text-left">환불 금액</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr className="border-t border-white/10">
                                <td className="px-4 py-3">1/3 미만 진행</td>
                                <td className="px-4 py-3">수강료의 2/3 환불</td>
                            </tr>
                            <tr className="border-t border-white/10">
                                <td className="px-4 py-3">1/2 미만 진행</td>
                                <td className="px-4 py-3">수강료의 1/2 환불</td>
                            </tr>
                            <tr className="border-t border-white/10 bg-red-500/5">
                                <td className="px-4 py-3 text-red-400">1/2 이상 진행</td>
                                <td className="px-4 py-3 text-red-400">환불 불가</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">3. 환불 불가 항목</h2>
                <ul className="list-disc list-inside space-y-2">
                    <li>이미 제공된 자료 및 템플릿</li>
                    <li>발급된 수료증</li>
                    <li>커뮤니티/멘토링 제공 기록</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">4. 환불 신청 방법</h2>
                <div className="bg-white/5 rounded-xl p-5 border border-white/10 space-y-3">
                    <p><strong>1단계:</strong> 아래 이메일로 환불 요청</p>
                    <p className="pl-4 text-[#4200FF]">kaylee@page-academy.com</p>
                    <p><strong>2단계:</strong> 환불 사유 및 계좌 정보 기재</p>
                    <p><strong>3단계:</strong> 환불 승인 후 5-7영업일 내 입금</p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-bold text-white mb-4">5. 환불 처리 기간</h2>
                <ul className="list-disc list-inside space-y-2 text-sm">
                    <li>환불 신청 접수: 1영업일 이내 확인</li>
                    <li>환불 승인 후: 5-7영업일 이내 계좌 입금</li>
                    <li>카드 결제 취소: 카드사별 상이 (최대 2주)</li>
                </ul>
            </section>

            <section className="text-sm text-slate-500">
                <p>시행일: 2026년 1월 19일</p>
                <p className="mt-2">※ 본 환불 정책은 관련 법령 변경 시 수정될 수 있습니다.</p>
            </section>
        </div>
    );
}
