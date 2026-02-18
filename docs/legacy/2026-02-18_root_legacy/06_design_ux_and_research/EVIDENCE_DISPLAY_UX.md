# EvidenceDisplay UI/UX 가이드

## 패널별 적용 규칙

| 패널 | Dimension | 테마 | 기본 노출 조건 |
|------|-----------|------|---------------|
| ReferenceDecoderPanel | 4D | amber | `evidence_refs` 있을 때 |
| VisualRealizerPanel | 3D | emerald | `evidence_refs` 있을 때 |
| PromptGeneratorPanel | 1D | violet | `evidence_refs` 있을 때 |
| AestheticDirectorPanel | AD | - | *(현재 미연결)* |
| QualityDirectorPanel | QC | - | *(현재 미연결)* |

---

## 노출/숨김/상태 규칙

### 1. Evidence가 있을 때 (evidence_refs.length > 0)

| 조건 | 동작 |
|------|------|
| confidence ≥ 0.5 | 섹션 펼침 (기본) |
| confidence < 0.5 | 섹션 접힘 + "(신뢰도 낮음)" 표시 |
| refs ≤ 3개 | 전체 표시 |
| refs > 3개 | 3개 표시 + "더보기" 버튼 |

### 2. Evidence가 없을 때 (evidence_refs.length === 0)

| 옵션 | 현재 선택 | 근거 |
|------|----------|------|
| **완전히 숨김** | ✅ 채택 | 불필요한 UI 노이즈 최소화 |
| "근거 없음" 메시지 표시 | ❌ | 사용자 혼란 방지 |

> **결정**: Evidence가 없으면 섹션 자체를 렌더링하지 않음. 이는 RAG 결과가 없거나 신뢰도가 너무 낮아 추천을 스킵한 경우에 해당.

### 2.1 미연결 패널 안내

AD/QC 패널은 현재 RAG suggest API를 호출하지 않으므로 EvidenceDisplay가 노출되지 않습니다.  
필요 시 `RAGSuggestionCard` 연동 후 동일 규칙을 적용합니다.

### 3. 렌더링 조건 정리

```tsx
// EvidenceDisplay 내부 로직
if (!Array.isArray(refs) || refs.length === 0) {
  return null;  // 완전히 숨김
}
```

---

## 접근성 (Accessibility)

| 요소 | aria 속성 |
|------|-----------|
| 펼침/접기 버튼 | `aria-expanded`, `aria-label="AI 근거 펼치기/접기"` |
| 더보기 버튼 | `aria-label="나머지 N개 근거 보기"` |
| 접기 버튼 | `aria-label="근거 목록 접기"` |

---

## 데이터 형식

### evidence_refs 배열 아이템

```typescript
interface EvidenceRef {
  ref_id: string;       // db:rag_docs:{dim}:{dataset}:{doc_id}
  source?: string;      // "db"
  content_preview?: string;  // 최대 200자
  dataset_id?: string;  // "video_ref", "image_grid" 등
  dataset_label?: string;  // 사용자 친화적 라벨
  score?: number;       // 0.0 ~ 1.0
}
```

### 포맷 규칙

- `ref_id`: 항상 `db:rag_docs:{dimension}:{dataset_id}:{doc_id}` 형식
- `score`: null/NaN → 표시 안함, 0 이하 → 표시 안함
- `dataset_label`: 없으면 `dataset_id` fallback
