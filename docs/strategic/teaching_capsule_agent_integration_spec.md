# Teaching Capsule Agent Integration Spec

**작성**: 2026-01-01
**버전**: v1.0
**대상**: Backend / Frontend Developer
**목표**: Teaching 캡슐들을 Agent Chat LLM에서 Tool로 호출하고, **내부 워크플로우 그래프(레거시 Canvas 노드)**로 연결하는 구현 가이드

> ⚠️ **DEPRECATED (2026-01-05)**: 이 문서는 레거시 통합 패턴을 설명합니다.
> - `routers/teaching.py` → **삭제됨** (현행: `routers/dimension.py`)
> - `teaching_adapter.py` → **삭제됨** (현행: `dimension_adapter.py`)
> - `TeachingCapsuleNode.tsx` → **삭제됨** (현행: `DimensionCapsuleNode.tsx`)
> - 현행 도구: `backend/app/agents/dimension_tools.py`

> Status (2026-01): 사용자 UI는 Flow/Dimension이 기본이며, Canvas/Node 용어는 내부 그래프 또는 레거시 UI를 의미합니다.
> Legacy UI 경로: `frontend/src/app/_deprecated/studio/`, `frontend/src/components/canvas/`.

---

## 1) 핵심 개념

### 1.1 통합 목표

```
┌─────────────────────────────────────────────────────────────────────────┐
│  User Chat Input                                                         │
│  "2분짜리 요리 브이로그를 만들고 싶어"                                    │
└─────────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Agent LLM (Gemini)                                                      │
│  - 사용자 의도 분석                                                       │
│  - 적절한 Teaching Capsule 선택                                           │
│  - 파라미터 자동 추출 & 노드 생성                                        │
└─────────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Canvas Node (수정 가능)                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ 📦 Prompt Generator                                               │  │
│  │ topic: "2분 요리 브이로그" ← 채팅에서 추출                        │  │
│  │ style: "vlog" ← LLM 추론                                          │  │
│  │ duration: "2분" ← 채팅에서 추출                                   │  │
│  │ [▶ Execute] [✏️ Edit Params]                                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Pipeline Connection                                                     │
│  [Prompt Generator] ──output──▶ [Storyboard Generator] ──▶ [Image Gen]   │
└─────────────────────────────────────────────────────────────────────────┘
```

> Note: 위 "Canvas Node"는 사용자 UI가 아닌 내부 그래프 표현입니다. UI에서는 Train Workflow/Dimension을 사용합니다.

### 1.2 주요 컴포넌트

| 컴포넌트 | 역할 | 위치 (현행) |
|----------|------|------|
| **Dimension Capsules** | 4개의 AI 도구 (Prompt, Storyboard, Image, Reference) | `routers/dimension.py` |
| **Agent Chat** | 사용자 의도 해석 + 도구 호출 | `routers/agent.py` |
| **Node Canvas (Legacy UI)** | 노드 기반 그래프 편집 (내부 그래프/레거시 UI) | `frontend/src/app/_deprecated/studio/`, `frontend/src/components/canvas/` |
| **Dimension Adapter** | 캡슐 실행 + 크레딧 차감 | `backend/app/dimension_adapter.py` |

---

## 2) Tool Schema 정의

Agent LLM은 Function Calling으로 Teaching 캡슐을 호출합니다.

### 2.1 Tool Declarations

