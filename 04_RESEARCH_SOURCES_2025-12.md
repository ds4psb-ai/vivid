# Research Sources (2025-12 기준)

이 문서는 **레퍼런스 목록**이며, 제품 결정/계약은 SoR 문서에 반영한다.
정본 문서 맵: `00_DOCS_INDEX.md`

## NotebookLM

- Google Workspace NotebookLM 제품 소개 (소스 유형/보안/인용)
  - https://workspace.google.com/products/notebooklm/
- NotebookLM Help: Audio Overview (Studio 출력, 백그라운드 생성/공유)
  - https://support.google.com/notebooklm/answer/16212820?hl=en
- NotebookLM Help: Add or discover new sources (source 타입/제한/Deep Research)
  - https://support.google.com/notebooklm/answer/16215270?hl=en
- NotebookLM Help: Output Language (출력 언어 선택)
  - https://support.google.com/notebooklm/answer/16261963?hl=en
- Google Labs Blog (2024-12): NotebookLM Plus, Audio Overview 인터랙션, Sources/Chat/Studio UI
  - https://blog.google/technology/google-labs/notebooklm-new-features-december-2024/

## NotebookLM (릴리즈 추적/Watchlist)

- Google Workspace Updates (2025-12): Enhanced NotebookLM experience (Ultra tier)
  - https://workspaceupdates.googleblog.com/2025/12/google-ai-ultra-business-enhanced-notebooklm.html
- Google Workspace Updates (2025-03): Mind Map + Output Language selector
  - https://workspaceupdates.googleblog.com/2025/03/new-features-available-in-notebooklm.html
- Google Labs Blog (2025-07): Video Overviews + Studio upgrades
  - https://blog.google/technology/google-labs/notebooklm-video-overviews-studio-upgrades/
- Google Labs Blog (2025-12): Data Tables (Sheets export)
  - https://blog.google/technology/google-labs/notebooklm-data-tables/

## Google Opal

- Google Developers Blog (2025-07): Introducing Opal (mini-apps, workflows, sharing)
  - https://developers.googleblog.com/en/introducing-opal/
- Google Labs Blog (2025-12): Opal in Gemini web app (experimental Gems)
  - https://blog.google/technology/google-labs/mini-apps-opal-gemini-app-experiment/
- Opal Developer Docs (overview / quickstart)
  - https://developers.google.com/opal

## Gemini Video Understanding / Structured Outputs (2025-12)

- Gemini API: Video understanding (timestamps, multi-video input)
  - https://ai.google.dev/gemini-api/docs/video-understanding
- Gemini API: Structured outputs (JSON Schema)
  - https://ai.google.dev/gemini-api/docs/structured-output
- Vertex AI: Video understanding (Gemini 3 Pro/Flash)
  - https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding
- Google Blog: Gemini 3 Pro vision (video understanding focus)
  - https://blog.google/technology/developers/gemini-3-pro-vision/

## 아키텍처 참고

- Microsoft RAG Solution Design & Evaluation Guide (2025-12)
  - https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide
- Databricks LLMOps Workflows (LLMOps 변화점, 평가/피드백, 벡터 인덱스)
  - https://docs.databricks.com/aws/en/machine-learning/mlops/llmops
- Azure GenAIOps Reference Architecture (CI/CD, Dev/QA/Prod, 모니터링)
  - https://raw.githubusercontent.com/Azure/GenAIOps/main/documentation/reference_architecture.md
- AWS Generative AI inference architecture (운영/지연/비용 스케일링)
  - https://docs.aws.amazon.com/prescriptive-guidance/latest/gen-ai-inference-architecture-and-best-practices-on-aws/introduction.html
- Google Cloud AI/ML architecture overview
  - https://docs.cloud.google.com/architecture/ai-ml
- Microsoft event-driven architecture guide
  - https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven

## Sheets API 참고

- Sheets API usage limits / quotas
  - https://developers.google.com/sheets/api/limits
- Values append
  - https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append
- Values batchGet / batchUpdate
  - https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchGet
  - https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchUpdate

## Key takeaways (2025-12)

- NotebookLM: Sources/Chat/Studio 3패널, Audio Overview/인터랙션, 출력 언어 선택, 다양한 소스/인용 지원
- Opal: 자연어 → 멀티스텝 워크플로우(프롬프트/모델/툴 체인) → 미니앱 공유/호스팅
- Gemini 3 Pro: Video understanding + Structured Outputs(JSON Schema)로 장면/샷 구조화 데이터화 가능
- RAG: chunking → enrichment → embedding → index → hybrid search → 평가(groundedness, relevancy 등) 단계 분리 필요
- LLMOps: 프롬프트/체인도 버전 관리 아티팩트, 휴먼 피드백 기반 평가/모니터링 필수
- 운영/인프라: Dev/QA/Prod 분리, CI/CD, 모니터링/알림, 비용/지연 최적화가 최신 기준
- Sheets API: 배치 호출, 2MB payload 권장, per-minute quota, exponential backoff 필요
