---
description: Claude Code 실행자 워크플로우 (with Codex 티키타카) - Vivid 전용
---

# Claude: 시니어 실행자 워크플로우 (Vivid)

> **핵심 원칙**: Plan First, Execute Later, Verify Always
> Codex(검증자)와 티키타카하며 완벽한 실행을 목표로 함

> [!CAUTION]
> **Codex 피드백 맹신 금지**
> - Codex는 주니어 수준일 수 있음 (능력치 편차)
> - 오버코딩/과도한 추상화 제안 가능성 있음
> - 반드시 **시니어 관점에서 비판적 검토** 후 수용 여부 결정
> - 의심되면 웹서칭/문서 확인으로 재검증

---

## 1. 시작 전 체크

```bash
# 1. CLAUDE.md 확인 (프로젝트 메모리)
cat CLAUDE.md

# 2. Git 브랜치 확인/생성
git status
git checkout -b feature/[작업명]

# 3. Vivid 서버 상태 확인
/server  # 워크플로우로 서버 시작/재시작
```

---

## 2. Vivid 핵심 파일 참조

### 반드시 확인할 문서
- `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` - Dimension 앱 개발 SSoT
- `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` - 아키텍처 철학
- `30_UNIFIED_EXECUTION_ROADMAP.md` - 로드맵

### 핵심 코드 경로
| 영역 | 경로 |
|------|------|
| Dimension Tools | `backend/app/agents/dimension_tools.py` |
| Generation Pipeline | `backend/app/generation_client.py` |
| Run Token | `backend/app/routers/run_token.py` |
| RAG Suggestion | `backend/app/rag/rag_suggestion_service.py` |
| Creative Intent | `backend/app/schemas/creative_intent.py` |

---

## 3. Plan → Execute → Verify 워크플로우

### Step 1: Plan Mode (계획 먼저)

```
[Shift+Tab 두 번 = Plan Mode]

이 기능을 구현하려고 해:
[기능 설명]

먼저 계획만 세워줘. 코드는 아직 작성하지 마.
- 수정할 파일 목록
- 각 파일의 변경 내용
- 예상되는 리스크
```

### Step 2: Codex에 계획 검증 요청

```bash
# Codex 터미널에 붙여넣기
방금 Claude Code가 아래 계획을 세웠어:
[계획 붙여넣기]

오버코딩은 지양하고 실수한 것들이나 크리티컬한 것들 니가 모두 전수조사하여 답해줘 python3웹서칭과 ultrathink로 시니어 개발자처럼 think harder 최대 토큰으로 진행
```

### Step 3: 피드백 반영 후 실행

```
Codex가 이런 피드백을 줬어:
[피드백 붙여넣기]

이걸 반영해서 계획을 수정하고, 이제 코드 작성해줘.
```

### Step 4: 실행 후 검증

```
작성한 코드:
[코드 또는 파일 경로]

테스트 돌려보고 결과 알려줘.
```

---

## 4. Vivid 특수 규칙

### ⚠️ 반드시 지켜야 할 것

1. **evidence_refs는 `List[str]`만 허용**
   ```python
   # ✅ 올바름
   evidence_refs = ["db:json_generator:shot_001"]
   
   # ❌ 틀림
   evidence_refs = [{"source": "...", "ref_id": "..."}]
   ```

2. **Run-Token 흐름 표준**
   ```
   issue() → 캡슐 실행 → deduct()/refund()
   ```
   - `reserve_credits()`/`commit_credits()` 직접 호출 금지

3. **Shot/Prompt Contract 우선**
   - `IntentFactory`/`AestheticHints`로 매핑 금지
   - 상세 필드는 `ShotContract` 레벨에서 처리

4. **Sealed Capsule 원칙**
   - 프론트엔드에서 Gemini 직접 호출 금지
   - 모든 LLM 호출은 서버 캡슐 내부에서

---

## 5. Codex 티키타카용 표준 프롬프트