```typescript
const TEACHING_TOOLS = [
  {
    name: "generate_veo_prompt",
    description: "영상 주제/스타일/분위기로 Veo 비디오 생성 프롬프트를 만듭니다",
    parameters: {
      type: "object",
      properties: {
        topic: {
          type: "string",
          description: "영상 주제 또는 컨셉 (필수)"
        },
        style: {
          type: "string",
          enum: ["cinematic", "documentary", "commercial", "artistic", "vlog"],
          description: "영상 스타일"
        },
        mood: {
          type: "string",
          enum: ["neutral", "dramatic", "calm", "energetic", "melancholic"],
          description: "분위기/톤"
        },
        duration: {
          type: "string",
          description: "영상 길이 (예: '15 seconds', '30 seconds', '60 seconds')"
        }
      },
      required: ["topic"]
    }
  },
  {
    name: "create_storyboard",
    description: "스토리 컨셉으로 씬 단위 스토리보드를 생성합니다",
    parameters: {
      type: "object",
      properties: {
        concept: {
          type: "string",
          description: "스토리 컨셉 또는 시나리오"
        },
        scene_count: {
          type: "number",
          description: "생성할 씬 개수 (3~20)"
        }
      },
      required: ["concept"]
    }
  },
  {
    name: "generate_image_prompt",
    description: "이미지 설명으로 AI 이미지 생성 프롬프트를 만듭니다",
    parameters: {
      type: "object",
      properties: {
        description: {
          type: "string",
          description: "이미지 설명"
        },
        style: {
          type: "string",
          enum: ["photorealistic", "cinematic", "anime", "illustration", "3d-render"],
          description: "이미지 스타일"
        },
        aspect_ratio: {
          type: "string",
          enum: ["16:9", "9:16", "1:1", "4:3"],
          description: "종횡비"
        }
      },
      required: ["description"]
    }
  },
  {
    name: "analyze_reference",
    description: "영상 레퍼런스의 시네마틱 요소를 분석합니다",
    parameters: {
      type: "object",
      properties: {
        video_description: {
          type: "string",
          description: "분석할 영상의 특징 설명"
        },
        focus_areas: {
          type: "array",
          items: { type: "string" },
          description: "분석 초점: composition, lighting, color, movement, narrative"
        }
      },
      required: ["video_description"]
    }
  }
];
```

### 2.2 System Prompt Injection

Agent LLM에게 Teaching 도구 사용 가이드를 주입합니다:

```python
TEACHING_SYSTEM_PROMPT = """
## Teaching Tools 가이드

사용자가 영상/이미지 콘텐츠 제작을 요청하면 Teaching 도구를 활용하세요.

### 도구 선택 기준

| 사용자 요청 | 추천 도구 |
|-------------|-----------|
| "영상 프롬프트", "비디오 만들기", "Veo 프롬프트" | generate_veo_prompt |
| "스토리보드", "씬 구성", "장면 만들기" | create_storyboard |
| "이미지 프롬프트", "그림 만들기", "사진 생성" | generate_image_prompt |
| "레퍼런스 분석", "영상 분석", "스타일 분석" | analyze_reference |

### 파라미터 추출 규칙

- 채팅에서 명시된 값은 그대로 사용
- 추론 가능한 값은 기본값으로 설정
- 불명확한 값은 사용자에게 확인 요청

### 노드 생성

도구 호출 후 결과를 **Canvas Node**로 변환하여 사용자가 수정할 수 있게 합니다.
"""
```

---

## 3) Backend 구현

### 3.1 Agent → Teaching Router 연동

`routers/agent.py`에서 Dimension 도구 호출:

```python
# routers/agent.py (현행: dimension.py 사용)

from app.routers.dimension import (
    generate_prompt,
    create_storyboard,
    generate_image_prompt,
    analyze_reference,
    PromptGenerateRequest,
    StoryboardCreateRequest,
    ImageGenerateRequest,
    ReferenceAnalyzeRequest,
)

TOOL_HANDLERS = {
    "generate_veo_prompt": {
        "handler": generate_prompt,
        "request_model": PromptGenerateRequest,
        "capsule_type": "dimension.prompt",
    },
    "create_storyboard": {
        "handler": create_storyboard,
        "request_model": StoryboardCreateRequest,
        "capsule_type": "dimension.storyboard",
    },
    "generate_image_prompt": {
        "handler": generate_image_prompt,
        "request_model": ImageGenerateRequest,
        "capsule_type": "dimension.image",
    },
    "analyze_reference": {
        "handler": analyze_reference,
        "request_model": ReferenceAnalyzeRequest,
        "capsule_type": "dimension.reference",
    },
}


async def execute_teaching_tool(
    tool_name: str,
    tool_args: dict,
    user: dict,
    db: AsyncSession,
    byok_key: Optional[str] = None,
) -> dict:
    """Agent가 호출한 Teaching 도구 실행"""
    
    if tool_name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    handler_info = TOOL_HANDLERS[tool_name]
    
    # 1. Request 모델 생성
    request = handler_info["request_model"](**tool_args)
    
    # 2. Handler 호출 (크레딧 검사 포함)
    result = await handler_info["handler"](
        request=request,
        user=user,
        byok_key=byok_key,
        db=db,
    )
    
    # 3. Node Spec으로 변환
    node_spec = build_node_spec(
        capsule_type=handler_info["capsule_type"],
        inputs=tool_args,
        output=result.output,
    )
    
    return {
        "success": result.success,
        "output": result.output,
        "node_spec": node_spec,  # ← Canvas 노드 생성용
        "capsule_id": result.capsule_id,
    }
```

