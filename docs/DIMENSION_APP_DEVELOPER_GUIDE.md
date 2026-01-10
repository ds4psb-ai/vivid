# Vivid Dimension 앱 개발자 공통 가이드

> **버전**: 1.0  
> **작성일**: 2026-01-10  
> **대상**: 개별 Dimension 앱 개발자  
> **목적**: 에코시스템 일관성 유지를 위한 단일 진실 문서

---

## 1. 핵심 원칙

### 1.1 자동 체이닝 아키텍처

각 앱은 **독립적으로 실행**되지만, **Singularity 템플릿 실행 시 체이닝**됩니다.

```
첫 입력 (topic, style...)
    ↓
1D (Prompt) → output.prompt
    ↓ 자동 전파
2D (Storyboard) → output.scenes
    ↓ 자동 전파
3D (Visual) → output.image_prompts
    ↓ 자동 전파
VEO (Video) → output.video_url
```

### 1.2 입출력 계약 (Contract)

**모든 앱은 다음을 준수해야 합니다:**

| 항목 | 규칙 |
|------|------|
| **입력** | `params: Dict[str, Any]` - 이전 차원 출력 자동 주입 |
| **출력** | `Dict[str, Any]` - 다음 차원이 사용할 필드 포함 |
| **메타데이터** | `credit_cost`, `model`, `duration_ms` 반환 |

---

## 2. 파일 구조 (앱 당)

```
config/apps/content/dimensions/{app_id}.yaml    ← SSoT (설정)
backend/app/routers/dimension/{app_id}.py       ← API 엔드포인트
backend/app/services/{app_id}_service.py        ← 비즈니스 로직 (선택)
frontend/src/components/dimension/{App}Panel.tsx ← UI 패널
```

---

## 3. YAML 설정 (SSoT)

모든 설정은 `config/apps/content/dimensions/{app_id}.yaml`에서 관리됩니다.

```yaml
$schema: "vivid-app/v2"

metadata:
  name: my-app
  type: dimension
  version: "1.0.0"

display:
  name_ko: "내 앱"
  name_en: "My App"
  icon: "🎬"

capabilities:
  - name: execution
    enabled: true
    config:
      credit_cost: 5              # 크레딧 비용 (프론트/백엔드 공통)
      capsule_key: "my-app.generate"
      endpoint: "/api/dimension/my-app/generate"
      
  - name: rag
    enabled: true
    config:
      mode: auteur_only          # auteur_only | dimension | hybrid
      confidence_threshold: 0.7
```

---

## 4. 입력 전파 규칙

`workflow_tools.py`의 `_prepare_dimension_inputs_tiered()`가 자동 전파합니다.

### 4.1 표준 입력 필드

| 필드 | 설명 | 전파 소스 |
|------|------|-----------|
| `topic` | 주제/컨셉 | 사용자 입력 or 이전 prompt |
| `style` | 스타일 | session 레벨 or 이전 출력 |
| `mood` | 분위기 | session 레벨 or 이전 출력 |
| `aspect_ratio` | 화면비 | session 레벨 |
| `language` | 언어(ko/en) | session 레벨 |

### 4.2 차원별 특수 입력

| 차원 | 특수 입력 | 소스 |
|------|----------|------|
| 2D | `concept`, `scene_count` | 1D.prompt, duration 기반 계산 |
| 3D | `description` | 2D.scenes[0].description |
| VEO | `prompt`, `duration` | 1D.prompt, session |
| QC | `content` | 이전 차원 전체 출력 (JSON) |

---

## 5. 출력 표준

### 5.1 필수 출력 필드

```python
return {
    # 핵심 결과
    "prompt": "생성된 프롬프트...",       # 다음 차원 전파용
    "description": "설명...",
    
    # 메타데이터 (자동 수집됨)
    "model": "gemini-3-flash",
    "duration_ms": 1234,
    "credit_cost": 5,
    
    # 선택: 상세 결과
    "scenes": [...],                      # 2D
    "image_prompts": [...],               # 3D
    "video_url": "...",                   # VEO
}
```

### 5.2 QC 호환 출력

QC가 검수할 수 있도록 **의미 있는 텍스트 필드**를 포함하세요:

