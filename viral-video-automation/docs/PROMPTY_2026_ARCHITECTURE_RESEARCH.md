# 🏛️ PROMPTY.CO.KR 2026 Architecture Research Report

> **Purpose**: 티키타카 학습 플랫폼을 위한 2026 아키텍처 & 백엔드 전략
> **Target**: prompty.co.kr - AI 창작 워크플로우 길잡이 플랫폼
> **Date**: 2026-02-02
> **Research Scope**: 웹서칭 기반 2026 트렌드 분석

---

## 📋 Executive Summary

### 핵심 목표
```
수강생들이 Dual AI (Gemini CLI + Claude Code) 티키타카를 수행할 때,
prompty.co.kr이 "길잡이"로서 효율성과 퀄리티를 높이는 UX 경험 제공
```

### 2026 키워드
| 트렌드 | 적용 방향 |
|--------|----------|
| **Agentic AI Orchestration** | 티키타카 단계별 가이드 자동화 |
| **CRDT + Local-First** | 실시간 협업, 오프라인 지원 |
| **Edge Computing** | 저지연 프롬프트 제안 |
| **Human-in-the-Loop** | 최종 결정은 사용자 |
| **Creator Economy** | 프롬프트 템플릿 마켓플레이스 |

---

## 🎯 PART 1: 플랫폼 비전

### 1.1 prompty.co.kr의 역할 정의

```
┌─────────────────────────────────────────────────────────────┐
│                    PROMPTY.CO.KR 역할                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ❌ AI를 대신 호출하는 플랫폼 (API 비용 부담)                 │
│   ❌ 결과물을 생성해주는 자동화 (품질 한계)                    │
│                                                              │
│   ✅ 티키타카 워크플로우 "가이드" 플랫폼                       │
│   ✅ 프롬프트 템플릿 + 상태 관리 + 품질 평가 길잡이            │
│   ✅ 학습자가 직접 AI와 대화 (Gemini/Claude)하는 것을 보조     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 핵심 가치 제안

| 기존 문제 | prompty 해결책 |
|----------|----------------|
| "어떤 프롬프트를 써야 할지 모르겠어" | 단계별 템플릿 + 가이드 |
| "지금 어디까지 했더라?" | 실시간 진행 상태 추적 |
| "이 결과물이 좋은 건가?" | Critique 체크리스트 + 자동 점수화 |
| "다른 사람은 어떻게 했지?" | 커뮤니티 템플릿 공유 |

---

## 🏗️ PART 2: 2026 아키텍처 설계

### 2.1 Reference: 2026 AI Orchestration Best Practices

> "An orchestration layer sits around the LLM/agent, gives the agent context (historical external state, tool catalog), and manages access to systems and tools. It also ensures human approval workflows and handles audit and logging."
> — [The New Stack: Choosing Your AI Orchestration Stack for 2026](https://thenewstack.io/choosing-your-ai-orchestration-stack-for-2026/)

### 2.2 prompty 아키텍처 (Orchestration Layer 패턴)

```
┌─────────────────────────────────────────────────────────────┐
│                    PROMPTY ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATION LAYER (prompty)            │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │  Template  │ │   State    │ │  Critique  │       │   │
│  │  │  Manager   │ │  Tracker   │ │  Scorer    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘       │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐       │   │
│  │  │  Workflow  │ │  Context   │ │ Community  │       │   │
│  │  │   Guide    │ │  Provider  │ │   Share    │       │   │
│  │  └────────────┘ └────────────┘ └────────────┘       │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│                           ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                USER'S LOCAL FOLDER                    │   │
│  │        (viral-video-automation/projects/)             │   │
│  │                                                       │   │
│  │   STATE.md   ANALYSIS.md   IMAGE_PROMPTS.md          │   │
│  │      ↑            ↑              ↑                    │   │
│  │      │            │              │                    │   │
│  │   [Claude]     [Gemini]      [Claude]                │   │
│  │   Code          CLI          Code                     │   │
│  │                                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 기술 스택 선정 (2026 Best Practices 기반)

