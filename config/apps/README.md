# Vivid App Standardization Framework v2

> **Updated**: 2026-01-09
> **Status**: SSoT 통합 완료

## 개요

YAML 기반 선언적 앱 설정 시스템입니다. 새 거장이나 차원 도구를 5분 내에 추가할 수 있습니다.

**YAML 수정만으로 프론트엔드 + 백엔드 설정이 자동 동기화됩니다.**

## 빠른 시작

### 새 거장 추가 (5분)

```bash
python scripts/vivid_app.py create auteur miyazaki \
  --display-name "미야자키 하야오" \
  --icon "🌿" \
  --themes "자연,성장,비행" \
  --style "camera_style=contemplative,color_grade=warm"
```

### 새 차원 도구 추가 (3분)

```bash
python scripts/vivid_app.py create dimension music \
  --display-name "음악 생성기" \
  --icon "🎵" \
  --rag-mode always
```

## CLI 명령어

| 명령어 | 설명 |
|--------|------|
| `list` | 등록된 앱 목록 |
| `list --type auteur` | 거장만 필터 |
| `validate` | 모든 설정 검증 |
| `reload` | Registry 핫 리로드 |
| `create auteur <name>` | 새 거장 생성 |
| `create dimension <name>` | 새 차원 생성 |

## 디렉토리 구조

```
config/apps/
├── schema.py           # Pydantic 스키마
└── content/
    ├── auteurs/        # 7 거장
    │   ├── bong.yaml
    │   ├── nolan.yaml
    │   └── ...
    └── dimensions/     # 10 차원
        ├── ad.yaml
        ├── story.yaml
        └── ...
```

## YAML 스키마 (v2.1 - SSoT 통합)

```yaml
$schema: "vivid-app/v2"

metadata:
  name: bong
  type: auteur  # or dimension
  version: "1.0.0"
  bounded_context: content

display:
  name_ko: "봉준호"
  name_en: "Bong Joon-ho"
  icon: "🎬"

capabilities:
  - name: rag
    enabled: true
    config:
      mode: auteur_only
      confidence_threshold: 0.7
      
  - name: cache
    enabled: true
    config:
      ttl: 7200

  # [NEW] 실행 설정 - 크레딧 비용 SSoT
  - name: execution
    enabled: true
    config:
      credit_cost: 5            # 프론트엔드/백엔드 공통 SSoT
      endpoint: "/api/dimension/1d/generate"
      capsule_key: "teaching.prompt.generate"

extensions:
  auteur:
    corpus_type: v-shape
    sources:
      - type: source_pack
        path: data/source_packs/bong/*.json
    style_hints:
      camera_style: tracking
      aspect_ratio: "2.35:1"
    themes:
      - 사회적 계급
      - 장르 블렌딩

keywords:
  patterns:
    - "bong"
    - "봉준호"
    - "기생충"
```

## SSoT 통합 현황 (2026-01-09)

| 연동 영역 | 상태 | 설명 |
|-----------|------|------|
| `/api/dimension/tools` | ✅ | 프론트엔드 DimensionConfigContext |
| `get_credit_cost()` | ✅ | 백엔드 실제 크레딧 차감 |
| `rag_presets.py` | ✅ | RAG capability 동적 로딩 |

## 코드에서 사용

```python
from app.core.app_registry import AppRegistry

# 초기화
AppRegistry.discover("config/apps")

# 조회
app = AppRegistry.get_by_name("bong")
app = AppRegistry.get_by_keyword("기생충 스타일")
apps = AppRegistry.get_by_type(AppType.AUTEUR)
apps = AppRegistry.get_by_capability("rag")

# 스타일 힌트
from app.rag.rag_presets import get_auteur_style_hints
hints = get_auteur_style_hints("bong")
# {'camera_style': 'tracking', 'aspect_ratio': '2.35:1', ...}

# 크레딧 비용 (SSoT)
exec_cap = app.get_capability("execution")
credit_cost = exec_cap.config.get("credit_cost", 5)
```

## 아키텍처 패턴

- **Microkernel**: Capability 기반 플러그인 시스템
- **Hexagonal**: Core(schema) + Adapters(YAML parser)
- **Registry**: 타입/기능/키워드 기반 동적 조회
- **DDD**: Bounded Context 분리
- **SSoT**: 단일 진실 원천 (YAML → Frontend + Backend)
