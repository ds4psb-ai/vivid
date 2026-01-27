"""
VDG Extractor - Video Data Graph Analysis Extraction Utilities

Extracted from outliers.py for better maintainability.
Provides functions to extract various fields from VDG analysis results.

Usage:
    from app.services.vdg_extractor import (
        extract_hook_pattern, extract_shotlist, translate_vdg_to_korean
    )
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


# ==================
# KOREAN TRANSLATION LAYER
# ==================

VDG_KOREAN_MAP = {
    # Camera shots
    "LS": "롱샷 (LS)",
    "MS": "미디엄샷 (MS)",
    "CU": "클로즈업 (CU)",
    "ECU": "익스트림 CU",
    "WS": "와이드샷 (WS)",
    "MCU": "미디엄 CU",
    "OTS": "오버더숄더",
    "POV": "1인칭 시점",
    "FS": "풀샷 (FS)",
    "2-Shot": "투샷",
    "3-Shot": "쓰리샷",
    "Group Shot": "그룹샷",
    # Camera moves
    "zoom_in": "줌인",
    "zoom_out": "줌아웃",
    "pan": "패닝",
    "tilt": "틸트",
    "dolly": "돌리",
    "track": "트래킹",
    "static": "고정샷",
    "handheld": "핸드헬드",
    "track_back": "트래킹백",
    "shake_effect": "흔들림 효과",
    "follow": "팔로우샷",
    # Camera angles
    "eye": "아이레벨",
    "low": "로우앵글",
    "high": "하이앵글",
    "dutch": "더치앵글",
    # Narrative roles
    "Action": "액션",
    "Reaction": "리액션",
    "Hook": "훅",
    "Setup": "셋업",
    "Payoff": "페이오프",
    "Conflict": "갈등",
    "Resolution": "해결",
    "Main Event": "메인 이벤트",
    "Full Sketch": "풀 스케치",
    "Hook & Setup": "훅 & 셋업",
    "Climax": "클라이맥스",
    "Outro": "아웃트로",
    "Transition": "전환",
    # Hook patterns
    "pattern_break": "패턴 브레이크",
    "question": "질문",
    "reveal": "공개/리빌",
    "transformation": "변신",
    "unboxing": "언박싱",
    "challenge": "챌린지",
    # Edit pace
    "real_time": "실시간",
    "fast": "빠른 편집",
    "slow": "슬로우",
    "jump_cut": "점프컷",
    "medium": "보통 속도",
    # Audio events
    "impact_sound": "충격음",
    "crowd_laughter": "관객 웃음",
    "speech": "대사",
    "music": "음악",
    "ambient": "환경음",
    "sfx": "효과음",
    "silence": "무음",
    "Laughter": "웃음",
    "Dialogue": "대화",
    "Buzzer": "버저음",
    "Applause": "박수",
    "Voiceover": "내레이션",
    "Sound Effect": "효과음",
    "Background Music": "배경 음악",
    # Visual style / Lighting
    "Stage Lighting": "무대 조명",
    "Natural": "자연광",
    "Dramatic": "드라마틱 조명",
    "Soft": "소프트 조명",
    "High Key": "하이키 조명",
    "Low Key": "로우키 조명",
    "High Key Studio": "스튜디오 조명",
    "Warm/Indoor": "따뜻한 실내광",
    "Outdoor": "야외광",
    "Neon": "네온 조명",
    "Cinematic": "시네마틱",
}


def translate_term(term: str) -> str:
    """Translate a single English term to Korean"""
    if not term:
        return term
    return VDG_KOREAN_MAP.get(term, term)


# ==================
# HOOK PATTERN REGISTRY (P7: 근본 개선)
# ==================

HOOK_PATTERN_REGISTRY = {
    # 질문/호기심 유발형
    "question_hook": {
        "name_ko": "질문형 훅",
        "name_en": "Question Hook",
        "description": "시청자의 호기심을 자극하는 질문으로 시작",
        "why_effective": "인간의 본능적인 답을 알고 싶은 욕구를 자극하여 끝까지 시청 유도",
        "example": "'이게 진짜 될까요?' 형태의 오프닝",
        "difficulty": "easy",
    },
    "curiosity_gap": {
        "name_ko": "호기심 갭",
        "name_en": "Curiosity Gap",
        "description": "정보를 불완전하게 제시하여 나머지를 알고싶게 만듦",
        "why_effective": "미완성 정보에 대한 인지적 긴장감이 시청 지속을 유도",
        "example": "'이렇게 하면...' (결과는 영상 후반에)",
        "difficulty": "medium",
    },
    # 시각적 충격형
    "shock_reveal": {
        "name_ko": "충격 공개",
        "name_en": "Shock Reveal",
        "description": "예상치 못한 반전이나 놀라운 장면으로 시작",
        "why_effective": "도파민 급상승으로 뇌가 '더 보고 싶다' 신호 발생",
        "example": "변신 전후, 예상 외 결과물",
        "difficulty": "medium",
    },
    "visual_punch": {
        "name_ko": "비주얼 펀치",
        "name_en": "Visual Punch",
        "description": "강렬한 시각적 자극으로 스크롤 중단 유도",
        "why_effective": "인간 뇌는 움직임과 대비가 큰 이미지에 자동 반응",
        "example": "빠른 동작, 밝은 색상 대비",
        "difficulty": "easy",
    },
    "pattern_break": {
        "name_ko": "패턴 브레이크",
        "name_en": "Pattern Break",
        "description": "예상 패턴을 깨는 예외적 상황 제시",
        "why_effective": "뇌의 '예측 오류' 신호가 주의력을 강제 집중시킴",
        "example": "일반적 상황에서 갑자기 비정상적 전개",
        "difficulty": "hard",
    },
    # POV/몰입형
    "pov": {
        "name_ko": "1인칭 시점",
        "name_en": "POV (Point of View)",
        "description": "시청자가 직접 경험하는 것처럼 1인칭 시점으로 촬영",
        "why_effective": "자기 투영으로 감정적 몰입도 극대화, 공감 유발",
        "example": "'내가 이 상황이라면?' 느낌의 촬영",
        "difficulty": "easy",
    },
    "confession": {
        "name_ko": "고백형",
        "name_en": "Confession",
        "description": "개인적인 이야기나 비밀을 털어놓는 형식",
        "why_effective": "친밀감 형성으로 시청자와 감정적 유대 생성",
        "example": "솔직한 경험담, 실패 스토리 공유",
        "difficulty": "medium",
    },
    # 비교/변화형
    "before_after": {
        "name_ko": "전후 비교",
        "name_en": "Before & After",
        "description": "변화의 결과물을 먼저 보여주고 과정을 설명",
        "why_effective": "성공적인 결과에 대한 기대감으로 과정까지 시청 유도",
        "example": "다이어트, 메이크업, 리모델링",
        "difficulty": "easy",
    },
    "transformation": {
        "name_ko": "변신/변혁",
        "name_en": "Transformation",
        "description": "극적인 변화 과정을 시간순으로 보여줌",
        "why_effective": "변화에 대한 인간의 본능적 관심 활용",
        "example": "10초 만에 변신, 극적 이미지 변화",
        "difficulty": "medium",
    },
    "expectation_vs_reality": {
        "name_ko": "기대 vs 현실",
        "name_en": "Expectation vs Reality",
        "description": "기대했던 것과 실제 결과의 대비",
        "why_effective": "공감과 유머를 동시에 유발하여 공유 욕구 자극",
        "example": "온라인 vs 실물, 광고 vs 실제",
        "difficulty": "easy",
    },
    # 정보/가이드형
    "tutorial_tease": {
        "name_ko": "튜토리얼 맛보기",
        "name_en": "Tutorial Tease",
        "description": "유용한 팁의 결과를 먼저 보여주고 방법 설명",
        "why_effective": "실용적 가치 + 호기심 = 완주율 상승",
        "example": "'이렇게 하면 2배 빨라집니다'",
        "difficulty": "easy",
    },
    "list_format": {
        "name_ko": "리스트형",
        "name_en": "List Format",
        "description": "3가지~5가지 항목으로 구조화된 정보 전달",
        "why_effective": "명확한 정보 구조로 기대치 설정, 완료 욕구 자극",
        "example": "'5가지 꿀팁', '3단계 방법'",
        "difficulty": "easy",
    },
    "myth_bust": {
        "name_ko": "미신 파괴",
        "name_en": "Myth Bust",
        "description": "일반적으로 믿는 것이 틀렸음을 증명",
        "why_effective": "인지 부조화 해결 욕구로 끝까지 시청",
        "example": "'다들 이렇게 알고 있는데 사실...'",
        "difficulty": "medium",
    },
    # 참여/도전형
    "challenge": {
        "name_ko": "챌린지",
        "name_en": "Challenge",
        "description": "시청자도 따라할 수 있는 도전 과제 제시",
        "why_effective": "참여 욕구 자극으로 저장 및 공유 증가",
        "example": "댄스 챌린지, 요리 챌린지",
        "difficulty": "medium",
    },
    "countdown": {
        "name_ko": "카운트다운",
        "name_en": "Countdown",
        "description": "시간 제한이나 숫자 카운트다운으로 긴장감 조성",
        "why_effective": "타임 프레셔가 집중력을 높이고 이탈 방지",
        "example": "'10초 안에', '3,2,1...'",
        "difficulty": "easy",
    },
    # 스토리형
    "story_hook": {
        "name_ko": "스토리텔링",
        "name_en": "Story Hook",
        "description": "이야기의 시작으로 시청자를 서사에 끌어들임",
        "why_effective": "인간은 이야기를 완료하고 싶은 본능이 있음",
        "example": "'어제 이런 일이 있었는데...'",
        "difficulty": "medium",
    },
    # 제품/언박싱형
    "unboxing": {
        "name_ko": "언박싱",
        "name_en": "Unboxing",
        "description": "제품 개봉 과정을 보여주며 기대감 조성",
        "why_effective": "선물 개봉에 대한 대리 만족감 제공",
        "example": "택배 도착, 신제품 개봉",
        "difficulty": "easy",
    },
    # 사회적 증거형
    "social_proof": {
        "name_ko": "사회적 증거",
        "name_en": "Social Proof",
        "description": "다른 사람들의 반응/선택을 보여줘 신뢰도 상승",
        "why_effective": "대중의 선택 = 안전한 선택이라는 심리 활용",
        "example": "'100만명이 선택한', 리뷰 모음",
        "difficulty": "easy",
    },
    "pain_point": {
        "name_ko": "페인 포인트",
        "name_en": "Pain Point",
        "description": "시청자의 고민/문제를 먼저 언급하고 해결책 제시",
        "why_effective": "문제에 공감하면 해결책까지 보게 됨",
        "example": "'이거 짜증나지 않으세요?'",
        "difficulty": "easy",
    },
    # 리액션형
    "reaction_bait": {
        "name_ko": "리액션 유도",
        "name_en": "Reaction Bait",
        "description": "강한 감정적 반응을 유도하는 콘텐츠",
        "why_effective": "감정이 움직이면 댓글/공유로 이어짐",
        "example": "놀라운 장면, 귀여운 동물",
        "difficulty": "easy",
    },
    # 논쟁형
    "controversy": {
        "name_ko": "논쟁 유발",
        "name_en": "Controversy",
        "description": "의견이 갈리는 주제로 토론 유도",
        "why_effective": "자신의 의견을 말하고 싶은 욕구가 댓글 폭발로",
        "example": "'이거 맞다 vs 틀리다'",
        "difficulty": "hard",
    },
    # 기본값
    "other": {
        "name_ko": "기타",
        "name_en": "Other",
        "description": "분류되지 않은 훅 패턴",
        "why_effective": "분석 데이터 부족",
        "example": "-",
        "difficulty": "unknown",
    },
}


def get_hook_pattern_info(pattern: str) -> dict:
    """
    훅 패턴에 대한 상세 정보 반환

    Returns:
        dict with name_ko, name_en, description, why_effective, example, difficulty
    """
    if not pattern:
        return HOOK_PATTERN_REGISTRY.get("other", {})

    # 정확히 매칭되는 패턴 찾기
    pattern_lower = pattern.lower().replace(" ", "_").replace("-", "_")

    if pattern_lower in HOOK_PATTERN_REGISTRY:
        return HOOK_PATTERN_REGISTRY[pattern_lower]

    # 부분 매칭 시도
    for key, info in HOOK_PATTERN_REGISTRY.items():
        if key in pattern_lower or pattern_lower in key:
            return info

    # 매칭 실패 시 기본값 반환 (패턴명은 유지)
    return {
        "name_ko": pattern,
        "name_en": pattern,
        "description": pattern,
        "why_effective": "분석 데이터 부족",
        "example": "-",
        "difficulty": "unknown",
    }


# ==================
# HOOK EXTRACTION
# ==================


def extract_hook_pattern(analysis: dict) -> Optional[str]:
    """Extract hook pattern from gemini_analysis (VDG v3/v4/v5/2-Pass schema)"""
    pattern = None
    hook_genome = None

    # 1. VDG v5: semantic.hook_genome
    semantic = analysis.get("semantic", {})
    if isinstance(semantic, dict):
        hook_genome = semantic.get("hook_genome")
        if isinstance(hook_genome, dict):
            pattern = hook_genome.get("pattern")

    # 2. VDG 2-Pass: llm_output.hook_genome
    if not hook_genome:
        llm_output = analysis.get("llm_output", {})
        if isinstance(llm_output, dict):
            hook_genome = llm_output.get("hook_genome")
            if isinstance(hook_genome, dict):
                pattern = hook_genome.get("pattern")

    # 3. Direct hook_genome field (VDG v3/v4)
    if not hook_genome:
        hook_genome = analysis.get("hook_genome")
        if isinstance(hook_genome, dict):
            pattern = hook_genome.get("pattern")

    # If pattern is "other" or None, try better alternatives
    if pattern in ("other", None) and isinstance(hook_genome, dict):
        # Try hook_summary first (best description)
        hook_summary = hook_genome.get("hook_summary")
        if hook_summary and len(hook_summary) > 5:
            return hook_summary[:50]

        # Try first microbeat note
        microbeats = hook_genome.get("microbeats", [])
        if microbeats and isinstance(microbeats[0], dict):
            note = microbeats[0].get("note") or microbeats[0].get("description", "")
            if note and len(note) > 5:
                return note[:50]

        # Try delivery as pattern
        delivery = hook_genome.get("delivery")
        if delivery and delivery != "visual_gag":
            return delivery

    # Return pattern if it's a good value
    if pattern and pattern != "other":
        return pattern

    # 4. VDG v3: scenes[0].narrative_unit.role
    scenes = analysis.get("scenes") or analysis.get("llm_output", {}).get("scenes", [])
    if scenes and len(scenes) > 0:
        first_scene = scenes[0]
        narrative = first_scene.get("narrative_unit", {})
        if narrative.get("role"):
            return narrative["role"].lower().replace(" ", "_")
        # VDG v5: scene-level summary
        summary = first_scene.get("summary")
        if summary and len(summary) > 10:
            return summary[:50]

    # 5. Legacy pattern field
    return analysis.get("pattern") or pattern


def extract_hook_score(analysis: dict) -> Optional[float]:
    """Extract hook strength score (VDG v3/v4/v5/2-Pass)

    Returns a value between 0 and 1 (strength) that can be displayed as 0-1000 in frontend.
    """
    # 1. VDG v5: semantic.hook_genome.strength
    semantic = analysis.get("semantic", {})
    if isinstance(semantic, dict):
        hook_genome = semantic.get("hook_genome")
        if isinstance(hook_genome, dict):
            strength = hook_genome.get("strength")
            if strength is not None:
                return float(strength)

    # 2. VDG 2-Pass: llm_output.hook_genome.strength
    llm_output = analysis.get("llm_output", {})
    if isinstance(llm_output, dict):
        hook_genome = llm_output.get("hook_genome")
        if isinstance(hook_genome, dict):
            strength = hook_genome.get("strength")
            if strength is not None:
                return float(strength)

    # 3. Direct hook_genome.strength (VDG v3/v4)
    hook_genome = analysis.get("hook_genome", {})
    if isinstance(hook_genome, dict):
        strength = hook_genome.get("strength")
        if strength is not None:
            return float(strength)

    # 4. Legacy metrics.hook_strength or predicted_retention_score
    if "metrics" in analysis:
        metrics = analysis["metrics"]
        score = metrics.get("hook_strength")
        if score is None:
            score = metrics.get("predicted_retention_score")
        if score is None:
            virality = metrics.get("virality", {})
            score = virality.get("hook_strength")
        if score is not None:
            return float(score)

    # 5. VDG v3: Use shots[0].confidence as proxy
    scenes = analysis.get("scenes", [])
    if not scenes:
        scenes = llm_output.get("scenes", []) if isinstance(llm_output, dict) else []

    if scenes and len(scenes) > 0:
        first_scene = scenes[0]
        shots = first_scene.get("shots", [])
        if shots:
            conf = shots[0].get("confidence")
            if conf == "high":
                return 0.9
            elif conf == "medium":
                return 0.7
            elif conf == "low":
                return 0.5

        # 6. Fallback: If first scene is labeled "hook", infer a moderate score
        label = first_scene.get("label", "")
        if label.lower() == "hook":
            return 0.65  # Moderate confidence for labeled hook scenes

    # 7. Final fallback: If hook_pattern was detected, assume moderate score
    pattern = extract_hook_pattern(analysis)
    if pattern and pattern not in ("other", "unknown", None):
        return 0.6  # Pattern detected = at least moderate hook strength

    return None


def extract_hook_duration(analysis: dict) -> Optional[float]:
    """Extract hook duration (VDG v3/v4/v5)"""
    # 1. VDG v5: semantic.hook_genome.end_sec
    semantic = analysis.get("semantic", {})
    if isinstance(semantic, dict):
        hook_genome = semantic.get("hook_genome")
        if isinstance(hook_genome, dict):
            end_sec = hook_genome.get("end_sec")
            if end_sec is not None:
                return float(end_sec)
            # Fallback to hook_end_ms
            end_ms = hook_genome.get("hook_end_ms")
            if end_ms is not None:
                return float(end_ms) / 1000.0

    # 2. Direct hook_genome (VDG v3/v4)
    hook_genome = analysis.get("hook_genome", {})
    if isinstance(hook_genome, dict):
        end_sec = hook_genome.get("end_sec")
        if end_sec is not None:
            return float(end_sec)
        duration = hook_genome.get("duration_sec")
        if duration is not None:
            return float(duration)
        # Fallback to hook_end_ms
        end_ms = hook_genome.get("hook_end_ms")
        if end_ms is not None:
            return float(end_ms) / 1000.0

    # 3. VDG v3: scenes[0].duration_sec or time_end
    if "scenes" in analysis and len(analysis["scenes"]) > 0:
        first_scene = analysis["scenes"][0]
        if "duration_sec" in first_scene:
            try:
                return float(first_scene["duration_sec"])
            except (TypeError, ValueError):
                pass
        if "time_end" in first_scene:
            try:
                return float(first_scene["time_end"])
            except (TypeError, ValueError):
                pass
        # Legacy: end_time
        if "end_time" in first_scene:
            try:
                return float(first_scene["end_time"])
            except (TypeError, ValueError):
                pass

    return None


# ==================
# SHOTLIST / TIMING / DO_NOT
# ==================


def extract_shotlist(analysis: dict) -> Optional[List[str]]:
    """Extract shotlist from VDG - supports v3, v4, v5, 2-Pass schemas"""
    shotlist = []

    # 1. VDG v5: semantic.capsule_brief.shotlist
    capsule = analysis.get("semantic", {}).get("capsule_brief", {})
    if capsule.get("shotlist"):
        return capsule["shotlist"]

    # 2. VDG 2-Pass: llm_output.capsule_brief.shotlist
    llm_output = analysis.get("llm_output", {})
    if isinstance(llm_output, dict):
        capsule_2p = llm_output.get("capsule_brief", {})
        if isinstance(capsule_2p, dict) and capsule_2p.get("shotlist"):
            return capsule_2p["shotlist"]

    # 3. VDG v5/2-Pass: Use viral_kicks as shotlist
    provenance = analysis.get("provenance", {})
    kicks = provenance.get("viral_kicks", []) or (
        llm_output.get("viral_kicks", []) if isinstance(llm_output, dict) else []
    )
    if kicks:
        for kick in kicks:
            title = kick.get("title", "")
            instr = kick.get("creator_instruction", "")
            window = kick.get("window", {})
            t_start = (window.get("start_ms", 0) if window else kick.get("t_start_ms", 0)) / 1000
            t_end = (window.get("end_ms", 0) if window else kick.get("t_end_ms", 0)) / 1000
            shotlist.append(f"[{t_start:.0f}-{t_end:.0f}s] {title}: {instr[:50]}...")
        if shotlist:
            return shotlist

    # 4. VDG v3/2-Pass: scenes[].narrative_unit.summary or scenes[].summary
    scenes = analysis.get("scenes") or (llm_output.get("scenes", []) if isinstance(llm_output, dict) else [])
    if scenes:
        for i, scene in enumerate(scenes):
            # VDG 2-Pass: direct summary field
            summary = scene.get("summary")
            if not summary:
                # VDG v3: narrative_unit.summary
                narrative = scene.get("narrative_unit", {})
                summary = narrative.get("summary")
            if summary:
                duration = scene.get("duration_sec")
                if duration:
                    shotlist.append(f"{summary} ({duration}s)")
                else:
                    shotlist.append(summary)
        if shotlist:
            return shotlist

    # 5. Legacy shotlist field
    if "shotlist" in analysis:
        return analysis["shotlist"]

    return None


def extract_timing(analysis: dict) -> Optional[List[str]]:
    """Extract timing info from VDG - supports v3, v4, v5 schemas"""
    timings = []

    def _safe_float(value, fallback: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    # P7: Reason 한글 매핑
    reason_ko_map = {
        "hook_punch": "훅 포인트",
        "hook_start": "훅 시작",
        "hook_build": "훅 빌드업",
        "hook_end": "훅 종료",
        "key_dialogue": "핵심 대사",
        "scene_boundary": "씬 전환",
        "sentiment_shift": "감정 전환",
        "product_mention": "제품 언급",
        "text_appear": "텍스트 등장",
        "comment_mise_en_scene": "미장센 포인트",
        "comment_evidence": "댓글 증거",
        "analysis": "분석 포인트",
    }

    # 1. VDG v5: analysis_plan.points
    analysis_plan = analysis.get("analysis_plan", {})
    points = analysis_plan.get("points", [])
    if points:
        for point in points[:6]:
            t_center = _safe_float(point.get("t_center"))
            t_window = point.get("t_window", [])
            reason_raw = point.get("reason", "analysis")
            reason_ko = reason_ko_map.get(reason_raw, reason_raw)
            if t_window and len(t_window) == 2:
                start = _safe_float(t_window[0])
                end = _safe_float(t_window[1])
                timings.append(f"{start:.1f}-{end:.1f}s: {reason_ko}")
            elif t_center:
                timings.append(f"{t_center:.1f}s: {reason_ko}")
        if timings:
            return timings

    # 2. VDG v5/2-Pass: Use viral_kicks for timing
    provenance = analysis.get("provenance", {})
    llm_output = analysis.get("llm_output", {})
    kicks = provenance.get("viral_kicks", []) or (
        llm_output.get("viral_kicks", []) if isinstance(llm_output, dict) else []
    )
    if kicks:
        for kick in kicks:
            window = kick.get("window", {})
            t_start = (
                window.get("start_ms", 0) / 1000
                if window.get("start_ms") is not None
                else kick.get("t_start_ms", 0) / 1000
            )
            t_end = (
                window.get("end_ms", 0) / 1000 if window.get("end_ms") is not None else kick.get("t_end_ms", 0) / 1000
            )
            # Use creator_instruction for meaningful description, fallback to title
            instruction = kick.get("creator_instruction", "")
            title = kick.get("title", "kick")
            if instruction and len(instruction) > 5:
                # Extract first meaningful part (up to 30 chars or first sentence)
                desc = instruction.split(".")[0][:40]
                if len(desc) > 35:
                    desc = desc[:35] + "..."
            else:
                desc = title
            timings.append(f"{t_start:.0f}-{t_end:.0f}s: {desc}")
        if timings:
            return timings

    # 3. VDG v3: scenes
    if "scenes" in analysis and analysis["scenes"]:
        for scene in analysis["scenes"]:
            if "duration_sec" in scene:
                timings.append(f"{scene['duration_sec']}s")
            elif "time_start" in scene and "time_end" in scene:
                start = _safe_float(scene.get("time_start"))
                end = _safe_float(scene.get("time_end"), start)
                timings.append(f"{end - start:.1f}s")
        if timings:
            return timings

    return None


def extract_do_not(analysis: dict) -> Optional[List[str]]:
    """Extract things to avoid - supports v3, v4, v5, 2-Pass schemas"""
    do_not = []

    # 1. VDG v5: semantic.capsule_brief.do_not
    capsule = analysis.get("semantic", {}).get("capsule_brief", {})
    if capsule.get("do_not"):
        return capsule["do_not"]

    # 1.5 VDG 2-Pass: llm_output.capsule_brief.do_not
    llm_output = analysis.get("llm_output", {})
    if isinstance(llm_output, dict):
        capsule_2p = llm_output.get("capsule_brief", {})
        if isinstance(capsule_2p, dict) and capsule_2p.get("do_not"):
            return capsule_2p["do_not"]

    # 2. Legacy fields
    if "warnings" in analysis:
        return analysis["warnings"]
    if "do_not" in analysis:
        return analysis["do_not"]

    # 3. VDG v5: contract_candidates.forbidden_mutations_candidates
    contract = analysis.get("contract_candidates", {})
    forbidden = contract.get("forbidden_mutations_candidates", [])
    if forbidden:
        for item in forbidden[:5]:
            if isinstance(item, str):
                do_not.append(f"❌ {item}")
            elif isinstance(item, dict):
                do_not.append(f"❌ {item.get('description', str(item))}")
        if do_not:
            return do_not

    # 4. Generate from causal_reasoning risks
    semantic = analysis.get("semantic", {})
    prov = semantic.get("provenance", {}) or analysis.get("provenance", {})
    causal = prov.get("causal_reasoning", {})
    risks = causal.get("risks_or_unknowns", [])
    if risks:
        for risk in risks[:3]:
            do_not.append(f"⚠️ {risk}")
        return do_not

    # 5. VDG v4: remix_suggestions[0].do_not
    remix = analysis.get("remix_suggestions", [])
    if remix:
        first_remix = remix[0]
        if first_remix.get("do_not"):
            return first_remix["do_not"]

    return None


# ==================
# INVARIANT / VARIABLE (Temporal Variation Theory)
# ==================


def extract_invariant(analysis: dict) -> Optional[List[str]]:
    """
    Extract must-keep elements (불변 요소) from VDG analysis - Smart Inference
    Priority: replication_recipe > hook_genome > viral_kicks > legacy extraction
    """
    invariant = []

    delivery_map = {
        "visual_gag": "시각적 개그",
        "storytelling": "스토리텔링",
        "reaction": "리액션",
        "tutorial": "튜토리얼",
        "reveal": "반전/공개",
        "montage": "몽타주",
        "talking_head": "토킹 헤드",
    }

    prov = analysis.get("provenance", {})
    llm_output = analysis.get("llm_output", {})

    # 1. PRIMARY: Use replication_recipe from causal_reasoning (most actionable)
    # Support both VDG v5 (provenance.causal_reasoning) and 2-Pass (llm_output.causal_reasoning)
    causal = prov.get("causal_reasoning", {}) or (
        llm_output.get("causal_reasoning", {}) if isinstance(llm_output, dict) else {}
    )
    recipe = causal.get("replication_recipe", [])
    if recipe:
        for step in recipe[:3]:
            if step and isinstance(step, str):
                invariant.append(f"📋 {step}")

    # 2. SECONDARY: Hook genome details (if recipe not enough)
    if len(invariant) < 3:
        # Support both VDG v5 (semantic.hook_genome) and 2-Pass (llm_output.hook_genome)
        semantic = analysis.get("semantic", {})
        hg = None
        if isinstance(semantic, dict):
            hg = semantic.get("hook_genome", {})
        if not hg and isinstance(llm_output, dict):
            hg = llm_output.get("hook_genome", {})
        if isinstance(hg, dict):
            # Hook pattern - improve "other" handling
            pattern = hg.get("pattern")
            if pattern and pattern != "other":
                invariant.append(f"🎣 훅 패턴: {pattern}")
            elif pattern == "other":
                # Infer from microbeats or hook_summary
                microbeats = hg.get("microbeats", [])
                if microbeats and microbeats[0].get("note"):
                    note = microbeats[0]["note"][:40]
                    invariant.append(f"🎣 훅 시작: {note}")
                elif hg.get("hook_summary"):
                    invariant.append(f"🎣 {hg['hook_summary'][:40]}")

            # Delivery method
            delivery = hg.get("delivery")
            if delivery:
                delivery_kr = delivery_map.get(delivery, delivery)
                invariant.append(f"🎯 전달 방식: {delivery_kr}")

            # Timing
            end_sec = hg.get("end_sec")
            if end_sec:
                invariant.append(f"⏱️ 훅 완성: {end_sec}초 안에")

    # 3. Fallback to legacy extraction if nothing found
    if not invariant:
        hook_pattern = extract_hook_pattern(analysis)
        if hook_pattern:
            invariant.append(f"🎣 훅: {hook_pattern}")
        hook_dur = extract_hook_duration(analysis)
        if hook_dur:
            invariant.append(f"⏱️ 처음 {hook_dur}초 안에 훅 완성")

    return invariant if invariant else None


def extract_variable(analysis: dict) -> Optional[List[str]]:
    """
    Extract creative variation elements (가변 요소)
    Priority: viral_kicks.creator_instruction > format-based suggestions
    """
    variable = []

    prov = analysis.get("provenance", {})
    llm_output = analysis.get("llm_output", {})

    # 1. PRIMARY: Use viral_kicks.creator_instruction
    # Support both VDG v5 (provenance.viral_kicks) and 2-Pass (llm_output.viral_kicks)
    kicks = prov.get("viral_kicks", []) or (llm_output.get("viral_kicks", []) if isinstance(llm_output, dict) else [])
    if kicks:
        for kick in kicks:
            instruction = kick.get("creator_instruction")
            if instruction and isinstance(instruction, str):
                text = instruction[:80] + "..." if len(instruction) > 80 else instruction
                variable.append(f"🎬 {text}")

    # 2. SECONDARY: Additional recipe steps
    if len(variable) < 3:
        # Support both VDG v5 (provenance.causal_reasoning) and 2-Pass (llm_output.causal_reasoning)
        causal = prov.get("causal_reasoning", {}) or (
            llm_output.get("causal_reasoning", {}) if isinstance(llm_output, dict) else {}
        )
        recipe = causal.get("replication_recipe", [])
        for step in recipe[3:5]:
            if step and isinstance(step, str):
                text = step[:60] + "..." if len(step) > 60 else step
                variable.append(f"✨ {text}")

    # 3. FALLBACK: Format-based suggestions
    if not variable:
        semantic = analysis.get("semantic", {})
        hook_genome = semantic.get("hook_genome", {}) if isinstance(semantic, dict) else {}
        delivery = hook_genome.get("delivery", "")

        variable = [
            "🎨 소재: 동일 포맷의 다른 주제 적용 가능",
            "👤 인물: 다른 크리에이터 스타일로 재해석",
            "📍 배경: 장소/환경 자유롭게 변경",
        ]

        if delivery == "visual_gag":
            variable.append("😂 개그 소재: 다른 밈/유머로 대체 가능")
        elif delivery == "storytelling":
            variable.append("📖 스토리: 다른 내러티브로 재구성 가능")

    return variable if variable else None


# ==================
# VISUAL / AUDIO PATTERNS
# ==================


def extract_visual_patterns(analysis: dict) -> Optional[List[str]]:
    """Extract visual patterns from VDG - supports v3, v4, v5, 2-Pass schemas"""
    patterns = []

    # Support both VDG v5 (semantic) and 2-Pass (llm_output)
    semantic = analysis.get("semantic", {})
    llm_output = analysis.get("llm_output", {})
    mise_signals = (semantic.get("mise_en_scene_signals", []) if isinstance(semantic, dict) else []) or (
        llm_output.get("mise_en_scene_signals", []) if isinstance(llm_output, dict) else []
    )
    if mise_signals:
        for signal in mise_signals[:6]:
            if isinstance(signal, dict):
                # VDG v5: element/value, VDG 2-Pass: type/description
                element = signal.get("element") or signal.get("type", "")
                value = signal.get("value") or signal.get("description", "")
                if element and value:
                    # Truncate long descriptions
                    if len(value) > 50:
                        value = value[:47] + "..."
                    patterns.append(f"{translate_term(element)}: {value}")
        if patterns:
            return patterns

    # 2. VDG v4: visual_analysis.results
    visual = analysis.get("visual_analysis", {})
    if visual.get("analysis_results"):
        for result in visual["analysis_results"][:3]:
            metrics = result.get("metrics", {})
            for metric_id in metrics.keys():
                if "color" in metric_id:
                    patterns.append("시각적 색상")
                if "motion" in metric_id:
                    patterns.append("모션/움직임")

    # 3. Legacy: scenes[].shots[].camera
    if "scenes" in analysis and analysis["scenes"]:
        for scene in analysis["scenes"][:3]:
            shots = scene.get("shots", [])
            for shot in shots[:2]:
                camera = shot.get("camera", {})
                if camera.get("shot"):
                    patterns.append(translate_term(camera["shot"]))
                if camera.get("move"):
                    patterns.append(translate_term(camera["move"]))

    return list(dict.fromkeys(patterns))[:6] if patterns else None


def extract_audio_pattern(analysis: dict) -> Optional[str]:
    """Extract audio pattern from VDG with Korean translation"""
    # Direct audio field
    audio = analysis.get("audio")
    if isinstance(audio, dict):
        pattern = audio.get("type") or audio.get("style")
        return translate_term(pattern) if pattern else None
    if isinstance(audio, str):
        return translate_term(audio) if audio else None

    # VDG v3: scenes[].setting.audio_style
    if "scenes" in analysis:
        for scene in analysis["scenes"]:
            setting = scene.get("setting", {})
            audio_style = setting.get("audio_style", {})
            if audio_style.get("music"):
                return translate_term(audio_style["music"])
            if audio_style.get("tone"):
                return translate_term(audio_style["tone"])

    return None


# ==================
# VDG TRANSLATION (for Storyboard UI)
# ==================


def translate_vdg_to_korean(analysis: dict) -> dict:
    """
    Translate VDG analysis to Korean for Storyboard UI.
    Returns structured scene data with Korean labels.
    """
    result = {
        "title": analysis.get("title", ""),
        "title_ko": analysis.get("title", ""),
        "total_duration": 0,
        "scene_count": 0,
        "scenes": [],
    }

    # VDG 2-Pass (llm_output) takes priority, then semantic, then top-level
    scenes = (
        analysis.get("llm_output", {}).get("scenes")
        or analysis.get("semantic", {}).get("scenes")
        or analysis.get("scenes")
        or []
    )
    if not isinstance(scenes, list):
        scenes = []
    scenes = [scene for scene in scenes if isinstance(scene, dict)]
    result["scene_count"] = len(scenes)

    # Fill title and duration from analysis
    result["title"] = analysis.get("title") or analysis.get("semantic", {}).get("summary", "")[:50] or "영상 분석"
    result["title_ko"] = result["title"]
    pre_set_duration = analysis.get("duration_sec", 0)
    result["total_duration"] = pre_set_duration

    for i, scene in enumerate(scenes):
        # --- VDG 2-Pass Schema Support ---
        if "visual_detail" in scene:
            visual = scene.get("visual_detail", {})
            bg = visual.get("background", {})

            # 2-Pass uses "summary" at root level, "label" as role
            scene["narrative_unit"] = {"summary": scene.get("summary", ""), "role": scene.get("label", "Scene")}

            # Map visual_detail to setting for UI compatibility
            scene["setting"] = {
                "visual_style": {
                    "lighting": bg.get("lighting_quality", ""),
                    "color": ", ".join(bg.get("color_palette", [])),
                }
            }

            # Create shots from subject info (2-Pass has no camera data)
            scene["shots"] = [
                {
                    "camera": {"shot": "", "angle": "", "move": ""},
                    "subject": visual.get("subject_description", ""),
                    "action": visual.get("subject_action", ""),
                }
            ]
        # --- End VDG 2-Pass Support ---

        narrative = scene.get("narrative_unit") or {}
        setting = scene.get("setting") or {}
        visual_style = setting.get("visual_style") or {}
        audio_style = setting.get("audio_style") or {}
        shots = scene.get("shots") or []

        # Calculate timing
        window = scene.get("window", {})
        time_start = (
            window.get("start_ms", 0) / 1000.0 if window.get("start_ms") is not None else scene.get("time_start")
        )
        time_end = window.get("end_ms", 0) / 1000.0 if window.get("end_ms") is not None else scene.get("time_end")
        try:
            time_start = float(time_start) if time_start is not None else 0.0
        except (TypeError, ValueError):
            time_start = 0.0
        try:
            time_end = float(time_end) if time_end is not None else 0.0
        except (TypeError, ValueError):
            time_end = 0.0

        raw_duration = scene.get("duration_sec")
        try:
            duration = float(raw_duration) if raw_duration is not None else (time_end - time_start)
        except (TypeError, ValueError):
            duration = time_end - time_start

        if not pre_set_duration:
            result["total_duration"] += duration

        # Extract camera info from first shot
        camera_info = {}
        if shots:
            cam = shots[0].get("camera", {})
            camera_info = {
                "shot": translate_term(cam.get("shot", "")),
                "shot_en": cam.get("shot", ""),
                "move": translate_term(cam.get("move", "")),
                "move_en": cam.get("move", ""),
                "angle": translate_term(cam.get("angle", "")),
                "angle_en": cam.get("angle", ""),
            }

        # Extract audio events
        audio_events = audio_style.get("audio_events") or []
        audio_descriptions = [
            {
                "label": translate_term(e.get("description", "")),
                "label_en": e.get("description", ""),
                "intensity": e.get("intensity", "medium"),
            }
            for e in audio_events
            if isinstance(e, dict) and e.get("description")
        ]

        scene_data = {
            "scene_id": scene.get("scene_id", f"S{i+1:02d}"),
            "scene_number": i + 1,
            "time_start": time_start,
            "time_end": time_end,
            "duration_sec": duration,
            "time_label": f"{int(time_start//60)}:{int(time_start%60):02d} - {int(time_end//60)}:{int(time_end%60):02d}",
            # Narrative - VDG v5: scene-level fields; legacy: narrative_unit
            "role": translate_term(scene.get("narrative_role") or narrative.get("role", "")),
            "role_en": scene.get("narrative_role") or narrative.get("role", ""),
            "summary": scene.get("summary") or narrative.get("summary", ""),
            "summary_ko": scene.get("summary") or narrative.get("summary", ""),
            "dialogue": narrative.get("dialogue", ""),
            "comedic_device": narrative.get("comedic_device", []),
            # Camera
            "camera": camera_info,
            # Setting
            "location": setting.get("location", ""),
            "lighting": translate_term(visual_style.get("lighting", "")),
            "lighting_en": visual_style.get("lighting", ""),
            "edit_pace": translate_term(visual_style.get("edit_pace", "")),
            "edit_pace_en": visual_style.get("edit_pace", ""),
            # Audio
            "audio_events": audio_descriptions,
            "music": audio_style.get("music", ""),
            "ambient": audio_style.get("ambient_sound", ""),
        }
        result["scenes"].append(scene_data)

    return result


# ==================
# PLATFORM TIPS
# ==================


def get_platform_specific_tips(platform: str) -> List[str]:
    """Get platform-specific shooting tips"""
    tips = {
        "youtube": [
            "🎬 쇼츠: 첫 1초가 생명, Thumbnail = 첫 프레임",
            "📱 세로 9:16 필수, 60초 이내",
        ],
        "tiktok": [
            "🎵 틱톡: 트렌딩 사운드 활용이 핵심",
            "🔄 듀엣/스티치 가능한 포맷 고려",
            "📱 세로 9:16, 15/30/60초 권장",
        ],
        "instagram": [
            "📸 릴스: 첫 3초 안에 주제 명확히",
            "🏷️ 해시태그 활용 중요",
        ],
    }
    return tips.get(platform.lower(), [])


# ==================
# VDG VISUAL DATA EXTRACTORS (for Ghost Overlay, Timeline)
# Moved from outliers.py for better maintainability
# ==================


def extract_hook_genome(analysis: dict) -> Optional[dict]:
    """Extract complete hook_genome object for frontend timeline indicator (VDG v4/v5)"""
    try:
        # VDG v5: semantic.hook_genome
        semantic = analysis.get("semantic", {})
        if isinstance(semantic, dict):
            hg = semantic.get("hook_genome")
            if isinstance(hg, dict):
                return {
                    "start_sec": hg.get("start_sec", 0),
                    "end_sec": hg.get("end_sec", 3),
                    "pattern": hg.get("pattern"),
                    "strength": hg.get("strength"),
                    "microbeats": hg.get("microbeats", []),
                }

        # VDG v4: direct hook_genome
        hg = analysis.get("hook_genome")
        if isinstance(hg, dict):
            return {
                "start_sec": hg.get("start_sec", 0),
                "end_sec": hg.get("end_sec") or hg.get("duration_sec", 3),
                "pattern": hg.get("pattern"),
                "strength": hg.get("strength"),
                "microbeats": hg.get("microbeats", []),
            }
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug(f"Failed to extract hook genome: {e}")
    return None


def extract_causal_reasoning(analysis: dict) -> Optional[dict]:
    """Extract causal reasoning for 'Why Viral' UI section (P2 Feature).

    Hardened for edge cases:
    - Invalid/missing analysis dict
    - Non-string items in causal_chain/recipe lists
    - Empty why_viral with fallback to first causal_chain item
    - XSS-safe HTML stripping

    Returns:
        {
            "why_viral": "짧은 한줄 요약",
            "causal_chain": ["원인1", "원인2", "결과"],
            "replication_recipe": ["따라하기 스텝1", "스텝2"],
            "risks": ["주의사항1"]
        }
    """
    try:
        # Input validation
        if not analysis or not isinstance(analysis, dict):
            return None

        causal = None

        # 1. VDG 2-Pass: llm_output.causal_reasoning
        llm_output = analysis.get("llm_output", {})
        if isinstance(llm_output, dict):
            causal = llm_output.get("causal_reasoning")

        # 2. VDG v5: provenance.causal_reasoning
        if not causal:
            provenance = analysis.get("provenance", {})
            if isinstance(provenance, dict):
                causal = provenance.get("causal_reasoning")

        # 3. VDG v5: semantic.provenance.causal_reasoning
        if not causal:
            semantic = analysis.get("semantic", {})
            if isinstance(semantic, dict):
                prov = semantic.get("provenance", {})
                if isinstance(prov, dict):
                    causal = prov.get("causal_reasoning")

        if not causal or not isinstance(causal, dict):
            return None

        # Helper: sanitize string (strip HTML, limit length)
        def sanitize_str(val, max_len: int = 300) -> str:
            if not val:
                return ""
            s = str(val).strip()
            # Basic HTML tag stripping for security
            s = re.sub(r"<[^>]+>", "", s)
            return s[:max_len]

        # Helper: extract list of strings with validation
        def extract_str_list(key: str, max_items: int = 8) -> List[str]:
            items = causal.get(key, [])
            if not isinstance(items, list):
                return []
            result = []
            for item in items[:max_items]:
                if isinstance(item, str) and item.strip():
                    result.append(sanitize_str(item, 200))
                elif isinstance(item, dict):
                    # Some VDG versions return dicts with 'text' or 'step' keys
                    text = item.get("text") or item.get("step") or item.get("description", "")
                    if text:
                        result.append(sanitize_str(str(text), 200))
            return result

        # Extract why_viral with fallback
        why_viral = sanitize_str(causal.get("why_viral_one_liner") or causal.get("why_viral", ""))
        causal_chain = extract_str_list("causal_chain")

        # Fallback: if why_viral empty, use first causal_chain item
        if not why_viral and causal_chain:
            why_viral = causal_chain[0]

        # If still no meaningful content, return None
        if not why_viral and not causal_chain:
            return None

        return {
            "why_viral": why_viral,
            "causal_chain": causal_chain,
            "replication_recipe": extract_str_list("replication_recipe"),
            "risks": extract_str_list("risks_or_unknowns", 4),
        }
    except Exception as e:
        logger.warning(f"Failed to extract causal reasoning: {e}")
    return None


def extract_entity_tracks(analysis: dict) -> Optional[List[dict]]:
    """Extract entity tracks with time-series bbox data from VDG 2-Pass Visual analysis.

    P2 Enhancement: Joins entity_tracks with entity_catalog to enrich class_name/entity_type.

    Join Priority:
    1. Track's own class_name/entity_type (if not empty/unknown)
    2. entity_catalog lookup by entity_id
    3. Fallback defaults: class_name="unknown", entity_type="other"

    Returns list of tracks with samples for dynamic overlay rendering.
    Includes hardening: try/except, type validation, bbox normalization.
    """
    try:
        if not analysis or not isinstance(analysis, dict):
            return None

        # VDG v4/v5: visual.entity_tracks OR visual_result.entity_tracks (2-Pass raw)
        visual = analysis.get("visual", {})
        if not isinstance(visual, dict):
            visual = {}

        visual_result = analysis.get("visual_result", {})
        if not isinstance(visual_result, dict):
            visual_result = {}

        # P2: Build entity_catalog index for O(1) lookup
        # Priority: visual.entity_catalog > visual_result.entity_catalog
        entity_catalog = visual.get("entity_catalog", []) or visual_result.get("entity_catalog", [])
        catalog_index: dict[str, dict] = {}
        if entity_catalog and isinstance(entity_catalog, list):
            for cat in entity_catalog:
                if not isinstance(cat, dict):
                    continue
                entity_id = cat.get("entity_id")
                if entity_id:
                    catalog_index[str(entity_id)] = {
                        "class_name": str(cat.get("class_name", "unknown")),
                        "entity_type": str(cat.get("entity_type", "other")),
                        "bbox_norm": cat.get("bbox_norm"),
                        "confidence": cat.get("confidence", 0.5),
                        "first_seen_ms": cat.get("first_seen_ms", 0),
                    }

        # Debug: log catalog size
        if catalog_index:
            logger.debug(f"[P2] entity_catalog index built: {len(catalog_index)} entries")

        entity_tracks = visual.get("entity_tracks", [])

        # Fallback: visual_result (VDG 2-Pass stores raw data here)
        if not entity_tracks:
            entity_tracks = visual_result.get("entity_tracks", [])

        if entity_tracks and isinstance(entity_tracks, list):
            # Validate each track has required structure
            validated = []
            enriched_count = 0

            for t in entity_tracks:
                if not isinstance(t, dict):
                    continue
                samples = t.get("samples", [])
                if not isinstance(samples, list):
                    continue
                # Validate each sample has bbox_norm as list of 4 numbers
                valid_samples = []
                for s in samples:
                    if not isinstance(s, dict):
                        continue
                    bbox = s.get("bbox_norm")
                    if isinstance(bbox, list) and len(bbox) == 4:
                        try:
                            # Clamp to [0,1] range
                            bbox = [max(0.0, min(1.0, float(v))) for v in bbox]
                            valid_samples.append(
                                {
                                    "t_ms": int(s.get("t_ms", 0) or 0),
                                    "bbox_norm": bbox,
                                    "confidence": float(s.get("confidence", 0.5) or 0.5),
                                }
                            )
                        except (TypeError, ValueError):
                            continue

                if valid_samples:
                    # P2: Enrich class_name/entity_type from catalog
                    track_class_name = t.get("class_name")
                    track_entity_type = t.get("entity_type")
                    entity_id = str(t.get("entity_id", ""))
                    track_id = str(t.get("track_id", ""))

                    # Check if enrichment needed (empty or "unknown")
                    needs_class_name = not track_class_name or track_class_name in ("", "unknown", None)
                    needs_entity_type = not track_entity_type or track_entity_type in ("", "unknown", None)

                    # Try catalog lookup if needed
                    if (needs_class_name or needs_entity_type) and catalog_index:
                        # Priority 1: entity_id
                        cat_entry = catalog_index.get(entity_id)
                        # Priority 2: track_id (some schemas use track_id as entity_id)
                        if not cat_entry and track_id:
                            cat_entry = catalog_index.get(track_id)

                        if cat_entry:
                            if needs_class_name:
                                track_class_name = cat_entry["class_name"]
                            if needs_entity_type:
                                track_entity_type = cat_entry["entity_type"]
                            enriched_count += 1

                    # Final defaults
                    final_class_name = str(track_class_name or "unknown")
                    final_entity_type = str(track_entity_type or "other")

                    validated.append(
                        {
                            "track_id": track_id or entity_id or f"track_{len(validated)}",
                            "entity_id": entity_id,
                            "class_name": final_class_name,
                            "entity_type": final_entity_type,
                            "samples": valid_samples,
                        }
                    )

            # Debug: log enrichment stats
            if validated:
                logger.debug(f"[P2] entity_tracks enriched: {enriched_count}/{len(validated)} from catalog")
                return validated

        # Fallback: Try entity_catalog for static data (when no entity_tracks exist)
        if catalog_index:
            fallback = []
            for entity_id, cat in catalog_index.items():
                bbox = cat.get("bbox_norm", [0.3, 0.3, 0.4, 0.4])
                if not isinstance(bbox, list) or len(bbox) != 4:
                    bbox = [0.3, 0.3, 0.4, 0.4]
                try:
                    bbox = [max(0.0, min(1.0, float(v))) for v in bbox]
                except (TypeError, ValueError):
                    bbox = [0.3, 0.3, 0.4, 0.4]
                fallback.append(
                    {
                        "track_id": entity_id,
                        "entity_id": entity_id,
                        "class_name": cat.get("class_name", "unknown"),
                        "entity_type": cat.get("entity_type", "other"),
                        "samples": [
                            {
                                "t_ms": int(cat.get("first_seen_ms", 0) or 0),
                                "bbox_norm": bbox,
                                "confidence": float(cat.get("confidence", 0.5) or 0.5),
                            }
                        ],
                    }
                )
            if fallback:
                logger.debug(f"[P2] Fallback: created {len(fallback)} tracks from entity_catalog only")
                return fallback

        return None
    except Exception as ex:
        logger.warning(f"extract_entity_tracks error: {ex}")
        return None


def extract_text_geometries(analysis: dict) -> Optional[List[dict]]:
    """Extract text geometries with bbox and timing from VDG 2-Pass Visual analysis.

    Includes hardening: try/except, type validation, bbox/timing validation.
    """
    try:
        if not analysis or not isinstance(analysis, dict):
            return None

        # VDG v4/v5: visual.text_geometries OR visual_result.text_geometries (2-Pass raw)
        visual = analysis.get("visual", {})
        if not isinstance(visual, dict):
            visual = {}

        text_geometries = visual.get("text_geometries", [])

        # Fallback: visual_result (VDG 2-Pass stores raw data here)
        if not text_geometries:
            visual_result = analysis.get("visual_result", {})
            if isinstance(visual_result, dict):
                text_geometries = visual_result.get("text_geometries", [])

        if not text_geometries or not isinstance(text_geometries, list):
            return None

        validated = []
        for tg in text_geometries:
            if not isinstance(tg, dict):
                continue

            text = tg.get("text", "")
            if not text or not isinstance(text, str):
                continue

            # Validate bbox_norm - list of 4 numbers in [0,1]
            bbox = tg.get("bbox_norm")
            valid_bbox = None
            if isinstance(bbox, list) and len(bbox) == 4:
                try:
                    valid_bbox = [max(0.0, min(1.0, float(v))) for v in bbox]
                except (TypeError, ValueError):
                    valid_bbox = None

            # Validate t_window - [start_ms, end_ms] (preserve float precision)
            t_window = tg.get("t_window")
            valid_t_window = None
            if isinstance(t_window, (list, tuple)) and len(t_window) == 2:
                try:
                    valid_t_window = [max(0.0, float(t_window[0] or 0)), max(0.0, float(t_window[1] or 0))]
                except (TypeError, ValueError):
                    valid_t_window = None

            validated.append(
                {
                    "text": str(text)[:200],  # Limit text length for safety
                    "role": str(tg.get("role", ""))[:50] if tg.get("role") else None,
                    "bbox_norm": valid_bbox,
                    "t_window": valid_t_window,
                }
            )

        return validated if validated else None

    except Exception as ex:
        logger.warning(f"extract_text_geometries error: {ex}")
        return None


def extract_loop_point(analysis: dict) -> Optional[dict]:
    """Extract loop point information from VDG analysis.

    Searches comment_evidence for signal_type="loop" which indicates
    structural loop potential detected from video analysis.

    Data paths (in priority order):
    1. provenance.comment_evidence_top5 - CORRECT primary path
    2. semantic.audience_reaction.best_comments - fallback

    Returns:
        {
            "loop_point_ms": int,  # Loop transition timestamp
            "evidence_comment_rank": int,  # Supporting comment rank
            "evidence_quote": str,  # First 50 chars of evidence
            "confidence": float,  # 0.7 if anchor_ms present, 0.4 otherwise
            "source": "video_structure"  # Inferred from video, not comments
        }
        or None if no loop potential detected
    """
    if not analysis:
        return None

    try:
        comment_evidence = []

        # Path 1: provenance.comment_evidence_top5 (CORRECT primary path)
        provenance = analysis.get("provenance", {})
        if isinstance(provenance, dict):
            comment_evidence = provenance.get("comment_evidence_top5", [])

        # Path 2: semantic.audience_reaction.best_comments (fallback)
        if not comment_evidence:
            sem = analysis.get("semantic", {})
            if isinstance(sem, dict):
                audience = sem.get("audience_reaction", {})
                if isinstance(audience, dict):
                    comment_evidence = audience.get("best_comments", [])

        if not comment_evidence:
            return None

        # Calculate duration_ms from duration_sec (VDGv4 uses duration_sec)
        duration_sec = analysis.get("duration_sec", 0)
        duration_ms = int(duration_sec * 1000) if duration_sec else 0

        # Find loop signal
        for ce in comment_evidence:
            if not isinstance(ce, dict):
                continue
            if ce.get("signal_type") == "loop":
                anchor_ms = ce.get("anchor_ms")

                # Fallback: use near-end if no anchor
                fallback_ms = (duration_ms - 500) if duration_ms > 500 else None

                return {
                    "loop_point_ms": anchor_ms if anchor_ms else fallback_ms,
                    "evidence_comment_rank": ce.get("rank") or ce.get("comment_rank"),
                    "evidence_quote": (ce.get("text") or ce.get("quote") or "")[:50],
                    "confidence": 0.7 if anchor_ms else 0.4,
                    "source": "video_structure",
                }

        return None

    except Exception as ex:
        logger.warning(f"extract_loop_point error: {ex}")
        return None


def extract_scenes(analysis: dict) -> Optional[List[dict]]:
    """Extract scenes with visual_detail from VDG analysis.

    Supports both VDG v3 (analysis.scenes) and VDG v4/v5 (analysis.semantic.scenes) paths.

    Returns list of scenes:
    [
        {
            "idx": 0,
            "label": "hook",
            "summary": "...",
            "window": {"start_ms": 0, "end_ms": 2500},
            "visual_detail": {...}  # May be None for older VDG data
        }
    ]
    """
    try:
        if not analysis or not isinstance(analysis, dict):
            return None

        # Try multiple paths: VDG 2-Pass llm_output.scenes, VDG v4/v5 semantic.scenes, VDG v3 direct scenes
        scenes = None

        # Path 1: llm_output.scenes (VDG 2-Pass - new unified format)
        llm_output = analysis.get("llm_output", {})
        if isinstance(llm_output, dict) and llm_output.get("scenes"):
            scenes = llm_output["scenes"]

        # Path 2: semantic.scenes (VDG v4/v5 - new format)
        if not scenes:
            semantic = analysis.get("semantic", {})
            if isinstance(semantic, dict) and semantic.get("scenes"):
                scenes = semantic["scenes"]

        # Path 3: direct scenes (VDG v3 - legacy format)
        if not scenes and analysis.get("scenes"):
            scenes = analysis["scenes"]

        if not scenes or not isinstance(scenes, list):
            return None

        # Validate and normalize each scene
        validated = []
        for i, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                continue

            # Required fields - support both VDG v5 (scene_id, time_start, duration_sec) and legacy (idx, label, window)
            idx = scene.get("idx") or scene.get("scene_id", f"S{i+1:02d}")
            label = scene.get("label") or scene.get("narrative_role", "unknown")

            # Time window normalization - support both formats
            window = scene.get("window", {})
            if isinstance(window, dict) and window:
                norm_window = {
                    "start_ms": int(window.get("start_ms", 0) or 0),
                    "end_ms": int(window.get("end_ms", 0) or 0),
                }
            else:
                # VDG v5: time_start (sec) + duration_sec -> convert to ms
                time_start = scene.get("time_start", 0) or 0
                duration_sec = scene.get("duration_sec", 0) or 0
                norm_window = {
                    "start_ms": int(time_start * 1000),
                    "end_ms": int((time_start + duration_sec) * 1000),
                }

            # Visual detail (new VDG v5 field)
            visual_detail = scene.get("visual_detail")
            if visual_detail and isinstance(visual_detail, dict):
                # Normalize visual_detail fields
                norm_vd = {
                    "scene_idx": visual_detail.get("scene_idx", idx),
                    "background": visual_detail.get("background"),
                    "foreground_props": visual_detail.get("foreground_props", []),
                    "text_overlays": visual_detail.get("text_overlays", []),
                    "subject_description": visual_detail.get("subject_description"),
                    "subject_action": visual_detail.get("subject_action"),
                }
            else:
                norm_vd = None

            validated.append(
                {
                    "idx": idx,
                    "label": str(label)[:50],
                    "summary": str(scene.get("summary", ""))[:500],
                    "window": norm_window,
                    "visual_detail": norm_vd,
                }
            )

        return validated if validated else None

    except Exception as ex:
        logger.warning(f"extract_scenes error: {ex}")
        return None


def extract_camera_metadata(analysis: dict) -> Optional[List[dict]]:
    """Extract camera metadata from VDG 2-Pass Visual analysis.

    Returns list of camera metadata per scene:
    [
        {
            "scene_id": "S01",
            "movement_type": "pan_right",
            "movement_intensity": "moderate",
            "steady_score": 0.85,
            "spatial_consistency": 0.9,
            "depth_variation": "shallow"
        }
    ]
    """
    try:
        if not analysis or not isinstance(analysis, dict):
            return None

        # VDG v4/v5: visual.camera_metadata
        visual = analysis.get("visual", {})
        if not isinstance(visual, dict):
            return None

        camera_metadata = visual.get("camera_metadata", [])

        if not camera_metadata or not isinstance(camera_metadata, list):
            return None

        validated = []
        for cm in camera_metadata:
            if not isinstance(cm, dict):
                continue

            # Extract and validate fields
            movement_type = cm.get("movement_type")
            if hasattr(movement_type, "value"):
                movement_type = movement_type.value  # Handle enum

            validated.append(
                {
                    "scene_id": str(cm.get("scene_id", ""))[:20],
                    "movement_type": str(movement_type or "static")[:30],
                    "movement_intensity": str(cm.get("movement_intensity", "subtle"))[:20],
                    "steady_score": float(cm.get("steady_score", 0.8)),
                    "spatial_consistency": float(cm.get("spatial_consistency", 0.8)),
                    "depth_variation": str(cm.get("depth_variation", "shallow"))[:20],
                }
            )

        return validated if validated else None

    except Exception as ex:
        logger.warning(f"extract_camera_metadata error: {ex}")
        return None


# ==================
# DIRECTOR PACK BASED SHOOTING GUIDE (L2 Integration)
# ==================


def extract_shooting_guide_from_director_pack(director_pack: dict) -> dict:
    """
    DirectorPack → 촬영 가이드 추출 (L2 Integration)

    VDG v4.0 DirectorPack의 DNAInvariant, MutationSlot, ForbiddenMutation을
    카드 상세의 가이드로 변환

    Returns:
        {
            "invariant": [...],  # 필수 요소 (DNAInvariant)
            "variable": [...],    # 변주 가능 (MutationSlot)
            "do_not": [...],      # 금지 사항 (ForbiddenMutation)
            "checkpoints": [...]  # 시간별 체크포인트
        }
    """
    guide = {
        "invariant": [],
        "variable": [],
        "do_not": [],
        "checkpoints": [],
    }

    # Priority emoji map
    priority_emoji = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "⚪",
    }

    # Domain emoji map
    domain_emoji = {
        "hook": "🎣",
        "timing": "⏱️",
        "composition": "📷",
        "pacing": "🎵",
        "audio": "🎤",
    }

    # 1. DNAInvariant → 필수 요소
    dna_invariants = director_pack.get("dna_invariants", [])
    for rule in dna_invariants[:5]:  # Top 5
        emoji = priority_emoji.get(rule.get("priority", "medium"), "")
        domain = rule.get("domain", "")
        domain_ico = domain_emoji.get(domain, "📌")

        # Use coach_line (friendly tone) or check_hint
        templates = rule.get("coach_line_templates", {})
        text = (
            templates.get("friendly")
            or templates.get("neutral")
            or rule.get("check_hint")
            or rule.get("description", "")
        )

        if text:
            guide["invariant"].append(f"{emoji}{domain_ico} {text}")

    # 2. MutationSlot → 변주 가능 요소
    mutation_slots = director_pack.get("mutation_slots", [])
    for slot in mutation_slots[:3]:
        slot_type = slot.get("slot_type", "")
        slot_guide = slot.get("guide", "")
        options = slot.get("options", [])

        if slot_guide:
            options_str = ", ".join(options[:3]) if options else "자유롭게"
            guide["variable"].append(f"🎨 {slot_type}: {slot_guide} ({options_str})")

    # 3. ForbiddenMutation → 금지 사항
    forbidden = director_pack.get("forbidden_mutations", [])
    for fm in forbidden[:3]:
        reason = fm.get("reason", "")
        if reason:
            guide["do_not"].append(f"❌ {reason}")

    # 4. Checkpoints → 시간별 가이드
    checkpoints = director_pack.get("checkpoints", [])
    for cp in checkpoints[:5]:
        t_window = cp.get("t_window", [0, 0])
        note = cp.get("note", "")
        if note and cp.get("checkpoint_id") != "overall":
            guide["checkpoints"].append(f"⏰ {t_window[0]:.0f}-{t_window[1]:.0f}초: {note}")

    return guide


def determine_variation_type(similarity: float) -> str:
    """
    유사도 점수로 변주 유형 결정

    - 0.95+ : homage (거의 복제)
    - 0.85-0.95 : remix (약간의 변형)
    - 0.75-0.85 : trend_follow (트렌드 따라하기)
    """
    if similarity >= 0.95:
        return "homage"
    elif similarity >= 0.85:
        return "remix"
    else:
        return "trend_follow"