### 3.2 Node Spec 생성

도구 호출 결과를 Canvas 노드로 변환:

```python
# services/node_builder.py

from typing import Any, Dict
import uuid


def build_node_spec(
    capsule_type: str,
    inputs: Dict[str, Any],
    output: Dict[str, Any],
) -> Dict[str, Any]:
    """Teaching 도구 결과를 Canvas Node Spec으로 변환"""
    
    CAPSULE_CONFIGS = {
        "dimension.prompt": {
            "display_name": "Veo 프롬프트 생성기",
            "node_type": "capsule",
            "input_ports": ["topic"],
            "output_ports": ["prompt", "negative_prompt", "technical"],
            "icon": "wand",
        },
        "dimension.storyboard": {
            "display_name": "스토리보드 생성기",
            "node_type": "capsule",
            "input_ports": ["concept"],
            "output_ports": ["scenes"],
            "icon": "film",
        },
        "dimension.image": {
            "display_name": "이미지 프롬프트 생성기",
            "node_type": "capsule",
            "input_ports": ["description"],
            "output_ports": ["prompt", "parameters"],
            "icon": "image",
        },
        "dimension.reference": {
            "display_name": "레퍼런스 분석기",
            "node_type": "capsule",
            "input_ports": ["video_description"],
            "output_ports": ["analysis", "recommendations"],
            "icon": "search",
        },
    }
    
    config = CAPSULE_CONFIGS[capsule_type]
    
    return {
        "id": str(uuid.uuid4()),
        "capsule_id": capsule_type,
        "type": config["node_type"],
        "display_name": config["display_name"],
        "position": {"x": 0, "y": 0},  # Canvas에서 자동 배치
        "data": {
            "inputs": inputs,
            "locked_inputs": list(inputs.keys()),  # 채팅에서 채운 값 표시
            "output": output,
            "editable": True,  # 사용자 수정 가능
        },
        "input_ports": config["input_ports"],
        "output_ports": config["output_ports"],
        "icon": config["icon"],
        "executed": True,
        "execution_time": None,
    }
```

### 3.3 SSE Event 발행

Agent Chat에서 노드 생성 이벤트 전송:

```python
# Agent Chat SSE Event Types

async def emit_teaching_node_created(
    session_id: str,
    node_spec: dict,
    seq: int,
) -> dict:
    """Teaching 도구 실행 후 노드 생성 이벤트"""
    return {
        "event_id": f"{session_id}:{seq}",
        "session_id": session_id,
        "type": "agent.node_created",
        "seq": seq,
        "ts": datetime.utcnow().isoformat() + "Z",
        "payload": {
            "node_type": "teaching_capsule",
            "node_spec": node_spec,
            "action": "add_to_canvas",  # 캔버스에 추가
        }
    }
```

---

## 4) Frontend 구현

### 4.1 Agent Chat → Canvas 연동

Agent Chat에서 노드 생성 이벤트 수신:

```typescript
// hooks/useAgentChatStream.ts

interface NodeCreatedEvent {
  type: "agent.node_created";
  payload: {
    node_type: "teaching_capsule";
    node_spec: TeachingNodeSpec;
    action: "add_to_canvas";
  };
}

function handleNodeCreatedEvent(event: NodeCreatedEvent) {
  // 1. Canvas에 노드 추가
  const node = convertToReactFlowNode(event.payload.node_spec);
  
  // 2. 자동 배치 (기존 노드들 옆에)
  const position = calculateAutoPosition(existingNodes);
  node.position = position;
  
  // 3. Canvas 상태 업데이트
  setNodes((prev) => [...prev, node]);
  
  // 4. 토스트 알림
  toast.success(`"${node.data.display_name}" 노드가 생성되었습니다`);
}
```

### 4.2 Teaching Node Component

Canvas에서 렌더링되는 Teaching 노드:

```typescript
// components/canvas/DimensionCapsuleNode.tsx (현행)

interface TeachingNodeData {
  capsule_id: string;
  display_name: string;
  inputs: Record<string, unknown>;
  locked_inputs: string[];  // 채팅에서 채운 값
  output: Record<string, unknown>;
  editable: boolean;
  executed: boolean;
}

function TeachingCapsuleNode({ data, id }: NodeProps<TeachingNodeData>) {
  const [isEditing, setIsEditing] = useState(false);
  const [localInputs, setLocalInputs] = useState(data.inputs);
  const { byokKey } = useBYOK();
  const { refresh: refreshCredits } = useCreditContext();

  const handleReExecute = async () => {
    // 수정된 파라미터로 재실행
    const result = await api.post(
      getEndpointForCapsule(data.capsule_id),
      localInputs,
      getBYOKHeaders(byokKey)
    );
    
    // 노드 출력 업데이트
    updateNodeData(id, { output: result.output, executed: true });
    refreshCredits();
  };

  return (
    <div className="teaching-capsule-node">
      <div className="node-header">
        <span className="node-icon">{getIcon(data.capsule_id)}</span>
        <span className="node-title">{data.display_name}</span>
        {data.executed && <span className="executed-badge">✓</span>}
      </div>
      
      <div className="node-inputs">
        {Object.entries(localInputs).map(([key, value]) => (
          <InputField
            key={key}
            label={key}
            value={value}
            locked={data.locked_inputs.includes(key)}
            onChange={(v) => setLocalInputs({ ...localInputs, [key]: v })}
            disabled={!isEditing}
          />
        ))}
      </div>
      
      <div className="node-actions">
        <button onClick={() => setIsEditing(!isEditing)}>
          {isEditing ? "저장" : "수정"}
        </button>
        <button onClick={handleReExecute} disabled={isEditing}>
          재실행
        </button>
      </div>
      
      {/* Output Handles for Pipeline */}
      <Handle type="source" position={Position.Right} id="output" />
      <Handle type="target" position={Position.Left} id="input" />
    </div>
  );
}
```

### 4.3 Pipeline Connection

노드 간 연결 시 데이터 전달:

```typescript
// hooks/usePipelineExecution.ts

function usePipelineExecution() {
  const { nodes, edges } = useReactFlow();

  const executePipeline = async (startNodeId: string) => {
    // 1. 위상 정렬로 실행 순서 결정
    const executionOrder = topologicalSort(nodes, edges, startNodeId);
    
    // 2. 순차 실행
    let context: Record<string, unknown> = {};
    
    for (const nodeId of executionOrder) {
      const node = nodes.find((n) => n.id === nodeId);
      
      // 3. Upstream 출력을 입력으로 전달
      const upstreamData = getUpstreamOutputs(nodeId, edges, nodes);
      const mergedInputs = { ...node.data.inputs, ...upstreamData };
      
      // 4. 노드 실행
      const result = await executeNode(node, mergedInputs);
      
      // 5. Context 업데이트
      context[nodeId] = result.output;
      
      // 6. 노드 상태 업데이트
      updateNodeData(nodeId, { output: result.output, executed: true });
    }
    
    return context;
  };

  return { executePipeline };
}
```

---

## 5) 파이프라인 예시