### Claude → Codex (검증 요청)

```
=== Codex 리뷰 요청 ===

작업: [작업 설명]
변경 파일: [파일 목록]
주요 변경: [요약]

---
[계획 또는 코드 diff]
---

오버코딩은 지양하고 실수한 것들이나 크리티컬한 것들 니가 모두 전수조사하여 답해줘 python3웹서칭과 ultrathink로 시니어 개발자처럼 think harder 최대 토큰으로 진행
```

### Codex → Claude (피드백 반영)

```
Codex 피드백:
1. 🔴 P0: [즉시 수정 필요]
2. 🟠 P1: [권장 수정]
3. 🟢 P2: [향후 개선]

위 피드백 반영해서 코드 수정해줘.
```

---

## 6. 자주 쓰는 명령

| 상황 | 프롬프트 |
|:-----|:---------|
| 계획 모드 | `먼저 계획만 세워줘. 코드는 작성하지 마.` |
| 실행 모드 | `계획대로 코드 작성해줘.` |
| 테스트 | `테스트 돌려보고 결과 알려줘.` |
| Git 커밋 | `변경사항 커밋해줘. 메시지는 conventional commit 형식으로.` |
| 서버 재시작 | `/server` |
| 되돌리기 | `방금 변경 취소하고 원래대로 돌려줘.` |

---

## 7. 티키타카 플로우 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                     Complete Tikitaka Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     Plan      ┌──────────────┐                │
│  │ Claude Code  │──────────────▶│    Codex     │                │
│  │   (실행자)    │               │   (검증자)    │                │
│  └──────────────┘               └──────────────┘                │
│         │                              │                         │
│         │         Feedback             │                         │
│         │◀─────────────────────────────│                         │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐     Code      ┌──────────────┐                │
│  │ Claude Code  │──────────────▶│    Codex     │                │
│  │   Execute    │               │   Review     │                │
│  └──────────────┘               └──────────────┘                │
│         │                              │                         │
│         │         Issues               │                         │
│         │◀─────────────────────────────│                         │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐    Final      ┌──────────────┐                │
│  │ Claude Code  │──────────────▶│    Codex     │                │
│  │   Fix & Test │               │   Approve ✅  │                │
│  └──────────────┘               └──────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Error 발생 시

```
이 에러 발생했어:
[에러 메시지]

1. 원인 분석해줘
2. 수정 방법 제안해줘
3. 근본적인 해결책도 알려줘

(필요하면 Codex에게 python3웹서칭 요청할게)
```

---

## 9. 일일 마무리 루틴

```bash
# 1. 변경사항 요약
git diff --stat

# 2. 커밋
git add -A && git commit -m "feat: [작업 요약]"

# 3. Codex 최종 검토 요청
오늘 전체 작업 전수조사해줘 (Codex 터미널)
```

---

## 10. CLAUDE.md 필수 내용

```markdown
# Project: Vivid

## Stack
- Backend: FastAPI + PostgreSQL + pgvector
- Frontend: Next.js 15 + TypeScript

## Commands
- `/server` - 백엔드/프론트엔드 서버 시작
- `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8100`
- `cd frontend && npm run dev`

## Key Files
- `backend/app/generation_client.py` - Shot/Prompt Contract
- `backend/app/agents/dimension_tools.py` - Dimension Tools
- `backend/app/routers/run_token.py` - Run Token
- `backend/app/rag/rag_suggestion_service.py` - RAG

## Warnings
- ⚠️ `evidence_refs` → `List[str]` only
- ⚠️ IntentFactory/AestheticHints 매핑 금지 → ShotContract 사용
- ⚠️ Run-Token 흐름: issue → execute → deduct/refund
```

---

> **2026 Best Practice**: Claude Code는 실행에 집중, 검증은 Codex에게 위임.
> 한 명이 두 역할 하면 Yes-Man 문제 발생. 반드시 분리!
