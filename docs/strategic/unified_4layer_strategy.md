# 🎯 Crebit 4-Layer 생태계 통합 전략

> **검증 완료 (2026-01-02)**: 컨설팅 리포트의 핵심 주장들을 웹 검색으로 검증함

---

## 📋 검증 결과 요약

| 주장 | 검증 결과 | 출처 |
|------|:--------:|------|
| NotebookLM 실시간 제한 | ✅ **확인** | Free: 50 chat/day, Plus: 500 chat/day |
| MCP Gateway 패턴 | ✅ **확인** | Anthropic 공식, "USB-C for AI" |
| Tool Tier System | ✅ **타당** | EU AI Act 리스크 티어 기반 |
| Fork Attribution 필요성 | ✅ **타당** | Sybil Attack 방어 필수 |

---

## 🏗️ 수정된 4-Layer 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                Layer 4: Trust & Governance                       │
│  Tool Tier (Experimental→Verified→Certified) + Sandbox + Audit  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Tool Workshop    Layer 2: Human Cloud    Layer 3: RAG │
│  ┌────────────────────┐   ┌─────────────────────┐  ┌───────────┐│
│  │ 도구 Fork 시스템   │   │ 의뢰 + 크리에이터  │  │ Hybrid   ││
│  │ 60/30/10 분배     │   │ 75/25 정산         │  │ Workbench││
│  │ Attribution Score │   │ Evidence Logs      │  │ + Prod   ││
│  └────────────────────┘   └─────────────────────┘  └───────────┘│
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Layer 3 개편: Hybrid RAG 아키텍처

> **핵심 인사이트**: NotebookLM을 런타임 엔진이 아닌 **Workbench(저작도구)**로 재정의

### Before (문제점)
```
사용자 요청 → NotebookLM API → 응답
           (Rate Limit 병목, API 종속)
```

### After (개선안)
```
┌─────────────────────────────────────────────────────────────┐
│                     Layer 3: RAG                            │
│                                                             │
│  ┌─────────────────┐          ┌────────────────────────┐   │
│  │   WORKBENCH     │  승격    │      PRODUCTION        │   │
│  │                 │ ─────→   │                        │   │
│  │ NotebookLM      │          │ Internal Vector DB     │   │
│  │ (Enterprise)    │          │ (Qdrant/Pinecone)      │   │
│  │                 │          │                        │   │
│  │ • Deep Research │          │ • 실시간 추천          │   │
│  │ • 가이드 생성   │          │ • 도구 조합 제안       │   │
│  │ • 패턴 분석     │          │ • 메트릭 기반 랭킹     │   │
│  └─────────────────┘          └────────────────────────┘   │
│                                                             │
│  Usage: 연구/저작용            Usage: 런타임/서빙용        │
│  Quota: 500 chat/day (충분)    Quota: 무제한 (자체 인프라) │
└─────────────────────────────────────────────────────────────┘
```

### NotebookLM 제한사항 (검증됨)

| 항목 | Free | Plus/Enterprise |
|------|:----:|:---------------:|
| 일일 채팅 쿼리 | 50 | 500 |
| 오디오 생성 | 3/day | 20/day |
| Deep Research | 10/month | 20/month |
| 소스/노트북 | 50/100 | 300/500 |

→ **결론**: 런타임 엔진으로 부적합, Workbench로 활용

---

## 🛡️ Layer 4: Trust & Governance (신규)

### Tool Tier System

```typescript
enum ToolTier {
  EXPERIMENTAL = 'experimental',  // 누구나 생성, 검색 노출 제한
  VERIFIED = 'verified',          // 자동 테스트 통과
  CERTIFIED = 'certified',        // Human Cloud 성공률 검증
}

interface ToolManifest {
  id: string;
  tier: ToolTier;
  
  // 스키마
  input_schema: JSONSchema;
  output_schema: JSONSchema;
  
  // 경제
  credit_cost: number;
  fork_count: number;
  attribution_score: number;
  
  // 거버넌스
  created_by: string;
  approved_at?: Date;
  safety_rating: 'safe' | 'review' | 'restricted';
  sandbox_required: boolean;
}
```

### Sandbox 실행 환경

외부 PR이나 바이브코딩으로 생성된 도구는 격리 환경에서 실행:

```yaml
# 도구 격리 정책
sandbox:
  network: disabled  # 외부 API 호출 차단
  filesystem: readonly  # 파일시스템 쓰기 금지
  timeout: 30s  # 실행 시간 제한
  memory: 512MB  # 메모리 제한
```

---

## 💰 경제 시스템 개선: Attribution Score

### 기존 문제점
```
단순 Depth 기반:
Original → Fork1 → Fork2 → Fork3
  60%       30%     10%     0%

문제: 의미없는 포크로 수익 가로채기 (Sybil Attack)
```

### 개선안: Attribution Score 기반

```typescript
interface AttributionScore {
  diff_score: number;      // 변경량 (0-100)
  test_pass: boolean;      // 테스트 통과 여부
  usage_count: number;     // 실제 사용량
  revenue_generated: number; // 매출 기여도
  quality_rating: number;  // 사용자 평점
}

function calculateAttributionScore(fork: Fork): number {
  const weights = {
    diff: 0.2,      // 변경량 20%
    test: 0.15,     // 테스트 15%
    usage: 0.25,    // 사용량 25%
    revenue: 0.25,  // 매출 25%
    quality: 0.15,  // 품질 15%
  };
  
  return (
    fork.diff_score * weights.diff +
    (fork.test_pass ? 100 : 0) * weights.test +
    normalize(fork.usage_count) * weights.usage +
    normalize(fork.revenue_generated) * weights.revenue +
    fork.quality_rating * weights.quality
  );
}
```

### 수익 분배 공식

```
총 매출 = 100%
├── 플랫폼 수수료: 30%
└── 크리에이터 풀: 70%
    ├── Original (attribution 비례)
    ├── Forker1 (attribution 비례)
    └── ForkerN (attribution 비례)
```

---

## 🔄 MCP Gateway 패턴 (검증됨)

> MCP = "USB-C for AI" - Anthropic 공식 설명

### 현재 구현 유지

```python
# backend/app/routers/mcp.py
# MCP는 내부 캡슐을 외부에 노출하는 Gateway 역할만 수행
# 내부 SoR(Source of Record)는 여전히 DB/Manifest
```

### MCP 역할 정의

| 역할 | 설명 |
|------|------|
| **Gateway** | 내부 도구를 외부 AI 에이전트에 노출 |
| **Discovery** | 사용 가능한 도구 목록 제공 |
| **Invocation** | 표준 프로토콜로 도구 실행 |

**핵심**: MCP는 인터페이스, 실제 도구 정의/실행은 내부 시스템

---

## 📅 수정된 실행 로드맵

### Week 1 (즉시)

| 우선순위 | 작업 | 담당 |
|:--------:|------|------|
| P0 | Telemetry 파이프라인 구축 | Backend |
| P0 | ToolRunEvent, ForkEvent 수집 시작 | Backend |
| P1 | Tool Manifest DB 스키마 설계 | Backend |
| P1 | capsule_registry → DB 승격 | Backend |

### Week 2-4

| 우선순위 | 작업 |
|:--------:|------|
| P1 | Tool Tier System 구현 |
| P1 | Sandbox 실행 환경 |
| P2 | Attribution Score 계산 로직 |
| P2 | NotebookLM → DB Import 파이프라인 |

### Month 2-3

| 우선순위 | 작업 |
|:--------:|------|
| P1 | Human Cloud MVP (영상 크리에이티브만) |
| P1 | Evidence Logs 자동 생성 |
| P2 | Internal RAG (Vector DB) |
| P2 | 실시간 도구 추천 |

---

## ⚠️ 리스크 및 완화 방안

| 리스크 | 확률 | 영향 | 완화 방안 |
|--------|:----:|:----:|-----------|
| NotebookLM API 변경 | 중 | 높음 | Workbench 역할만 의존 |
| 도구 품질 저하 | 높음 | 높음 | Tier System + Sandbox |
| Sybil Attack | 중 | 높음 | Attribution Score |
| Human Cloud 운영 비용 | 높음 | 중 | 단일 카테고리 MVP |

---

## 결론

> "피벗 방향은 **기술적/시장적으로 매우 정확**합니다. 
> NotebookLM을 '저작 도구'로 제한하고, 
> 도구 확장에 따른 '품질 거버넌스'를 설계에 포함시킨다면, 
> 이 플랫폼은 **복제 불가능한 생태계**가 될 것입니다."

---

*검증 완료: 2026-01-02 19:10 KST*