### 5.1 컨텐츠 제작 파이프라인

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Prompt Generator│────▶│ Storyboard Gen  │────▶│ Image Tool      │
│                 │     │                 │     │                 │
│ topic: "요리"    │     │ concept: (from  │     │ description:    │
│ style: "vlog"   │     │   upstream.     │     │   (from scene   │
│ duration: "2분" │     │   prompt)       │     │   description)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 5.2 데이터 흐름

```typescript
// Pipeline Data Flow Example

// 1. Prompt Generator Output
{
  prompt: "A cozy kitchen scene with soft natural lighting...",
  negative_prompt: "blurry, dark, overexposed",
  technical: { aspect_ratio: "16:9", duration: "15s" }
}

// 2. Storyboard Generator Input (upstream 자동 연결)
{
  concept: "A cozy kitchen scene with soft natural lighting...",  // ← from upstream
  scene_count: 5
}

// 3. Storyboard Generator Output
{
  scenes: [
    { scene_number: 1, description: "Opening shot of kitchen", camera: "wide" },
    { scene_number: 2, description: "Chef enters", camera: "medium" },
    ...
  ]
}

// 4. Image Tool Input (scene 1 자동 연결)
{
  description: "Opening shot of kitchen",  // ← from scene[0].description
  style: "photorealistic",
  aspect_ratio: "16:9"
}
```

---

## 6) 구현 체크리스트

> **Last Updated**: 2026-01-02

### Backend ✅
- [x] `DIMENSION_TOOLS` 스키마를 Agent chat system prompt에 추가 → `dimension_tools.py`
- [x] `execute_teaching_tool()` 함수 구현 → `_teaching_tool_handler()`
- [x] `build_node_spec()` 노드 변환 로직 → `build_teaching_node_spec()`
- [x] `agent.node_created` SSE 이벤트 발행 → L376-380
- [x] 기존 Teaching 엔드포인트와 통합 테스트 → 4개 tools 등록 확인

### Frontend ✅
- [x] `DimensionCapsuleNode` 컴포넌트 (React Flow) → `DimensionCapsuleNode.tsx`
- [x] `agent.node_created` 이벤트 핸들러 → `useAgentEvents.ts`
- [x] 노드 자동 배치 로직 → `calculateAutoPosition()`
- [x] 노드 파라미터 수정 UI → `NodeChatPanel.tsx`
- [x] 파이프라인 연결 + 순차 실행 → `usePipelineExecution.ts`

### Integration ✅
- [x] BYOK 헤더 전달 (Agent → Dimension) → `routers/dimension.py` 크레딧 로직
- [x] 크레딧 검사 + 402 에러 처리 → `credit_service.py`
- [x] 실행 결과 Canvas 저장 → Canvas state update in hooks

---

## 7) 참고 문서

| 문서 | 내용 |
|------|------|
| [04_CAPSULE_NODE_SPEC.md](file:///Users/ted/vivid/04_CAPSULE_NODE_SPEC.md) | 캡슐 노드 스키마 |
| [31_AGENT_STUDIO_ARTIFACT_SPEC_V1.md](file:///Users/ted/vivid/31_AGENT_STUDIO_ARTIFACT_SPEC_V1.md) | 아티팩트 타입 |
| [crebit_teaching_apps_spec.md](file:///Users/ted/vivid/docs/strategic/crebit_teaching_apps_spec.md) | Teaching Apps 현황 |
| [13_CREDITS_AND_BILLING_SPEC_V1.md](file:///Users/ted/vivid/13_CREDITS_AND_BILLING_SPEC_V1.md) | 크레딧 시스템 |

---

## 8) Change Log

- **v1.1 (2026-01-02)**: 구현 완료 ✅
  - Backend: teaching_tools.py, node_builder.py, agent_tool_executor.py
  - Frontend: usePipelineExecution.ts, useAgentEvents.ts, NodeChatPanel.tsx
  - 4개 Teaching Tools 통합, SSE agent.node_created 발행 확인
- v1.0 (2026-01-01): 초안 작성 - Tool Schema, Node 변환, Pipeline 연결 정의
