"use client";

import { useState } from "react";
import { PageHeader, ContentCard } from "./shared";

// 강의별 과제 데이터
const homeworkData = {
  "1강": {
    date: "2026년 1월 30일 (목)",
    tasks: [
      {
        title: "1. Crebit AI Studio 회원가입",
        items: ["• prompty.co.kr 접속", "• Google 계정으로 로그인"],
      },
      {
        title: "2. 디스코드 가입",
        items: ["• 초대 링크로 서버 입장", "• 닉네임 설정 (실명 권장)"],
      },
    ],
    submission: {
      channel: "📤 디스코드 #과제제출 채널에 '완료' 댓글",
      items: [],
    },
  },
  "2강": {
    date: "2026년 2월 6일 (목)",
    tasks: [
      {
        title: "1. 이미지 프롬프트 생성기 완료",
        items: ["• 본인이 선정한 바이럴 영상 분석", "• 결과물(.md) 저장"],
      },
      {
        title: "2. 바이브 철학관 세션",
        items: ["• 최소 50% 깊이 도달", "• 프로필(.json) 다운로드"],
      },
      {
        title: "3. Google 계정 준비",
        items: ["• 최소 3개 계정 생성", "• 하나의 핸드폰 번호로 5개까지 가능"],
        highlight: "3개",
      },
    ],
    submission: {
      channel: "📤 디스코드 #과제제출 채널에 업로드",
      items: ["• 이미지 프롬프트 생성기 결과물 (.md)"],
      note: "※ 바이브 철학관 프로필은 개인정보이므로 제출하지 않습니다",
    },
  },
  "3강": {
    date: "2026년 2월 13일 (목)",
    tasks: [
      {
        title: "1. 비디오 프롬프트 생성 완료",
        items: ["• 이미지 프롬프트 기반 비디오 프롬프트 생성", "• 결과물(.md) 저장"],
      },
      {
        title: "2. Veo3 영상 생성 (1개 이상)",
        items: ["• 생성된 프롬프트로 Veo3 실행", "• 결과 영상 저장"],
      },
    ],
    submission: {
      channel: "📤 디스코드 #과제제출 채널에 업로드",
      items: ["• 비디오 프롬프트 결과물 (.md)", "• Veo3 생성 영상 (1개 이상)"],
    },
  },
};

type LectureKey = keyof typeof homeworkData;

export function HomeworkContent() {
  const [selectedLecture, setSelectedLecture] = useState<LectureKey>("3강");
  const data = homeworkData[selectedLecture];

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <PageHeader title="과제 안내" sub={`📅 ${selectedLecture} 예정: ${data.date}`} />

      {/* 강의 탭 */}
      <div className="flex items-center gap-2 bg-white/5 rounded-xl p-1.5">
        {(Object.keys(homeworkData) as LectureKey[]).map((key) => (
          <button
            key={key}
            onClick={() => setSelectedLecture(key)}
            className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${selectedLecture === key
                ? "bg-purple-500 text-white"
                : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
          >
            {key}
          </button>
        ))}
      </div>

      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">필수 과제</h3>
        <div className="space-y-4">
          {data.tasks.map((task, i) => (
            <div key={i} className="p-4 rounded-xl bg-white text-gray-900">
              <p className="font-bold mb-2">{task.title}</p>
              <ul className="text-gray-600 text-sm space-y-1">
                {task.items.map((item, j) => (
                  <li key={j}>
                    {"highlight" in task && task.highlight && item.includes(task.highlight) ? (
                      <>
                        {item.split(task.highlight)[0]}
                        <span className="font-bold text-purple-600">{task.highlight}</span>
                        {item.split(task.highlight)[1]}
                      </>
                    ) : (
                      item
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </ContentCard>

      <ContentCard>
        <h3 className="text-lg font-bold text-white mb-4">제출 방법</h3>
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-emerald-300 font-medium mb-2">{data.submission.channel}</p>
          {data.submission.items.length > 0 && (
            <ul className="text-emerald-200/70 text-sm space-y-1">
              {data.submission.items.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          )}
        </div>
        {"note" in data.submission && data.submission.note && (
          <p className="text-gray-500 text-xs mt-3">{data.submission.note}</p>
        )}
      </ContentCard>
    </div>
  );
}
