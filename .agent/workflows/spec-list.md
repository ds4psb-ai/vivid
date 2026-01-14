---
description: SPEC 목록 조회 - 최근 SPEC 파일 확인
---

# SPEC List Workflow

> **목적**: 구현 가능한 SPEC 문서 목록 조회

// turbo-all

## 1. SPEC 파일 목록 (최근순)
```bash
echo "=== 📋 구현 가능한 SPEC 목록 ===" && \
ls -lt docs/specs/*.md 2>/dev/null | grep -v TEMPLATE | head -10
```

## 2. 각 SPEC 상태 확인
```bash
for f in docs/specs/*.md; do
  [[ $(basename "$f") == "TEMPLATE"* ]] && continue
  name=$(basename "$f" .md)
  status=$(grep -m1 "^상태:" "$f" 2>/dev/null || echo "상태: 미정")
  echo "• $name - $status"
done
```

---

**사용법**:
```
/execute [위 목록에서 선택]
```