```python
# ❌ Bad: QC가 검수할 수 없음
return {"result": {"data": [...]}}

# ✅ Good: QC가 검수 가능
return {
    "prompt": "생성된 프롬프트 텍스트...",
    "scenes": [{"description": "..."}],
}
```

---

## 6. RAG 연동

### 6.1 거장 스타일 주입

```python
from app.rag.rag_presets import get_auteur_style_hints

# auteur_style이 세션에 있으면 자동 주입됨
hints = get_auteur_style_hints("bong")
# {'camera_style': 'tracking', 'aspect_ratio': '2.35:1', ...}
```

### 6.2 차원별 RAG 검색

```python
from app.rag.tier1_dimension_rag import get_dimension_rag

rag = get_dimension_rag("AD")  # Aesthetic Director용
results = await rag.search(query, limit=5)
```

---

## 7. 크레딧 비용

### 7.1 SSoT에서 가져오기

```python
from app.core.app_registry import AppRegistry

app = AppRegistry.get_by_capsule_key("my-app.generate")
exec_cap = app.get_capability("execution")
cost = exec_cap.config.get("credit_cost", 5)
```

### 7.2 크레딧 차감 (자동)

`dimension_adapter.py`에서 자동 차감됩니다. 앱 개발자가 직접 호출할 필요 없습니다.

---

## 8. Singularity 템플릿 연동

### 8.1 템플릿 구조

```python
template = {
    "tool_sequence": ["1D", "2D", "VEO"],  # 차원 실행 순서
    "input_preset": {                      # 첫 차원 초기값
        "intent": {...},                   # Phase 3 Intent 스키마
        "legacy_params": {...},            # 기존 파라미터 (하위호환)
    }
}
```

### 8.2 Intent 기반 파라미터

앱이 `input_preset`에서 Intent를 활용하려면:

```python
from app.resolvers.integration import extract_intent_from_preset

intent, legacy_params = extract_intent_from_preset(input_preset)
if intent:
    # intent.mood, intent.pace, intent.target 등 사용
    pass
```

---

## 9. 옵션 추가 시 체크리스트

새로운 옵션/파라미터 추가 시:

- [ ] `config/apps/content/dimensions/{app}.yaml` 업데이트
- [ ] `_prepare_dimension_inputs_tiered()` 에 전파 로직 추가 (필요시)
- [ ] 프론트엔드 UI에 옵션 노출
- [ ] 출력에 새 필드 포함 (다음 차원 전파 필요시)
- [ ] QC 검수 대상 여부 확인

---

## 10. 테스트

### 10.1 단위 테스트

```bash
cd backend && pytest -v tests/test_dimension_{app}.py
```

### 10.2 E2E 테스트

```bash
cd frontend && npx playwright test dimension.spec.ts
```

### 10.3 체이닝 테스트

Singularity에서 템플릿 선택 후 전체 워크플로우 실행:

```
1. http://localhost:3100/singularity 접속
2. 템플릿 선택 (예: "시네마틱 프롬프트 마스터")
3. 첫 입력만 작성
4. 전체 차원 자동 실행 확인
```

---

## 11. 참고 문서

| 문서 | 경로 |
|------|------|
| 앱 설정 SSoT | `config/apps/README.md` |
| 파이프라인 흐름 | `08_PIPELINES_AND_USER_FLOWS.md` |
| 아키텍처 철학 | `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` |
| 개발 현황 | `docs/DEVELOPER_STATUS_GUIDE.md` |
| Intent 스키마 | `backend/app/schemas/creative_intent.py` |
| 워크플로우 도구 | `backend/app/agents/workflow_tools.py` |

---

## 12. FAQ

### Q: 새 옵션 추가하면 기존 템플릿이 깨지나요?

**A**: 아니요. `legacy_params`가 하위 호환 레이어 역할을 합니다. 새 옵션은 기본값이 적용됩니다.

### Q: QC를 여러 곳에 배치할 수 있나요?

**A**: 네. `tool_sequence`에서 원하는 위치에 "QC"를 삽입하면 됩니다:
```python
["STORY", "2D", "QC", "3D", "QC", "VEO"]  # 스토리보드와 이미지 각각 검수
```

### Q: 크레딧 비용을 동적으로 변경하려면?

**A**: `config/apps/content/dimensions/{app}.yaml`의 `credit_cost`만 수정하면 프론트/백엔드 모두 자동 반영됩니다.
