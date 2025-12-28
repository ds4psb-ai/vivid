# Implementation Roadmap: Node Canvas → AI Shortform OTT

**작성**: 2025-12-24  
**버전**: Reference v1.0  
**목표**: MVP → 숏드라마/숏필름/숏애니메이션 OTT 고도화  

---

**정본 원칙/흐름**: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`, `10_PIPELINES_AND_USER_FLOWS.md`
**문서 맵**: `00_DOCS_INDEX.md`

---

## Phase 0: 문서/리서치 정본화 (현재)

- 최신 아키텍처/도구 리서치 완료
- NotebookLM / Opal 활용 전략 확정
- 기술 명세서 및 로드맵 정리
- Sheets Bus → DB SoR 마이그레이션 기준 정리
- Pattern Library/Trace 기본 스키마 정의
- 파이프라인/사용자 흐름 문서 확정

---

## Phase 1: Node Canvas MVP (0~12주)

### 핵심 목표
- 거장 데이터화 파이프라인 (Gemini 구조화 → DB SoR → NotebookLM)
- 통 데이터셋(Visual/Persona/Synapse) 구조 정립
- 캔버스 편집 + 저장/불러오기
- 기본 Spec 생성 및 미리보기
- 템플릿 저장/공유 (초기)
- 거장 템플릿 카드 → 캔버스 시작 플로우
- 캡슐 노드(Sealed Node) v1 적용

### 주요 작업
- Sheets 스키마 v1 + NotebookLM 출력 규격 v1
- Gemini 구조화 출력 (ASR/키프레임/샷) → Video Schema DB 구축
- Creator Self-Style 노트북 수집/요약 루틴 확정
- Synapse Logic(변환 규칙) 가이드 출력 규격 추가
- Derived → DB 승격 파이프라인 (Pattern Library/Trace)
- Canvas UI (ReactFlow 기반) 완성
- Graph persistence (Postgres JSONB)
- 템플릿 갤러리/카드 UI + 템플릿으로 새 캔버스 생성
- 캡슐 노드 스펙/버전 관리 + 노출 파라미터 UI
- 캡슐 실행 API + 요약 출력 + 증거 참조 정책
- Spec Engine v1 (규칙 기반)
- GA 프로토타입 (상위 3 추천)
- 인증/기본 권한 (템플릿 공개/비공개)
- NotebookLM/Opal Derived 결과 **Sheets Bus 기록** 규격 확정
- Pattern Library/Trace **DB 승격 파이프라인** 설계

### NotebookLM/Opal 활용
- 역할/흐름 정본: `10_PIPELINES_AND_USER_FLOWS.md`
- 영상 구조화 기준: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- 실행 정책/보안: `05_CAPSULE_NODE_SPEC.md`

---

## Phase 2: Optimization + Marketplace (3~6개월)

### 핵심 목표
- GA/RL 정식 도입
- 템플릿 마켓 베타 오픈
- 사용자 피드백 루프 구축

### 주요 작업
- GA 고도화 (adaptive mutation, multi-objective)
- RL/밴딧 추천 시스템 구축
- 템플릿 마켓 (검색/태그/판매)
- 실시간 미리보기 최적화

---

## Phase 3: AI Shortform Studio (6~12개월)

### 핵심 목표
- 숏드라마/숏필름/숏애니 생성 파이프라인 구축
- Script → Storyboard → Scene 생성 자동화

### 주요 작업
- Script/Beat Sheet 생성
- Storyboard 자동화 (컷 시퀀스)
- Scene 생성 파이프라인 (영상/이미지/오디오)
- Asset Library + Provenance 기록

### NotebookLM/Opal 활용
- NotebookLM: 시나리오/세계관 문서 요약 → 노드 템플릿화
- Opal: 로컬라이징, 자막/번역, QA 자동화 도구화

---

## Phase 4: OTT 고도화 (12~24개월)

### 핵심 목표
- 넷플릭스형 OTT급 개인화/배포 체계 구축
- 콘텐츠 대량 생산 + 추천/퍼블리싱 자동화

### 주요 작업
- 개인화 추천 엔진 (취향 기반/행동 기반)
- 시즌/에피소드 구조 자동 생성
- 멀티랭귀지 배포 파이프라인
- 콘텐츠 품질 자동 평가 + 휴먼 인더 루프
- 라이선스/권리 관리 + 수익 정산 자동화

---

## 기술 확장 로드맵 (핵심 인프라)

- **MVP**: 단일 서비스 + 최소 DB + Sheets Bus
- **Scale**: 이벤트 기반 큐 + 관찰성 + GPU 클러스터
- **OTT**: 멀티 리전 배포 + 캐싱 + 품질 평가 자동화

---

## 리스크 & 대응

- **품질 변동**: 자동 평가 지표 + 휴먼 검수 루프
- **비용 폭증**: 저비용 프리뷰 vs 고품질 최종 생성 분리
- **IP/저작권**: provenance 기록 + 워터마킹 + 라이선스 관리

---

## 마일스톤 요약

- **MVP**: 캔버스 + 저장/불러오기 + 템플릿 카드 + 캡슐 노드 v1 + GA 프로토타입
- **6개월**: 최적화 추천 + 템플릿 마켓
- **12개월**: AI 숏드라마/숏필름/숏애니 파이프라인
- **24개월**: OTT급 개인화/배포 시스템
