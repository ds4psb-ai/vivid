# 📋 Project Design Record (PDR)

> **Purpose**: 주요 설계 결정 및 그 이유 기록
> **Project**: Viral Video Automation
> **Version**: 2.0 (Tiki-Taka Edition)
> **Last Updated**: 2026-02-02

---

## 📌 PDR-001: Tiki-Taka vs One-Shot 듀얼 모드

### 결정
두 가지 워크플로우 모드 지원: ONE-SHOT (빠른) / TIKI-TAKA (품질)

### 배경
- 초기에는 ONE-SHOT만 존재
- 품질 문제 발생 시 어디서 수정해야 할지 불명확

### 근거
- **상황별 최적화**: 테스트는 빠르게, 최종본은 정밀하게
- **피드백 루프**: TIKI-TAKA에서 발견 → ONE-SHOT 템플릿 개선
- **시간 효율**: 모든 씬에 30분 투자할 필요 없음

### 대안 검토
| 대안 | 거부 이유 |
|------|----------|
| ONE-SHOT만 | 품질 한계 (85%) |
| TIKI-TAKA만 | 시간 과다 소요 |

### 상태
✅ **채택** (2026-02-01)

---

## 📌 PDR-002: ANCHOR 시스템

### 결정
캐릭터 얼굴 확정을 위해 특정 씬을 ANCHOR로 먼저 생성

### 배경
- AI 이미지 생성 시 캐릭터 얼굴이 씬마다 달라지는 문제
- 10컷 영상에서 동일 인물 유지 어려움

### 근거
- **일관성 우선**: 얼굴이 확정되면 다른 씬에서 레퍼런스로 사용
- **품질 기반선**: 가장 좋은 결과물을 기준으로 삼음
- **AI 도구 활용**: Midjourney --cw, NanoBanana Multi-ref 연동

### 구현
1. Scene 2 (클로즈업)를 ANCHOR로 선정
2. 결과물을 `ANCHOR.png`로 저장
3. 나머지 씬에서 `[Image 2: CHARACTER FACE] ANCHOR.png` 형식으로 참조

### 상태
✅ **채택** (2026-02-01)

---

## 📌 PDR-003: Multi-Entity Consistency

### 결정
캐릭터 외에 의상, 소품, 배경도 레퍼런스로 관리

### 배경
- ANCHOR로 얼굴은 일관되지만 의상/배경이 변함
- Kling Elements 4슬롯, NanoBanana 14레퍼런스 활용 가능

### 근거
- **완전한 일관성**: 모든 시각 요소 통제
- **도구 기능 활용**: 이미 존재하는 기능을 문서화
- **티키타카 철학 정합**: 반복 정제에 기여

### 구현
```
Element 1: CHARACTER FACE
Element 2: SCENE COMPOSITION
Element 3: COSTUME
Element 4: BACKGROUND
```

### 상태
✅ **채택** (2026-02-02)

---

## 📌 PDR-004: Frame-to-Frame Chaining

### 결정
Scene N 마지막 프레임을 Scene N+1 첫 프레임으로 연결

### 배경
- AI 생성 영상 간 점프컷 발생
- 캐릭터 위치/표정 불일치

### 근거
- **자연스러운 전환**: 시각적 연속성 확보
- **추가 도구 불필요**: FFmpeg로 프레임 추출
- **업계 표준**: Pika Labs 등에서 권장하는 방식

### 구현
```bash
ffmpeg -sseof -0.1 -i scene01.mp4 -vframes 1 scene01_last.png
```

### 상태
✅ **채택** (2026-02-02)

---

## 📌 PDR-005: Critique Self-Loop

### 결정
AI가 자체 평가 → 개선 제안 → Human 승인 루프

### 배경
- 사용자가 매번 직접 평가하기 부담
- AI가 명확한 기준으로 먼저 체크 가능

### 근거
- **Human-in-the-Loop 유지**: 최종 결정은 사람
- **효율성 향상**: 명백한 문제는 AI가 먼저 발견
- **티키타카 철학 정합**: AI 자체 비평 원칙과 일치

### 구현
```
Generate → AI Self-Critique → Improvement Suggestion 
→ Human: "OK" or "수정해"
→ Regenerate or Accept
```

### 상태
✅ **채택** (2026-02-02)

---

## 📌 PDR-006: End-to-End Automation 거부

