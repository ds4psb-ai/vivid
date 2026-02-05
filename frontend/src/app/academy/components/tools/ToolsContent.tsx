"use client";

import { useState } from "react";
import type { TabKey } from "../../constants";
import { PageHeader, ContentCard } from "../shared";
import { ToolDetailCard } from "./ToolDetailCard";
import { FAQItem } from "./FAQItem";
import { FAQ_ITEMS, MIDJOURNEY_PARAMS, KLING_CAMERA_OPTIONS, KLING_MOTION_SCORES } from "./toolsData";

interface ToolsContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function ToolsContent({ setActiveTab }: ToolsContentProps) {
  const [openTool, setOpenTool] = useState<string | null>(null);
  const [openFaq, setOpenFaq] = useState<string | null>(null);

  const toggleTool = (tool: string) => {
    setOpenTool(openTool === tool ? null : tool);
  };

  const toggleFaq = (faq: string) => {
    setOpenFaq(openFaq === faq ? null : faq);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <PageHeader title="외부 툴" sub="파싱 탭에서 복사한 프롬프트를 여기 도구에 붙여넣기" />

      {/* Workflow Connection Notice */}
      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-emerald-400">link</span>
          <div>
            <p className="text-emerald-300 font-bold text-sm">워크플로우 연결</p>
            <p className="text-emerald-200/70 text-xs mt-1">
              <span className="text-white font-medium">파싱 탭</span>에서 복사한 프롬프트 → 아래 도구에 붙여넣기
            </p>
          </div>
        </div>
      </div>

      {/* Image Tools Section */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-purple-400">image</span>
          이미지 생성
        </h3>

        {/* NanoBanana Pro */}
        <ToolDetailCard
          title="NanoBanana Pro"
          color="orange"
          url="https://gemini.google.com"
          isOpen={openTool === "nanobanana"}
          onToggle={() => toggleTool("nanobanana")}
          badge="한글 OK"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">실행 단계</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-orange-400 font-bold">1.</span>gemini.google.com 접속</li>
                <li className="flex gap-2"><span className="text-orange-400 font-bold">2.</span>오른쪽 상단 모델 선택 → "2.0 Flash (Experimental)"</li>
                <li className="flex gap-2"><span className="text-orange-400 font-bold">3.</span>파싱탭에서 복사한 NanoBanana 프롬프트 붙여넣기</li>
                <li className="flex gap-2"><span className="text-orange-400 font-bold">4.</span>생성된 이미지 다운로드 (우클릭 → 이미지 저장)</li>
              </ol>
            </div>
            <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <p className="text-orange-300 text-xs">💡 <span className="font-bold">팁:</span> 한글 프롬프트 100% 지원, Google AI Pro 구독 포함</p>
            </div>
          </div>
        </ToolDetailCard>

        {/* Midjourney V7 */}
        <ToolDetailCard
          title="Midjourney V7"
          color="violet"
          url="https://www.midjourney.com"
          isOpen={openTool === "midjourney"}
          onToggle={() => toggleTool("midjourney")}
          badge="--cref"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">웹사이트 방법 (권장)</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-violet-400 font-bold">1.</span>midjourney.com 접속 → 로그인</li>
                <li className="flex gap-2"><span className="text-violet-400 font-bold">2.</span>하단 프롬프트 입력창에 붙여넣기</li>
                <li className="flex gap-2"><span className="text-violet-400 font-bold">3.</span>Enter로 생성</li>
              </ol>
            </div>
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">Discord 방법</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-violet-400 font-bold">1.</span>Discord → Midjourney 서버</li>
                <li className="flex gap-2"><span className="text-violet-400 font-bold">2.</span><code className="text-violet-300 bg-violet-500/20 px-1 rounded">/imagine</code> 명령어 + 프롬프트</li>
              </ol>
            </div>

            {/* Parameter Table */}
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">파라미터 레퍼런스</p>
              <div className="overflow-hidden rounded-lg border border-violet-500/20">
                <table className="w-full text-xs">
                  <thead className="bg-violet-500/10">
                    <tr>
                      <th className="text-left text-violet-300 px-3 py-2 font-bold">파라미터</th>
                      <th className="text-left text-violet-300 px-3 py-2 font-bold">설명</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-violet-500/10">
                    {MIDJOURNEY_PARAMS.map((p) => (
                      <tr key={p.param}>
                        <td className="px-3 py-1.5 text-violet-200 font-mono">{p.param}</td>
                        <td className="px-3 py-1.5 text-gray-400">{p.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Anchor Image Workflow */}
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <p className="text-amber-300 text-xs font-bold mb-2">⭐ 앵커 이미지 사용법</p>
              <ol className="text-amber-200/80 text-xs space-y-1">
                <li>1. <span className="text-white">앵커 씬</span> 먼저 생성 (--oref 없는 프롬프트)</li>
                <li>2. 생성된 이미지 URL 복사 (우클릭 → 이미지 주소 복사)</li>
                <li>3. 나머지 씬 프롬프트의 <span className="text-white">[ANCHOR_URL]</span>을 복사한 URL로 교체</li>
              </ol>
            </div>
          </div>
        </ToolDetailCard>
      </ContentCard>

      {/* Video Tools Section */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-red-400">movie</span>
          영상 생성
        </h3>

        {/* Kling 3.0 */}
        <ToolDetailCard
          title="Kling 3.0"
          color="cyan"
          url="https://klingai.com"
          isOpen={openTool === "kling"}
          onToggle={() => toggleTool("kling")}
          badge="4K"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">실행 단계</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">1.</span>klingai.com 접속 → 로그인</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">2.</span>"AI Videos" → "Image to Video" 선택</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">3.</span>생성한 이미지 업로드</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">4.</span>파싱탭에서 복사한 Kling 프롬프트 붙여넣기</li>
                <li className="flex gap-2"><span className="text-cyan-400 font-bold">5.</span>Duration, Camera 설정 → Generate</li>
              </ol>
            </div>

            {/* Camera Options */}
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">카메라 옵션</p>
              <div className="overflow-hidden rounded-lg border border-cyan-500/20">
                <table className="w-full text-xs">
                  <thead className="bg-cyan-500/10">
                    <tr>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">옵션</th>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">설명</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cyan-500/10">
                    {KLING_CAMERA_OPTIONS.map((o) => (
                      <tr key={o.option}>
                        <td className="px-3 py-1.5 text-cyan-200">{o.option}</td>
                        <td className="px-3 py-1.5 text-gray-400">{o.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Motion Score */}
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">Motion Score 가이드</p>
              <div className="overflow-hidden rounded-lg border border-cyan-500/20">
                <table className="w-full text-xs">
                  <thead className="bg-cyan-500/10">
                    <tr>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">점수</th>
                      <th className="text-left text-cyan-300 px-3 py-2 font-bold">용도</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cyan-500/10">
                    {KLING_MOTION_SCORES.map((m) => (
                      <tr key={m.score}>
                        <td className="px-3 py-1.5 text-cyan-200 font-bold">{m.score}</td>
                        <td className="px-3 py-1.5 text-gray-400">{m.usage}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
              <p className="text-cyan-300 text-xs">💡 <span className="font-bold">팁:</span> 캐릭터 일관성이 가장 좋음. 무음이므로 CapCut에서 오디오 추가</p>
            </div>
          </div>
        </ToolDetailCard>

        {/* Veo 3.1 */}
        <ToolDetailCard
          title="Veo 3.1"
          color="red"
          url="https://labs.google/fx/tools/flow"
          isOpen={openTool === "veo"}
          onToggle={() => toggleTool("veo")}
          badge="오디오 포함"
        >
          <div className="space-y-4">
            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">실행 단계 (Flow 권장)</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-red-400 font-bold">1.</span>labs.google/fx/tools/flow 접속</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">2.</span>Google 계정 로그인 (AI Pro 필요)</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">3.</span>파싱탭에서 복사한 Veo 프롬프트 붙여넣기</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">4.</span>Generate → 대사/효과음 자동 생성됨</li>
              </ol>
            </div>

            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">대안: AI Studio</p>
              <ol className="text-gray-300 text-xs space-y-1.5">
                <li className="flex gap-2"><span className="text-red-400 font-bold">1.</span>aistudio.google.com 접속</li>
                <li className="flex gap-2"><span className="text-red-400 font-bold">2.</span>왼쪽 메뉴 → "Veo" 선택</li>
              </ol>
            </div>

            <div>
              <p className="text-gray-400 text-xs font-bold mb-2">프롬프트 구조</p>
              <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 font-mono text-xs text-red-200">
                <p><span className="text-red-400">[Subject]</span> 주체 (누가)</p>
                <p><span className="text-red-400">[Action]</span> 동작 (무엇을)</p>
                <p><span className="text-red-400">[Setting]</span> 장소 (어디서)</p>
                <p><span className="text-red-400">[Style]</span> 스타일 (cinematic, etc)</p>
                <p><span className="text-red-400">[Camera]</span> 카메라 (close-up, etc)</p>
                <p><span className="text-red-400">[Lighting]</span> 조명 (dramatic, etc)</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-red-300 text-xs">💡 <span className="font-bold">팁:</span> 대사/효과음 필요한 씬에 적합. Flow는 AI 크레딧 소모</p>
            </div>
          </div>
        </ToolDetailCard>
      </ContentCard>

      {/* FAQ Section */}
      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-yellow-400">help</span>
          자주 묻는 질문
        </h3>
        <div className="space-y-2">
          {FAQ_ITEMS.map((faq) => (
            <FAQItem
              key={faq.id}
              question={faq.question}
              answer={faq.answer}
              isOpen={openFaq === faq.id}
              onToggle={() => toggleFaq(faq.id)}
            />
          ))}
        </div>
      </ContentCard>

      {/* Subscription Info */}
      <ContentCard highlight>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <span className="material-symbols-outlined text-purple-400">credit_card</span>
          구독 안내
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold text-purple-600 mb-1">Google AI Pro</p>
            <p className="text-xl font-black text-gray-900">₩14,500/월</p>
            <ul className="text-gray-600 text-xs mt-2 space-y-1">
              <li>✓ NanoBanana + Veo + Flow</li>
              <li>✓ AI 크레딧 1,000/월</li>
            </ul>
            <a
              href="https://one.google.com/ai"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-600 text-white text-xs font-bold hover:bg-purple-700 transition-colors"
            >
              구독하기
              <span className="material-symbols-outlined text-xs">open_in_new</span>
            </a>
          </div>
          <div className="p-4 rounded-xl bg-white text-gray-900">
            <p className="font-bold text-cyan-600 mb-1">Kling Pro</p>
            <p className="text-xl font-black text-gray-900">₩31,200/월</p>
            <ul className="text-gray-600 text-xs mt-2 space-y-1">
              <li>✓ 3,000cr (5초 ~60개)</li>
              <li>✓ 상업용 라이선스</li>
            </ul>
            <a
              href="https://app.klingai.com/global/membership/membership-plan"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-cyan-600 text-white text-xs font-bold hover:bg-cyan-700 transition-colors"
            >
              구독하기
              <span className="material-symbols-outlined text-xs">open_in_new</span>
            </a>
          </div>
        </div>
        <div className="mt-4 p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
          <p className="text-violet-300 text-xs">
            <span className="font-bold">Midjourney:</span> $10/월 Basic ~ $30/월 Standard (월 15~30시간)
            <a href="https://www.midjourney.com/account" target="_blank" rel="noopener noreferrer" className="ml-2 text-violet-400 underline">구독하기</a>
          </p>
        </div>
      </ContentCard>

      {/* Completion */}
      <div className="text-center py-6">
        <div className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-teal-500/20 border border-emerald-500/30 mb-4">
          <span className="material-symbols-outlined text-emerald-400">celebration</span>
          <span className="font-bold text-emerald-300 text-lg">워크플로우 완료!</span>
        </div>
        <p className="text-gray-500 text-sm mb-6">씬별로 이미지/영상을 생성한 후 CapCut에서 합치면 끝</p>
        <button
          onClick={() => setActiveTab("homework")}
          className="px-6 py-3 rounded-xl bg-white text-gray-900 font-bold hover:bg-gray-100 transition-all inline-flex items-center gap-2"
        >
          <span className="material-symbols-outlined">assignment</span>
          과제 확인하기
        </button>
      </div>
    </div>
  );
}
