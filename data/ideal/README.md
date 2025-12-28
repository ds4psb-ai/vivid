# Ideal Mock Data

이 디렉토리는 **이상적인 NotebookLM 출력 구조**를 정의합니다.

## 목적

1. **벤치마크**: 실제 NotebookLM 파이프라인 결과와 비교
2. **갭 분석**: 이상 vs 현실 차이 측정
3. **프롬프트 개선**: 분석 결과를 기반으로 Source Pack Protocol 개선

## 파일 구조

```
data/ideal/
├── bong_ideal_homage_guide.json   # 완전한 시각 언어 가이드
├── bong_ideal_beat_sheet.json     # 5막 비트시트 템플릿
├── bong_ideal_storyboard.json     # 12샷 스토리보드
├── bong_ideal_persona.json        # 감독 페르소나 프로파일
└── README.md                      # 이 파일
```

## 비교 사이클

```
Ideal Mock → Real NotebookLM Output → Gap Analysis → Prompt Improvement → Re-run
```

## 필드 커버리지 기준

| Guide Type | 필수 필드 |
|------------|-----------|
| homage | visual_language, color_palette, camera_motion, thematic_motifs |
| beat_sheet | beats (5개), transitions, tonal_markers |
| storyboard | shots (10+), composition, camera, lighting |
| persona | artistic_philosophy, thematic_obsessions, signature_techniques |
