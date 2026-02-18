# Vivid Architecture Flexibility Analysis 2026

> 워크플로우 유연성, Human-in-the-Loop, RAG 통합 아키텍처 분석

---

## Executive Summary

### 현재 상태 평가

| 항목 | 현재 점수 | 2026 베스트 프랙티스 | 갭 분석 |
|------|----------|---------------------|---------|
| **단독 앱 실행** | ✅ 10/10 | Composable Microservices | 완벽 지원 |
| **워크플로우 순서 유연성** | ⚠️ 6/10 | Dynamic DAG Orchestration | 하드코딩된 연결 맵 |
| **동적 앱 삽입/제거** | ⚠️ 5/10 | Agentic Tool Selection | 수동 템플릿 기반 |
| **Human-in-the-Loop** | ⚠️ 4/10 | Hybrid Intelligence | 인프라 있으나 미적용 |
| **RAG + 사용자 DB 통합** | ⚠️ 5/10 | Context-Native Workflow | 부분 구현 |

**종합 평가**: 기초 아키텍처는 갖춰졌으나, **2026 Composable AI 표준에 도달하려면 중요한 업그레이드 필요**

---

## 1. 2026 Industry Trends (웹 리서치 기반)

### 1.1 Composable AI Architecture

> "Agentic AI is now doing the same for enterprises by turning workflows into adaptive, tool-enabled processes. Each tool acts like a microservice, and agents orchestrate them dynamically."
> — [The New Stack: AI Workflow Composable Architecture](https://thenewstack.io/your-ai-workflow-is-missing-a-composable-architecture/)

**2026 핵심 패턴:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    2026 Composable Enterprise                   │
├─────────────────────────────────────────────────────────────────┤
│  Foundation Models → Core reasoning engines                     │
│  Tools → Specialized microservice-like functions                │
│  Agents → Orchestrators of tools                                │
│  Vector Databases & Context Layers → Memory and knowledge       │
│  Composable Workflows → Adaptive processes (never hardcoded)    │
└─────────────────────────────────────────────────────────────────┘
```

**Sources:**
- [Composable Data Architecture: 2026 Tipping Point](https://www.infojiniconsulting.com/blog/composable-data-architectures-explained-why-2026-is-the-tipping-point/)
- [Tribe AI: Composable Agents](https://www.tribe.ai/applied-ai/inside-the-machine-how-composable-agents-are-rewiring-ai-architecture-in-2025)

### 1.2 Dynamic DAG Orchestration

> "The best pattern varies across your system. Hub-and-spoke is typically used for coordinating high-level goals, with pipelines for well-defined subtasks."
> — [Choosing Your AI Orchestration Stack for 2026](https://thenewstack.io/choosing-your-ai-orchestration-stack-for-2026/)

**2026 오케스트레이션 선택지:**

| Framework | 특성 | Vivid 적합도 |
|-----------|------|-------------|
| **LangGraph** | Graph-based, stateful, DAG 구조 | ⭐⭐⭐⭐ |
| **Temporal** | Durable Execution, 장기 실행 | ⭐⭐⭐⭐⭐ |
| **CrewAI** | Multi-agent collaboration | ⭐⭐⭐ |

**Sources:**
- [Temporal: Dynamic AI Agents](https://temporal.io/blog/of-course-you-can-build-dynamic-ai-agents-with-temporal)
- [Agent Orchestration 2026 Guide](https://iterathon.tech/blog/ai-agent-orchestration-frameworks-2026)

### 1.3 Human-in-the-Loop (HITL)

> "Human-in-the-Loop (HitL) is critical to the success of agent AI orchestration. Not only does HitL allow for people to step in and move processes forward when AI agents run into problems, it also gives agents opportunities to learn from those people."
> — [Agentic AI Orchestration 2026](https://onereach.ai/blog/agentic-ai-orchestration-enterprise-workflow-automation/)

**2026 HITL 패턴:**

```
┌─────────────────────────────────────────────────────────────────┐
│                  Hybrid Intelligence Workflow                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    AI Step 1 → [Human Checkpoint] → AI Step 2 → AI Step 3       │
│         ↓              ↓                ↓           ↓            │
│    Auto-execute    Review/Edit    Auto-execute  Auto-execute     │
│                                                                  │
│    Human input feeds back into system for continuous learning    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Sources:**
- [Parseur: Future of HITL AI 2025-2026](https://parseur.com/blog/future-of-hitl-ai)
- [IBM: Human-in-the-Loop AI](https://www.ibm.com/think/topics/human-in-the-loop)

### 1.4 Agentic RAG (Context-Native)

> "RAG is undergoing its own profound metamorphosis, evolving from 'Retrieval-Augmented Generation' into a 'Context Engine' with 'intelligent retrieval' as its core capability."
> — [RAGFlow: From RAG to Context](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)

**ARAG (Agentic RAG) 패턴:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARAG Multi-Agent Framework                    │
├─────────────────────────────────────────────────────────────────┤
│  User Understanding Agent → Summarizes preferences               │
│  NLI Agent → Evaluates semantic alignment                        │
│  Context Summary Agent → Aggregates context                      │
│  Item Ranker Agent → Final ranking based on intent               │
├─────────────────────────────────────────────────────────────────┤
│  Result: 42.1% improvement in NDCG@5 vs standard RAG             │
└─────────────────────────────────────────────────────────────────┘
```

**Sources:**
- [ARAG: Agentic RAG for Personalization](https://arxiv.org/html/2506.21931v1)
- [RAG Models 2026 Enterprise Guide](https://www.techment.com/blogs/rag-models-2026-enterprise-ai/)

---

## 2. 현재 Vivid 아키텍처 분석

### 2.1 단독 앱 실행 (✅ 완벽 지원)

**현재 구현:**

```typescript
// Frontend: 각 패널 독립 실행 가능
// frontend/src/components/dimension/PromptGeneratorPanel.tsx
export default function PromptGeneratorPanel() {
  return (
    <DimensionPanel dimensionCode="1d">
      <PromptGeneratorContent />
    </DimensionPanel>
  );
}
```

```python
# Backend: 각 캡슐 독립 호출 가능
# backend/app/dimension_adapter.py
class DimensionCapsuleId(str, Enum):
    PROMPT_GENERATE = "teaching.prompt.generate"
    STORYBOARD_CREATE = "teaching.storyboard.create"
    # ... 16개 독립 캡슐
```

**평가**: ✅ **각 Dimension 앱은 완전히 독립적으로 실행 가능**

---

### 2.2 워크플로우 순서 유연성 (⚠️ 제한적)

**현재 구현:**

```typescript
// frontend/src/lib/dimension-theme.ts
// 연결 맵이 하드코딩되어 있음
export const DIMENSION_CONNECTIONS: Record<string, string[]> = {
    "abyss-mirror": ["reference-decoder", "story-architect", "aesthetic-director"],
    "reference-decoder": ["story-architect", "storyboard-sketch"],
    "story-architect": ["storyboard-sketch", "sound-crafter", "prompt-alchemy"],
    // ...
};
```

```python
# backend/app/services/workflow_planner.py
WORKFLOW_TEMPLATES: Dict[str, WorkflowTemplate] = {
    "content_creation": WorkflowTemplate(
        tools=["prompt_generator", "storyboard", "image_tool"],  # 순서 고정
        connections=[...],  # 연결 고정
    ),
    # ...
}
```

**문제점:**

| 현재 | 2026 표준 |
|------|-----------|
| 하드코딩된 `DIMENSION_CONNECTIONS` | Dynamic DAG based on intent |
| 고정된 `WorkflowTemplate.tools` 순서 | Agent-driven tool selection |
| 수동 템플릿 선택 | Intent-based auto-planning |

**필요한 개선:**

```python
# 제안: Dynamic Connection Resolution
class DynamicWorkflowPlanner:
    async def plan(self, intent: str, available_tools: List[str]) -> DAG:
        """
        LLM이 의도를 분석하고 동적으로 DAG 생성
        """
        # 1. Intent classification
        intent_type = await self.classify_intent(intent)

        # 2. Tool selection (agent-driven)
        selected_tools = await self.select_tools(intent_type, available_tools)

        # 3. Dynamic ordering based on dependencies
        dag = await self.build_dag(selected_tools, intent_type)

        return dag
```

---

### 2.3 동적 앱 삽입/제거 (⚠️ 부분 지원)

**현재 구현:**

```typescript
// frontend/src/contexts/DimensionChainContext.tsx
const getInputData = useCallback((dimensionKey: string): Record<string, ChainData> => {
    // 입력 소스가 하드코딩됨
    const inputMap: Record<string, string[]> = {
        "reference-decoder": ["abyss-mirror"],
        "story-architect": ["abyss-mirror", "reference-decoder"],
        // ...
    };
    // ...
}, [chainData]);
```

**문제점:**
- 새 앱 추가 시 `inputMap` 수동 업데이트 필요
- 런타임 동적 삽입 불가

**2026 표준 해결책:**

```python
# Composable Tool Registry Pattern
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec):
        """런타임에 도구 등록"""
        self.tools[tool.id] = tool
        self._update_dependency_graph()

    def get_compatible_inputs(self, tool_id: str) -> List[str]:
        """도구의 호환 가능한 입력 소스 동적 계산"""
        tool = self.tools[tool_id]
        return [
            t.id for t in self.tools.values()
            if self._outputs_match(t.output_schema, tool.input_schema)
        ]
```

---

### 2.4 Human-in-the-Loop (⚠️ 인프라만 존재)

**현재 구현:**

```python
# backend/app/services/workflow_executor.py
async def execute_step(...):
    """
    현재: 모든 스텝 자동 실행
    Human checkpoint 없음
    """
    # ...순차 실행...
```

```typescript
// frontend/src/contexts/DimensionChainContext.tsx
// 데이터 흐름 추적은 가능하나, 인간 개입 포인트 없음
```

**필요한 개선:**

```python
# 제안: HITL-enabled Workflow
class HITLWorkflow:
    async def execute_step(self, step: WorkflowStep) -> StepResult:
        if step.requires_human_review:
            # 1. 실행 후 일시 정지
            result = await self._execute(step)

            # 2. 인간 리뷰 대기
            await self._notify_human(step, result)
            human_input = await self._wait_for_human_input(step.id, timeout=3600)

            # 3. 인간 입력 반영
            if human_input.action == "approve":
                return result
            elif human_input.action == "edit":
                return await self._apply_edits(result, human_input.edits)
            elif human_input.action == "regenerate":
                return await self._regenerate(step, human_input.feedback)
        else:
            return await self._execute(step)
```

---

### 2.5 RAG + 사용자 DB 통합 (⚠️ 부분 구현)

**현재 구현:**

```python
# backend/app/rag/hybrid_rag.py
@dataclass
class HybridRAGResult:
    notebooklm_sources: List[NotebookSource]  # 거장 DNA
    vertex_sources: List[RAGSource]           # 차원별 지식
    # 사용자 개인화 소스 없음!
```

```python
# backend/app/services/workflow_executor.py
def _build_prompt_inputs(node_inputs, session):
    """
    현재: session.extracted_params만 사용
    사용자 히스토리/선호도 통합 없음
    """
    params = session.extracted_params
    return {...}
```

**필요한 개선:**

```python
# 제안: Agentic RAG with User Context
class AgenticRAGService:
    async def query(
        self,
        query: str,
        user_id: str,
        workflow_context: Dict[str, Any],
    ) -> EnrichedRAGResult:
        # 1. 사용자 프로필 로드
        user_profile = await self.user_service.get_profile(user_id)
        user_history = await self.user_service.get_recent_outputs(user_id, limit=10)

        # 2. 컨텍스트 통합
        enriched_query = await self.context_agent.enrich(
            query=query,
            user_preferences=user_profile.preferences,
            user_style_history=user_history,
            current_workflow=workflow_context,
        )

        # 3. 다중 소스 검색
        results = await asyncio.gather(
            self.notebooklm.query(enriched_query),  # 거장 DNA
            self.qdrant.hybrid_search(enriched_query),  # 차원 지식
            self.user_db.search_similar(user_id, enriched_query),  # 사용자 과거 작업
        )

        # 4. 개인화된 리랭킹
        return await self.ranker.rank_with_personalization(
            results,
            user_profile,
        )
```

---

## 3. 사용자 시나리오 분석

### 시나리오: "레퍼런스 해석기만 사람이 하고 나머지는 자동화"

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Hybrid Intelligence Workflow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Reference Decoder (4D) → [HUMAN REVIEW] ← 사용자 직접 분석           │
│         ↓                                                                │
│  2. Story Architect → AUTO (RAG: 거장 스타일 + 사용자 히스토리)          │
│         ↓                                                                │
│  3. Aesthetic Director → AUTO (템플릿 특성 + 사용자 선호도)              │
│         ↓                                                                │
│  4. Storyboard → AUTO                                                   │
│         ↓                                                                │
│  5. Visual Realizer → AUTO                                              │
│         ↓                                                                │
│  6. Quality Check → AUTO → [OPTIONAL HUMAN REVIEW]                      │
│         ↓                                                                │
│  7. Final Output (VEO) → AUTO                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**현재 가능 여부:**

| 요소 | 현재 상태 | 필요 작업 |
|------|----------|----------|
| 4D 단독 실행 | ✅ 가능 | - |
| 인간 리뷰 후 재개 | ❌ 불가 | HITL 워크플로우 구현 |
| RAG 거장 스타일 | ✅ 가능 | - |
| 사용자 히스토리 통합 | ❌ 불가 | User Context Service 구현 |
| 템플릿 특성 적용 | ⚠️ 부분 | WorkflowTemplate 확장 |
| 자동 연속 실행 | ✅ 가능 | execute_all_steps 존재 |

---

## 4. 아키텍처 업그레이드 로드맵

### Phase 1: Dynamic Workflow (2-3주)

```python
# 1. Tool Registry 리팩토링
class DynamicToolRegistry:
    """런타임 도구 등록/해제 지원"""
    pass

# 2. DAG-based Planner
class DAGWorkflowPlanner:
    """의존성 기반 동적 순서 결정"""
    pass

# 3. Intent-based Selection
class IntentBasedSelector:
    """LLM 기반 도구 선택"""
    pass
```

### Phase 2: Human-in-the-Loop (2-3주)

```python
# 1. Checkpoint System
class WorkflowCheckpoint:
    """실행 중단/재개 지점 관리"""
    pass

# 2. Human Review Queue
class HumanReviewQueue:
    """인간 리뷰 대기열 관리"""
    pass

# 3. Feedback Integration
class HumanFeedbackIntegrator:
    """인간 피드백을 다음 스텝에 반영"""
    pass
```

### Phase 3: Personalized RAG (3-4주)

```python
# 1. User Context Service
class UserContextService:
    """사용자 프로필, 히스토리, 선호도 관리"""
    pass

# 2. Agentic RAG
class AgenticRAGOrchestrator:
    """다중 에이전트 RAG 조정"""
    pass

# 3. Template Personalization
class TemplatePersonalizer:
    """템플릿에 사용자 컨텍스트 주입"""
    pass
```

---

## 5. 권장 아키텍처 (2026 Target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Vivid 2026 Target Architecture                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Orchestration Layer                           │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │ Intent Agent │  │ DAG Planner  │  │ HITL Manager │          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Tool Layer (Composable)                       │    │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐      │    │
│  │  │ 1D │ │ 2D │ │ 3D │ │ 4D │ │ AD │ │ SC │ │VEO │ │ QC │      │    │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↓                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Context Layer (Agentic RAG)                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │ NotebookLM   │  │   Qdrant     │  │  User DB     │          │    │
│  │  │ (거장 DNA)   │  │ (차원 지식)  │  │(히스토리/선호)│          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 결론

### 질문 1: 순서 유연성

> **"단독/템플릿/순서 변경/동적 삽입이 되는 구조인가?"**

**현재**: ⚠️ **부분적으로 가능**
- ✅ 단독 실행: 완벽 지원
- ⚠️ 템플릿 순서 고정: `WorkflowTemplate.tools` 배열 순서 고정
- ❌ 동적 순서 변경: `DIMENSION_CONNECTIONS` 하드코딩
- ❌ 런타임 삽입/제거: 수동 템플릿 수정 필요

**필요 작업**: DAG-based Dynamic Planner + Tool Registry 리팩토링

### 질문 2: HITL + RAG + 사용자 DB 통합

> **"사람이 한 단계만 하고 나머지는 RAG/템플릿/사용자DB로 자동 생성 가능한가?"**

**현재**: ⚠️ **인프라는 있으나 통합 안됨**
- ✅ RAG 거장 지식: HybridRAG 구현됨
- ✅ 템플릿 시스템: WorkflowTemplate 존재
- ❌ Human Checkpoint: 워크플로우 중단/재개 없음
- ❌ 사용자 개인화: User Context Service 없음
- ❌ 통합 오케스트레이션: 세 가지 분리됨

**필요 작업**: HITL Workflow + UserContextService + AgenticRAG Orchestrator

---

### 최종 평가

| 영역 | 현재 | 2026 목표 | 우선순위 |
|------|------|----------|----------|
| **Composable Tools** | 80% | 100% | P1 |
| **Dynamic Orchestration** | 40% | 100% | P0 |
| **Human-in-the-Loop** | 20% | 100% | P0 |
| **Personalized RAG** | 30% | 100% | P1 |

**총평**: 기반 아키텍처는 훌륭하지만, **2026 Hybrid Intelligence 표준을 달성하려면 Orchestration Layer 대폭 업그레이드 필요**

---

## References

### 2026 Industry Research
- [Composable Data Architecture 2026](https://www.infojiniconsulting.com/blog/composable-data-architectures-explained-why-2026-is-the-tipping-point/)
- [AI Orchestration Stack 2026](https://thenewstack.io/choosing-your-ai-orchestration-stack-for-2026/)
- [Agentic AI as New Microservices](https://www.fluid.ai/blog/agentic-ai-tools-are-the-new-microservices)
- [Temporal for Dynamic AI Agents](https://temporal.io/blog/of-course-you-can-build-dynamic-ai-agents-with-temporal)
- [LangGraph Agent Orchestration 2026](https://iterathon.tech/blog/ai-agent-orchestration-frameworks-2026)
- [Human-in-the-Loop AI 2026](https://parseur.com/blog/human-in-the-loop-ai)
- [ARAG Personalized Recommendation](https://arxiv.org/html/2506.21931v1)
- [RAG to Context Engine](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)

### Vivid Codebase References
- `frontend/src/contexts/DimensionChainContext.tsx`
- `frontend/src/lib/dimension-theme.ts`
- `backend/app/services/workflow_executor.py`
- `backend/app/services/workflow_planner.py`
- `backend/app/rag/hybrid_rag.py`
- `backend/app/dimension_adapter.py`

---

*Generated with ultrathink analysis based on 2026 MCP research and web search*

*Last Updated: 2026-01-16*
