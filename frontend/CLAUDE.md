# Frontend CLAUDE.md

> **Prompty.co.kr** - Dual AI 티키타카 워크플로우 가이드 플랫폼
> Next.js 16 + React 19 + TypeScript

---

## Quick Commands

```bash
npm run dev      # localhost:3100
npm run build    # 프로덕션 빌드
npm run lint     # 린트
```

---

## 핵심 철학

```
Gemini CLI (영상 @언급) ←→ Claude Antigravity
         │                         │
         └───── projects/{name}/ ──────┘
                      ↓
               STATE.md (공유 상태)
```

- **NOT**: AI가 대신 호출/생성
- **YES**: Dual AI 티키타카의 "길잡이" + Critique 기록 추적

---

## Prompty 디렉토리 구조

```
src/
├── app/                            # Prompty 라우트 (루트 레벨)
│   ├── page.tsx                    # 랜딩/대시보드
│   ├── templates/                  # 템플릿 목록/상세
│   ├── projects/                   # 프로젝트 가이드
│   │   └── [id]/
│   │       ├── page.tsx            # 워크플로우 가이드
│   │       └── critique/page.tsx   # Critique 입력
│   └── community/                  # 커뮤니티
├── components/prompty/             # Prompty UI 컴포넌트
│   ├── CopyPromptButton.tsx        # 프롬프트 복사
│   ├── GuideWorkflow.tsx           # 4-Stage 진행바
│   ├── CritiqueChecklist.tsx       # 평가 체크리스트
│   └── ExternalToolLinks.tsx       # 외부 도구 링크
└── lib/api.ts                      # API 클라이언트
```

---

## 4-Stage 워크플로우

| Stage | 도구 | 출력 |
|-------|------|------|
| ANALYZE | Gemini CLI | ANALYSIS.md, PROFILES.md |
| IMAGE | NanoBanana, MJ | ANCHOR + 씬 이미지 |
| VIDEO | Kling, Veo | Image-to-Video |
| ASSEMBLY | CapCut | 최종 편집 |

---

## Critique 판정 기준

```
PASS   (85+)   → 다음 단계
REVISE (60-84) → 수정 후 재생성 (티키타카)
REJECT (<60)   → 프롬프트 재검토
```

---

## 컴포넌트 사용 예시

```tsx
import { 
  CopyPromptButton, 
  GuideWorkflow, 
  CritiqueChecklist 
} from '@/components/prompty';

// 프롬프트 복사
<CopyPromptButton 
  promptText={step.prompt_text} 
  onCopy={handleCopyAnalytics} 
/>

// 4-Stage 진행바
<GuideWorkflow 
  stages={guide.stages}
  currentStage="stage2"
  progressPercent={60}
/>

// Critique 체크리스트
<CritiqueChecklist
  items={template.critique_config.items}
  scores={scores}
  onScoreChange={handleScore}
  passingScore={85}
/>
```

---

## API 클라이언트

```typescript
import { api } from '@/lib/api';

// 템플릿 목록
const templates = await api.getPromptyTemplates();

// 프로젝트 Guide
const guide = await api.getPromptyGuide(projectId);

// Critique 제출
await api.submitPromptyCritique(projectId, stage, stepId, scores);

// 액션 로그
await api.logPromptyAction(projectId, 'copy_prompt', stage, step);
```

---

## 환경 변수

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8100
```

---

## SSoT 참조

```
viral-video-automation/templates/
├── CRITIQUE_IMAGE.md    # 이미지 평가 기준
├── CRITIQUE_VIDEO.md    # 영상 평가 기준
├── CRITIQUE_SELFLOOP.md # Self-Loop 흐름
└── MODE_TIKITAKA.md     # 티키타카 UX
```
