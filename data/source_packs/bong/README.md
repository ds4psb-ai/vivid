# 봉준호 클러스터 소스 팩

> **클러스터 ID**: CL_BONG_01  
> **생성일**: 2025-12-29  
> **프로토콜**: 4-Layer Source Architecture v1

---

## 구조

```
bong/
├── layer0_raw/                    # 원본 증거
│   └── shot_analysis_chunks.json  # 5개 샷 분석 (청크 메타데이터 포함)
├── layer1_structured/             # 구조화 지식
│   └── logic_persona_vectors.json # Logic Vector + Persona Vector
├── layer2_synthesized/            # 합성 가이드
│   └── variation_guide_ko.md      # 오마주 변주 가이드 (한국어)
└── layer3_accumulated/            # 축적 지식
    └── accumulated_wisdom.json    # 메타 인사이트 (초기 상태)
```

---

## 포함 작품

| 작품 | 연도 | 샷 수 | Temporal Phases |
|------|------|-------|-----------------|
| 기생충 | 2019 | 3 | HOOK, BUILD, PAYOFF |
| 설국열차 | 2013 | 1 | HOOK |
| 살인의 추억 | 2003 | 1 | HOOK |

---

## 토큰 추정

- **Layer 0**: ~4,250 tokens
- **Layer 1**: ~2,800 tokens
- **Layer 2**: ~1,500 tokens (markdown)
- **Layer 3**: ~500 tokens
- **총계**: ~9,050 tokens (NotebookLM 50 source 제한 내)

---

## NotebookLM 적재 순서

1. Layer 0 JSON → Google Docs 변환 후 업로드
2. Layer 1 JSON → Google Docs 변환 후 업로드
3. Layer 2 Markdown → 직접 업로드 가능
4. Layer 3 → 축적 루프 시작 전까지 대기

---

## Knowledge Accumulation Loop

```
[가이드 생성] → [품질 검증] → [Notes 추출] → [Source 변환] → [Layer 3 갱신]
     └──────────────────────────────────────────────────────────┘
```

**현재 상태**: 초기 시드 (iteration 0)

---

## 근거 연결

모든 청크는 `evidence_refs` 필드를 통해 DB 레코드에 연결됨.
예: `db:shot:bong-2019-parasite-hook-001`
