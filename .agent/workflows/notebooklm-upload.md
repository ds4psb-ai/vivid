---
description: NotebookLM에 RAG 소스 파일 수동 업로드 워크플로우
---

# NotebookLM RAG 소스 업로드 가이드

## 개요
Vivid 프로젝트의 거장 감독 RAG 데이터를 NotebookLM에 업로드하는 수동 워크플로우입니다.
브라우저 보안 제한으로 자동화가 어려워 **드래그 앤 드롭** 방식을 사용합니다.

---

## 1. 소스 파일 위치

| 거장 | 폴더 경로 | 파일 수 |
|------|----------|--------|
| Bong Joon-ho | `/Users/ted/vivid/data/notebooklm_ready/bong/` | 11 |
| Wong Kar-wai | `/Users/ted/vivid/data/notebooklm_ready/wong/` | 11 |
| Denis Villeneuve | `/Users/ted/vivid/data/notebooklm_ready/villeneuve/` | 11 |
| Christopher Nolan | `/Users/ted/vivid/data/notebooklm_ready/nolan/` | 11 |
| Quentin Tarantino | `/Users/ted/vivid/data/notebooklm_ready/tarantino/` | 11 |

---

## 2. NotebookLM 노트북 생성

### 노트북 이름 규칙
```
{감독명} Source Packs 2026
```

### 생성할 노트북 목록
1. **Bong Joon-ho Source Packs 2026**
2. **Wong Kar-wai Source Packs 2026**
3. **Denis Villeneuve Source Packs 2026**
4. **Christopher Nolan Source Packs 2026**
5. **Quentin Tarantino Source Packs 2026**

---

## 3. 업로드 절차

### Step 1: NotebookLM 접속
```
https://notebooklm.google.com/
```
- Google 계정: `arkain.info@gmail.com` (아캐인)

### Step 2: 새 노트북 생성
1. **"새 노트북"** (또는 **"New Notebook"**) 클릭
2. 노트북 이름 입력 (위 규칙 참조)
3. 생성 완료

### Step 3: 소스 파일 업로드
1. Finder에서 해당 거장 폴더 열기:
   ```bash
   open /Users/ted/vivid/data/notebooklm_ready/bong/
   ```
2. 폴더 내 모든 `.md` 파일 선택 (`Cmd + A`)
3. NotebookLM 노트북 페이지로 **드래그 앤 드롭**
4. 업로드 완료 대기 (파일당 2-5초)

### Step 4: 검증
- 좌측 "소스" 패널에서 업로드된 파일 수 확인
- 각 거장당 **11개** 소스가 있어야 함

---

## 4. 빠른 폴더 열기 명령어

```bash
# Bong Joon-ho
open /Users/ted/vivid/data/notebooklm_ready/bong/

# Wong Kar-wai
open /Users/ted/vivid/data/notebooklm_ready/wong/

# Denis Villeneuve
open /Users/ted/vivid/data/notebooklm_ready/villeneuve/

# Christopher Nolan
open /Users/ted/vivid/data/notebooklm_ready/nolan/

# Quentin Tarantino
open /Users/ted/vivid/data/notebooklm_ready/tarantino/
```

---

## 5. 새 거장 추가 시

1. **JSON 소스 파일 생성**: `/Users/ted/vivid/data/source_packs/{director}/`
2. **Markdown 변환**: `python scripts/convert_json_to_docs.py`
3. **NotebookLM 업로드**: 위 절차 반복

---

## 6. 문제 해결

| 문제 | 해결책 |
|------|--------|
| 파일이 업로드되지 않음 | 파일 크기 확인 (NotebookLM 제한: 500KB/파일) |
| 한글 깨짐 | UTF-8 인코딩 확인 |
| 소스 인식 안됨 | `.md` 확장자 확인 |

---

## 참고 문서
- [RAG Data Protocol](file:///Users/ted/.gemini/antigravity/brain/4b7f3c43-e92e-45e7-90c3-af0e69e32e21/rag_data_protocol.md)
- [Source Pack JSON 원본](file:///Users/ted/vivid/data/source_packs/)
