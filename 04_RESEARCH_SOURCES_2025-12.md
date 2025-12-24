# Research Sources (2025-12 기준)

이 문서는 최신 아키텍처/도구 업데이트 확인을 위한 참고 자료 목록입니다.

## NotebookLM

- Google Workspace Updates (2025-12): Enhanced NotebookLM experience (Ultra tier)
  - https://workspaceupdates.googleblog.com/2025/12/google-ai-ultra-business-enhanced-notebooklm.html
- Google Workspace Updates (2025-03): Mind Map + Output Language selector
  - https://workspaceupdates.googleblog.com/2025/03/new-features-available-in-notebooklm.html
- Google Labs Blog (2025-07): Video Overviews + Studio upgrades
  - https://blog.google/technology/google-labs/notebooklm-video-overviews-studio-upgrades/

## Google Opal

- Google Developers Blog (2025-07): Introducing Opal (mini-apps, workflows, sharing)
  - https://developers.googleblog.com/en/introducing-opal/
- Google Labs Blog (2025-12): Opal in Gemini web app (experimental Gems)
  - https://blog.google/technology/google-labs/mini-apps-opal-gemini-app-experiment/
- Opal Developer Docs (overview / quickstart)
  - https://developers.google.com/opal

## 아키텍처 참고

- Google Cloud AI/ML architecture overview
  - https://docs.cloud.google.com/architecture/ai-ml
- AWS Generative AI inference architecture (Prescriptive Guidance)
  - https://docs.aws.amazon.com/prescriptive-guidance/latest/gen-ai-inference-architecture-and-best-practices-on-aws/introduction.html
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

- NotebookLM: Video/Audio Overviews, Studio 다중 출력, Mind Map, 출력 언어 선택이 강화됨
- Opal: 미니앱/워크플로우 시각 편집과 공유 중심의 실험적 도구로 발전
- 아키텍처: 이벤트 기반 분리, 관찰성, 비용/지연 최적화가 핵심 베스트 프랙티스
- 운영 전제: NotebookLM/Opal Ultra 구독 활성화 (현재)
- Sheets API: 배치 호출, 2MB payload 권장, per-minute quota, exponential backoff 필요