| Layer | 기술 | 선정 이유 |
|-------|------|----------|
| **Frontend** | Next.js 16 + React 19 | Server Components, Streaming |
| **State Sync** | **Yjs (CRDT)** | Local-first, 오프라인 지원, 실시간 협업 |
| **Backend** | Edge Functions (Cloudflare Workers) | 저지연, 글로벌 배포 |
| **DB** | Cloudflare D1 + R2 | Edge-native, 비용 효율 |
| **Auth** | Clerk / Auth.js | OAuth 간편 연동 |
| **Real-time** | Yjs + WebSocket | CRDT 기반 동기화 |

> "Yjs is a high-performance CRDT for building collaborative applications that sync automatically. With over 900k weekly downloads, used by Proton Docs, NextCloud, Shopify, and many others."
> — [Yjs Documentation](https://docs.yjs.dev/)

---

## 🔄 PART 3: 핵심 기능 설계

### 3.1 Workflow Guide (워크플로우 가이드)

> "Old-school onboarding with tooltips, checklists, and endless tutorials is fading—only 4 out of 10 AI tools still use them. Most now focus on embedded experiences."
> — [UserGuiding: How Top AI Tools Onboard New Users in 2026](https://userguiding.com/blog/how-top-ai-tools-onboard-new-users)

#### UX 원칙: "Embedded Experience"

```
❌ 별도 튜토리얼 페이지
❌ 팝업 가이드
❌ 긴 설명서

✅ 워크플로우 자체가 가이드
✅ 컨텍스트에 맞는 "다음 단계" 제안
✅ 진행하면서 자연스럽게 학습
```

#### Workflow Guide 화면 구조

```
┌─────────────────────────────────────────────────────────────┐
│  🎬 umbrella-parody                              [Stage 2]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ PROGRESS         │  │ CURRENT STEP                      │ │
│  │                  │  │                                   │ │
│  │ ✅ Analysis      │  │ 📸 ANCHOR_GIRL 생성                │ │
│  │ ◉ Image Gen     │  │                                   │ │
│  │   ├─ ANCHOR_GIRL │  │ [📋 Copy Prompt]                  │ │
│  │   ├─ ANCHOR_BOY  │  │                                   │ │
│  │   └─ Scenes...   │  │ Close-up portrait of a beautiful  │ │
│  │ ○ Video Gen     │  │ Korean::2 female high school...   │ │
│  │ ○ Assembly      │  │                                   │ │
│  │                  │  │ [Open Midjourney →]               │ │
│  └──────────────────┘  │                                   │ │
│                        │ ─────────────────────────────────  │ │
│                        │ 💡 TIP: MJ V7에서 --cw 80 필수!    │ │
│                        └──────────────────────────────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │ ✅ 완료 후: [결과 이미지 업로드] → 자동 Critique          ││
│  └──────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 3.2 State Tracker (상태 추적기)

> "State Synchronization ensures that all user actions and changes are accurately synchronized and instantly propagated."
> — [Palos Publishing: Architecture for Real-Time Collaboration Tools](https://palospublishing.com/architecture-for-real-time-collaboration-tools/)

#### Yjs CRDT 기반 상태 동기화

```typescript
// 상태 구조 (Yjs Y.Map 기반)
interface ProjectState {
  stages: {
    analysis: { status: 'pending' | 'done', files: string[] },
    image: {
      anchor_girl: { status: 'pending' | 'in_progress' | 'done', version: number },
      anchor_boy: { status: 'pending' | 'in_progress' | 'done', version: number },
      scenes: { [key: string]: SceneStatus }
    },
    video: { ... },
    assembly: { ... }
  },
  currentStep: string,
  lastActivity: timestamp
}

// Local-first: 오프라인에서도 작업, 온라인 시 자동 동기화
const ydoc = new Y.Doc()
const projectState = ydoc.getMap('projectState')

// WebSocket provider for real-time sync
const provider = new WebsocketProvider('wss://prompty.co.kr/sync', projectId, ydoc)
```

#### 상태 → Markdown 양방향 동기화

```
┌────────────────────┐        ┌────────────────────┐
│   prompty.co.kr    │        │   Local Folder     │
│   (Yjs State)      │ ←────→ │   (STATE.md)       │
└────────────────────┘        └────────────────────┘
        ↑                              ↑
        │    File Watch + Parse        │
        └──────────────────────────────┘
```

**구현 방식:**
1. 사용자가 로컬에서 STATE.md 수정 → prompty가 변경 감지
2. prompty에서 진행 업데이트 → STATE.md 자동 갱신
3. **충돌 해결**: CRDT가 자동 병합 (Yjs의 강점)

### 3.3 Critique Scorer (품질 평가기)

#### 자동 평가 체크리스트 UI

```
┌─────────────────────────────────────────────────────────────┐
│  📊 CRITIQUE: ANCHOR_GIRL                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [이미지 미리보기]                                            │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  ▼ 프롬프트 준수                                             │
│    ☑ 한국인 여고생 표현됨                          +20       │
│    ☑ 긴 웨이브 머리                                +15       │
│    ☑ 투명 우산 핸들 보임                           +10       │
│    ☐ 네이비 리본 타이 불분명                       -10       │
│                                                              │
│  ▼ 캐릭터 일관성                                             │
│    ☑ 한국인 피부톤                                 +15       │
│    ☑ 홑꺼풀 눈                                     +15       │
│    ☐ 서양인 코 형태 의심                           -5        │
│                                                              │
│  ▼ 기술적 품질                                               │
│    ☑ 해상도 충분                                   +10       │
│    ☑ 아티팩트 없음                                 +10       │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  SCORE: 80/100                                               │
│  VERDICT: 🔄 REVISE                                          │
│                                                              │
│  💡 개선 제안:                                               │
│  • --no double eyelids 추가                                  │
│  • 네이비 리본 타이 더 강조 ("navy blue ribbon tie")          │
│                                                              │
│  [📋 개선된 프롬프트 복사]  [✅ 그냥 PASS]  [❌ REJECT]       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Template Marketplace (템플릿 마켓플레이스)

> "The 'AI whispering' economy is emerging, and platforms like PromptBase are at its center."
> — [Skywork AI: PromptBase Deep Dive](https://skywork.ai/skypage/en/PromptBase-Deep-Dive-Mastering-the-AI-Prompt-Marketplace-for-Future-Growth-and-SEO-Dominance/1972861300479422464)

#### Creator Economy 모델 적용

```
┌─────────────────────────────────────────────────────────────┐
│  🛒 TEMPLATE MARKETPLACE                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 🌧️ Rainy    │  │ 🎂 Birthday │  │ 📱 K-Drama  │         │
│  │ Romance     │  │ Party       │  │ Moment      │         │
│  │             │  │             │  │             │         │
│  │ by @creator │  │ by @ted     │  │ by @academy │         │
│  │ ★★★★☆ (47) │  │ ★★★★★ (128)│  │ ★★★★☆ (89) │         │
│  │             │  │             │  │             │         │
│  │ [사용하기]   │  │ [사용하기]   │  │ [사용하기]   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
│  📊 템플릿 포함 내용:                                        │
│  • ANALYSIS.md (분석 프롬프트)                               │
│  • IMAGE_PROMPTS.md (이미지 프롬프트)                        │
│  • MOTION_PROMPTS.md (모션 프롬프트)                         │
│  • COLOR_KEY 프리셋                                          │
│  • CRITIQUE 체크리스트                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 비즈니스 모델

| 모델 | 설명 | 수익 분배 |
|------|------|----------|
| **Free Tier** | 기본 템플릿 무료 사용 | - |
| **Pro Templates** | 고급 템플릿 유료 구매 | Creator 70%, Platform 30% |
| **Academy Bundle** | 아카데미 수강생 전용 | 구독료 포함 |
| **Custom Template** | 의뢰 제작 | 협의 |

> "Creators share a common goal of building a digital audience and monetizing their work. The digital products market is valued at $10B."
> — [Digital Collective: The Creator Economy in 2026](https://digitalcollective.media/p/the-creator-economy-in-2026-20-trends)

---

## 🔧 PART 4: 백엔드 아키텍처

### 4.1 Edge-First Architecture

> "Providers like Cloudflare Workers and AWS Lambda@Edge push compute close to users, enabling ultra-low-latency workloads."
> — [American Chase: Future of Serverless Computing 2026](https://americanchase.com/future-of-serverless-computing/)

```
┌─────────────────────────────────────────────────────────────┐
│                   EDGE-FIRST BACKEND                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User (Seoul) ──→ [CF Edge Seoul] ──→ [D1 Database]         │
│                         │                                    │
│                         ├── Template API (Edge Function)     │
│                         ├── State Sync (Durable Objects)     │
│                         └── File Storage (R2)                │
│                                                              │
│  User (Tokyo) ──→ [CF Edge Tokyo] ──→ [D1 Database]         │
│                         │                                    │
│                         └── (Same services, local edge)      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 API 설계

```typescript
// Cloudflare Workers API Routes

// 1. Project Management
POST   /api/projects                    // 새 프로젝트 생성
GET    /api/projects/:id                // 프로젝트 조회
PUT    /api/projects/:id/state          // 상태 업데이트
DELETE /api/projects/:id                // 프로젝트 삭제

// 2. Template Marketplace
GET    /api/templates                   // 템플릿 목록
GET    /api/templates/:id               // 템플릿 상세
POST   /api/templates                   // 템플릿 등록 (creator)
POST   /api/templates/:id/use           // 템플릿 사용 → 프로젝트 생성

// 3. Critique
POST   /api/critique/image              // 이미지 평가 요청
POST   /api/critique/video              // 비디오 평가 요청
GET    /api/critique/:id                // 평가 결과 조회

// 4. Real-time Sync (WebSocket)
WS     /sync/:projectId                 // Yjs CRDT 동기화
```

### 4.3 데이터 스키마 (D1 SQLite)

```sql
-- 사용자
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE,
  name TEXT,
  role TEXT DEFAULT 'student', -- 'student' | 'creator' | 'admin'
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 프로젝트
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  name TEXT NOT NULL,
  template_id TEXT REFERENCES templates(id),
  state_json TEXT, -- Yjs state snapshot
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 템플릿
CREATE TABLE templates (
  id TEXT PRIMARY KEY,
  creator_id TEXT REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  category TEXT,
  content_json TEXT, -- 프롬프트들 JSON
  price INTEGER DEFAULT 0, -- 0 = free
  downloads INTEGER DEFAULT 0,
  rating REAL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Critique 기록
CREATE TABLE critiques (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES projects(id),
  scene_id TEXT,
  type TEXT, -- 'image' | 'video'
  score INTEGER,
  verdict TEXT, -- 'PASS' | 'REVISE' | 'REJECT'
  checklist_json TEXT,
  suggestions TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 Yjs 동기화 서버 (Durable Objects)

> "Yjs is network agnostic, supports offline editing, version snapshots, undo/redo and shared cursors."
> — [Yjs GitHub](https://github.com/yjs/yjs)

```typescript
// Cloudflare Durable Object for Yjs sync
export class YjsSyncServer {
  private ydoc: Y.Doc
  private conns: Set<WebSocket>

  constructor(state: DurableObjectState) {
    this.ydoc = new Y.Doc()
    this.conns = new Set()

    // Load persisted state
    state.blockConcurrencyWhile(async () => {
      const stored = await state.storage.get('ydoc')
      if (stored) {
        Y.applyUpdate(this.ydoc, stored as Uint8Array)
      }
    })
  }

  async fetch(request: Request) {
    const upgradeHeader = request.headers.get('Upgrade')
    if (upgradeHeader === 'websocket') {
      const pair = new WebSocketPair()
      this.handleSession(pair[1])
      return new Response(null, { status: 101, webSocket: pair[0] })
    }
    return new Response('Expected WebSocket', { status: 426 })
  }

  handleSession(ws: WebSocket) {
    ws.accept()
    this.conns.add(ws)

    // Send current state
    ws.send(Y.encodeStateAsUpdate(this.ydoc))

    ws.addEventListener('message', (event) => {
      const update = new Uint8Array(event.data as ArrayBuffer)
      Y.applyUpdate(this.ydoc, update)

      // Broadcast to other connections
      for (const conn of this.conns) {
        if (conn !== ws) conn.send(update)
      }
    })

    ws.addEventListener('close', () => this.conns.delete(ws))
  }
}
```

---

## 📱 PART 5: UX/UI 설계 원칙

### 5.1 2026 AI Tool Onboarding Best Practices

> "Let people experience the product's magic first, and they'll stick around. Perplexity gives new users example prompts right away, so they see value in seconds without reading a guide."
> — [UserGuiding: How Top AI Tools Onboard New Users](https://userguiding.com/blog/how-top-ai-tools-onboard-new-users)

#### 적용: First-Time User Experience

```
┌─────────────────────────────────────────────────────────────┐
│  👋 prompty에 오신 것을 환영합니다!                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  바로 시작하세요:                                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  🌧️ "우산 로맨스" 템플릿으로 시작하기                    │ │
│  │                                                         │ │
│  │  비 오는 날 우연히 만난 두 사람의 짧은 이야기를          │ │
│  │  AI와 함께 영상으로 만들어보세요.                        │ │
│  │                                                         │ │
│  │  [🚀 바로 시작] ← 클릭 한 번으로 프로젝트 생성           │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  또는:                                                       │
│  • 📹 내 영상으로 새 프로젝트 만들기                         │
│  • 🛒 템플릿 마켓플레이스 둘러보기                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Progressive Disclosure (점진적 공개)

> "Don't automate everything. Users want control, not surrender. Provide AI assistance, not AI takeover."
> — [Orbix: 10 AI-Driven UX Patterns Transforming SaaS in 2026](https://www.orbix.studio/blogs/ai-driven-ux-patterns-saas-2026)

```
Level 1: 기본 (초보자)
├── 단계별 가이드 표시
├── 프롬프트 자동 복사 버튼
└── 간단한 PASS/REVISE 선택

Level 2: 중급 (숙련자)
├── 가이드 숨기기 옵션
├── 프롬프트 직접 편집
└── Critique 상세 점수 확인

Level 3: 고급 (크리에이터)
├── 템플릿 제작/판매
├── Custom Critique 기준
└── API 연동
```

### 5.3 Contextual AI Assistance

```
┌─────────────────────────────────────────────────────────────┐
│  "ANCHOR_GIRL 프롬프트를 수정하고 싶어요"                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  💡 AI 어시스턴트:                                           │
│                                                              │
│  현재 프롬프트에서 수정 가능한 부분:                         │
│                                                              │
│  1. 얼굴 특징 강화                                           │
│     "single eyelids" → "monolid eyes, Korean features"       │
│     [적용]                                                   │
│                                                              │
│  2. 표정 변경                                                │
│     "confused and annoyed" → [다른 표정 선택 ▼]              │
│     • surprised and curious                                  │
│     • cold and indifferent                                   │
│     • amused and intrigued                                   │
│                                                              │
│  3. 조명 조절                                                │
│     "Soft diffused natural light" → [조명 프리셋 ▼]          │
│                                                              │
│  [전체 프롬프트 보기]  [Claude에게 물어보기]                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 PART 6: 기술 스택 상세

### 6.1 Frontend Stack

```typescript
// package.json (핵심 의존성)
{
  "dependencies": {
    "next": "^16.0.0",
    "react": "^19.0.0",
    "yjs": "^13.6.0",
    "y-websocket": "^2.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^5.0.0",
    "framer-motion": "^11.0.0",
    "tailwindcss": "^4.0.0"
  }
}
```

### 6.2 State Management (Yjs + Zustand)

```typescript
// stores/projectStore.ts
import { create } from 'zustand'
import * as Y from 'yjs'
import { WebsocketProvider } from 'y-websocket'

interface ProjectStore {
  ydoc: Y.Doc | null
  state: ProjectState | null
  connect: (projectId: string) => void
  updateStep: (stepId: string, status: StepStatus) => void
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  ydoc: null,
  state: null,

  connect: (projectId) => {
    const ydoc = new Y.Doc()
    const provider = new WebsocketProvider(
      'wss://prompty.co.kr/sync',
      projectId,
      ydoc
    )

    const stateMap = ydoc.getMap('state')
    stateMap.observe(() => {
      set({ state: stateMap.toJSON() as ProjectState })
    })

    set({ ydoc })
  },

  updateStep: (stepId, status) => {
    const { ydoc } = get()
    if (!ydoc) return

    const stateMap = ydoc.getMap('state')
    stateMap.set(`steps.${stepId}`, status)
  }
}))
```

### 6.3 Backend Stack (Cloudflare)

```
wrangler.toml
─────────────────────────────────────
name = "prompty-api"
main = "src/index.ts"
compatibility_date = "2026-01-15"

[[d1_databases]]
binding = "DB"
database_name = "prompty-db"
database_id = "xxx"

[[r2_buckets]]
binding = "STORAGE"
bucket_name = "prompty-files"

[[durable_objects.bindings]]
name = "SYNC_SERVER"
class_name = "YjsSyncServer"
```

### 6.4 비용 추정 (월간)

| 서비스 | 예상 사용량 | 비용 |
|--------|------------|------|
| Cloudflare Workers | 10M requests | $5 |
| D1 Database | 5GB | $0.75 |
| R2 Storage | 50GB | $0.75 |
| Durable Objects | 100K requests | $0.15 |
| **Total** | | **~$7/월** |

> "Serverless and FaaS is inherently greener and more cost-effective than running persistent virtual machines."
> — [Middleware: Serverless Architecture in 2026](https://middleware.io/blog/serverless-architecture/)

---

## 🚀 PART 7: 구현 로드맵

### Phase 1: MVP (2주)

```
Week 1:
├── Cloudflare Workers 설정
├── D1 Database 스키마
├── 기본 API 구현
└── Yjs 동기화 서버

Week 2:
├── Next.js 프로젝트 설정
├── Workflow Guide UI
├── State Tracker (로컬 상태)
└── 템플릿 1개 (umbrella-parody)
```

**MVP 목표**:
- 수강생이 prompty.co.kr에서 "우산 로맨스" 템플릿으로 프로젝트 시작
- 단계별 가이드 따라 Gemini/Claude 티키타카 수행
- STATE.md 연동 없이 웹 UI만으로 진행 추적

### Phase 2: Core Features (4주)

```
Week 3-4:
├── STATE.md 양방향 동기화
├── Critique Scorer UI
├── 이미지 업로드 + 미리보기
└── 진행률 대시보드

Week 5-6:
├── Template Marketplace
├── Creator 등록 시스템
├── 결제 연동 (Stripe)
└── 커뮤니티 기능 (댓글, 평점)
```

### Phase 3: Scale (4주)

```
Week 7-8:
├── 멀티 프로젝트 관리
├── 협업 기능 (팀 프로젝트)
├── 버전 히스토리
└── 분석 대시보드

Week 9-10:
├── 모바일 최적화
├── 오프라인 지원 강화
├── API 공개 (크리에이터용)
└── 아카데미 어드민 패널
```

---

## 📚 PART 8: 참고 자료

### Architecture & Best Practices
- [The New Stack: Choosing Your AI Orchestration Stack for 2026](https://thenewstack.io/choosing-your-ai-orchestration-stack-for-2026/)
- [Vellum: The 2026 Guide to AI Agent Workflows](https://www.vellum.ai/blog/agentic-workflows-emerging-architectures-and-design-patterns)
- [Hatchworks: AI Orchestration Unleashed](https://hatchworks.com/blog/gen-ai/ai-orchestration/)

### Real-Time Collaboration
- [Yjs Documentation](https://docs.yjs.dev/)
- [Yjs GitHub](https://github.com/yjs/yjs)
- [Velt: Best CRDT Libraries 2025](https://velt.dev/blog/best-crdt-libraries-real-time-data-sync)
- [Palos Publishing: Architecture for Real-Time Collaboration](https://palospublishing.com/architecture-for-real-time-collaboration-tools/)

### UX/UI Design Patterns
- [Orbix: 10 AI-Driven UX Patterns Transforming SaaS in 2026](https://www.orbix.studio/blogs/ai-driven-ux-patterns-saas-2026)
- [UserGuiding: How Top AI Tools Onboard New Users in 2026](https://userguiding.com/blog/how-top-ai-tools-onboard-new-users)
- [Whatfix: 17 Best Onboarding Flow Examples](https://whatfix.com/blog/user-onboarding-examples/)

### Serverless & Edge
- [American Chase: Future of Serverless Computing 2026](https://americanchase.com/future-of-serverless-computing/)
- [Vasundhara: Best Serverless Architecture for AI Apps](https://www.vasundhara.io/blogs/best-serverless-architecture-for-cloud-based-ai-apps)
- [Xaylonlabs: Top Software Architecture Trends for 2026](https://medium.com/@xaylonlabs/top-software-architecture-trends-for-2026-ai-edge-computing-and-the-rise-of-the-autonomous-81a2554fe9fd)

### Creator Economy & Marketplace
- [Digital Collective: The Creator Economy in 2026](https://digitalcollective.media/p/the-creator-economy-in-2026-20-trends)
- [Skywork AI: PromptBase Deep Dive](https://skywork.ai/skypage/en/PromptBase-Deep-Dive-Mastering-the-AI-Prompt-Marketplace-for-Future-Growth-and-SEO-Dominance/1972861300479422464)
- [Maxim AI: Top 5 AI Prompt Management Tools in 2026](https://www.getmaxim.ai/articles/top-5-ai-prompt-management-tools-in-2026/)

### Prompt Management
- [Langfuse: Open-source LLM Engineering](https://langfuse.com/)
- [Braintrust: Prompt Versioning](https://braintrustdata.com/)

---

## ✅ 결론

### prompty.co.kr 핵심 포지셔닝

```
"AI를 대신 호출하는 플랫폼" ❌
"AI 티키타카의 길잡이 플랫폼" ✅
```

### 2026 아키텍처 핵심

| 원칙 | 구현 |
|------|------|
| **Orchestration Layer** | 템플릿 + 상태 + Critique 통합 관리 |
| **Local-First** | Yjs CRDT, 오프라인 지원 |
| **Edge Computing** | Cloudflare Workers, 저지연 |
| **Human-in-the-Loop** | 가이드 제공, 최종 결정은 사용자 |
| **Creator Economy** | 템플릿 마켓플레이스, 수익 분배 |

### 차별화 포인트

1. **Dual AI Folder Sync와의 통합**
   - 로컬 STATE.md ↔ prompty 양방향 동기화
   - Gemini CLI + Claude Code 협업 지원

2. **교육 특화 UX**
   - 단계별 가이드, 자연스러운 학습 흐름
   - Critique 기반 품질 보장

3. **크리에이터 생태계**
   - 템플릿 제작/판매
   - 아카데미 수료생 → 크리에이터 전환

---

> **Prepared by**: Claude Code Analysis
> **Research Method**: 2026 Web Search
> **Status**: READY FOR IMPLEMENTATION