### 결정
완전 자동화 파이프라인 **구현하지 않음**

### 배경
- 2026 트렌드로 End-to-End AI 파이프라인 제안됨
- 사람 개입 없이 영상 → 최종물 자동 생성

### 근거
- **철학 충돌**: Human-in-the-Loop 원칙 위배
- **품질 리스크**: AI 실수 누적 시 복구 어려움
- **창작 가치**: 사람의 판단이 차별화 요소

### 대안 채택
- **부분 자동화**: 프롬프트 생성, Critique는 자동
- **Human 체크포인트**: 각 Stage 사이에 승인 단계

### 상태
❌ **거부** (2026-02-02)

---

## 📌 PDR-007: 4-Tool Architecture

### 결정
이미지 2종 + 영상 2종 = 4개 도구 표준화

### 배경
- 도구마다 강점이 다름
- 모든 씬에 동일 도구 사용 비효율

### 근거

| 도구 | 강점 | 약점 |
|------|------|------|
| NanoBanana | 다중 레퍼런스 | 단일 얼굴 정밀도 |
| Midjourney | 얼굴 일관성 | 복잡 구도 어려움 |
| Kling | 비용효율, 빠름 | 짧은 영상 |
| Sora | 물리 정확, 길이 | 비용, 접근성 |

### 구현
씬별 도구 매핑 테이블 (SYSTEM_GUIDE.md)

### 상태
✅ **채택** (2026-02-01)

---

## 📌 PDR-008: Error Recovery Playbook

### 결정
흔한 AI 생성 문제와 해결책을 문서화

### 배경
- 문제 발생 시 해결 방법 찾느라 시간 낭비
- 같은 실수 반복

### 근거
- **복구 시간 단축**: 즉시 참조 가능한 플레이북
- **경험 축적**: 발견한 문제와 해결책 기록
- **팀 공유**: 다른 프로젝트에서도 활용

### 구현
`docs/ERROR_RECOVERY.md` - 8개 에러 유형, 복구 절차

### 상태
✅ **채택** (2026-02-02)

---

## 📌 PDR-009: Version Rollback 시스템

### 결정
생성물 버전 관리 및 롤백 기능 구현

### 배경
- "어제 버전이 더 나았는데..." 상황
- 실수로 좋은 결과물 덮어씀

### 근거
- **즉시 복원**: 롤백 명령어로 이전 버전 복구
- **버전 비교**: 두 버전 간 차이 확인
- **메타데이터**: 각 버전 정보 기록

### 구현
- `scripts/version.sh` (rollback, compare, metadata)
- `docs/VERSION_CONTROL.md`

### 상태
✅ **채택** (2026-02-02)

---

## 📌 PDR-010: 4-Layer Guardrails

### 결정
4단계 품질 검증 체계 도입

### 배경
- 문제가 늦게 발견될수록 복구 비용 증가
- 각 단계별 체크 기준 부재

### 근거
- **조기 발견**: Layer 1(Data)에서 잡으면 비용 최소
- **Human-in-the-Loop**: Layer 4에서 최종 인간 판단
- **체계적 검증**: 누락 없는 체크리스트

### 구현
```
Layer 1: Data (입력 검증)
Layer 2: Model (도구/파라미터)
Layer 3: Output (결과물 Critique)
Layer 4: Human (최종 승인)
```

### 상태
✅ **채택** (2026-02-02)

---

## 🗂️ Decision Log

| # | 결정 | 날짜 | 상태 |
|---|------|------|------|
| 001 | Tiki-Taka 듀얼 모드 | 2026-02-01 | ✅ |
| 002 | ANCHOR 시스템 | 2026-02-01 | ✅ |
| 003 | Multi-Entity | 2026-02-02 | ✅ |
| 004 | Frame Chaining | 2026-02-02 | ✅ |
| 005 | Critique Self-Loop | 2026-02-02 | ✅ |
| 006 | E2E Automation 거부 | 2026-02-02 | ❌ |
| 007 | 4-Tool Architecture | 2026-02-01 | ✅ |
| 008 | Error Recovery | 2026-02-02 | ✅ |
| 009 | Version Rollback | 2026-02-02 | ✅ |
| 010 | 4-Layer Guardrails | 2026-02-02 | ✅ |

---

> **Maintainer**: Ted
> **Next Review**: 2026-03-01
