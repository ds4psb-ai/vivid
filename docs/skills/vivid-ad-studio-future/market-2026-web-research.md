# AD Studio 2026 H2 Web Research

확인일: 2026-02-13

이 문서는 조감독 기능 고도화를 위한 외부 근거 링크를 보관한다.

## A. Agentic Tooling Baseline

1. OpenAI Tools 가이드
- Built-in tools + remote MCP 서버 연동을 공식 가이드로 제시한다.
- 링크: [OpenAI - Built-in tools guide](https://platform.openai.com/docs/guides/tools)

2. OpenAI MCP 가이드
- remote MCP 연결 시 도구 신뢰 경계와 보안 위험(예: prompt injection) 주의를 공식 문서에서 명시한다.
- 링크: [OpenAI - MCP guide](https://platform.openai.com/docs/guides/tools-remote-mcp)

3. OpenAI 모델 최적화 가이드
- 기능 릴리즈를 "eval 중심 반복"으로 운영하는 실무 루틴을 제시한다.
- 링크: [OpenAI - model optimization guide](https://platform.openai.com/docs/guides/model-optimization)

## B. Video Engine Reality (Veo 중심)

1. Google Cloud Veo API 문서
- 모델별 capability와 입력 계약(예: style reference image 제한)을 명확히 문서화한다.
- 링크: [Google Cloud - Generate videos with Veo](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation)

2. Google DeepMind Veo 3 업데이트
- Veo 3/3.1, 이미지-영상 변환, 음성/오디오 결합 흐름을 제품 전략으로 공개한다.
- 링크: [Google DeepMind - Veo 3 and Veo 3 Fast](https://deepmind.google/models/veo/)

## C. Trust / Provenance Layer

1. C2PA 공식 스펙
- 생성 콘텐츠의 provenance/manifest 표준을 유지보수 가능한 계약으로 제공한다.
- 링크: [C2PA - Specifications](https://c2pa.org/specifications/)

2. Google SynthID 정책 문서
- 생성물 워터마크 검증 흐름(탐지 도구 포함)을 제시한다.
- 링크: [Google SynthID FAQ](https://deepmind.google/models/synthid/)

## D. Multi-shot Consistency Research

1. VGoT 논문
- 멀티샷 비디오 생성에서 장면 간 일관성(캐릭터/관계/카메라/조명)을 핵심 문제로 정의한다.
- 링크: [arXiv - VGoT](https://arxiv.org/abs/2412.02259)

2. GLASS 논문
- 긴 영상에서 일관성 유지와 계산 효율 문제를 함께 다루는 방향을 제시한다.
- 링크: [arXiv - GLASS](https://arxiv.org/abs/2505.14538)

## E. Product Decisions for Vivid AD Studio

1. Engine abstraction 유지
- 특정 모델/벤더에 종속된 prompt schema를 core schema에 직접 박지 않는다.

2. Provenance by default
- export JSON에 evidence + provenance 필드(현재 evidence_refs 기반)를 기본 포함한다.

3. Eval-first 배포
- 기능 완료 기준을 UI 데모가 아니라 회귀 테스트 + 품질 체크로 고정한다.

4. Continuity as first-class metric
- 장면 단위 품질보다 시퀀스 단위 연속성을 우선 지표로 본다.
- 2026-02-14 아키텍처 결정: AD Studio North Star를 `continuity_score`로 고정한다.
