"""
VDG → DB 저장 서비스 (P1-1 완전 통합)

VDG 분석 결과를 정규화된 테이블에 저장:
1. viral_kicks 테이블에 개별 kick 저장
2. keyframe_evidences 테이블에 CV 검증된 keyframes 저장
3. comment_evidences 테이블에 댓글 증거 저장
4. cinematography 필드 (shot_type, composition, lighting 등) 저장

사용:
    from app.services.vdg_2pass.vdg_db_saver import vdg_db_saver
    await vdg_db_saver.save_vdg_to_db(db, node_id, vdg_data, video_path)
"""

import hashlib
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Vocabulary imports for normalization
from app.services.vdg_2pass.vocab import (
    normalize_shot_type,
    normalize_composition,
    normalize_lighting,
    normalize_camera_angle,
    normalize_movement,
    normalize_lens,
    infer_composition_from_description,
    infer_lighting_from_description,
)
from app.services.vdg_feature_extractor import get_feature_extractor

logger = logging.getLogger(__name__)

# === Category Normalization (2026-01-26) ===
# 10개 유효 카테고리 (allow-list)
VALID_CATEGORIES = {
    "beauty",
    "meme",
    "food",
    "fashion",
    "art",
    "sports",
    "tech",
    "entertainment",
    "game",
    "fandom",
}

# Gemini가 반환하는 비표준 값 → 정규화 매핑
CATEGORY_MAPPING = {
    # 정확히 일치 (10개)
    "beauty": "beauty",
    "meme": "meme",
    "food": "food",
    "fashion": "fashion",
    "art": "art",
    "sports": "sports",
    "tech": "tech",
    "entertainment": "entertainment",
    "game": "game",
    "fandom": "fandom",
    # 스포츠 관련
    "basketball": "sports",
    "padel": "sports",
    "fitness": "sports",
    "soccer": "sports",
    "football": "sports",
    "tennis": "sports",
    "golf": "sports",
    "workout": "sports",
    "gym": "sports",
    # 밈/유머 관련
    "trending": "meme",
    "comedy": "meme",
    "humor": "meme",
    "funny": "meme",
    "viral": "meme",
    # 팬덤 관련
    "movies-tv": "fandom",
    "drama": "fandom",
    "kpop": "fandom",
    "k-pop": "fandom",
    "idol": "fandom",
    "anime": "fandom",
    "movie": "fandom",
    "tv": "fandom",
    # 엔터테인먼트 관련
    "travel": "entertainment",
    "music": "entertainment",
    "pet": "entertainment",
    "education": "entertainment",
    "lifestyle": "entertainment",
    "dance": "entertainment",
    "vlog": "entertainment",
    # 게임 관련
    "gaming": "game",
    "esports": "game",
    "e-sports": "game",
}

# 제목/해시태그 기반 카테고리 추론 키워드
KEYWORD_TO_CATEGORY = {
    # beauty
    "lipstick": "beauty",
    "makeup": "beauty",
    "skincare": "beauty",
    "cosmetic": "beauty",
    "화장": "beauty",
    "메이크업": "beauty",
    # sports
    "basketball": "sports",
    "padel": "sports",
    "fitness": "sports",
    "workout": "sports",
    "gym": "sports",
    "축구": "sports",
    "농구": "sports",
    # food
    "food": "food",
    "먹방": "food",
    "recipe": "food",
    "cooking": "food",
    "국밥": "food",
    "맛집": "food",
    "카페": "food",
    "요리": "food",
    # meme
    "funny": "meme",
    "meme": "meme",
    "comedy": "meme",
    "웃긴": "meme",
    "ㅋㅋ": "meme",
    "emotional damage": "meme",
    "lol": "meme",
    # fandom
    "strangerthings": "fandom",
    "stranger things": "fandom",
    "mileven": "fandom",
    "vecna": "fandom",
    "netflix": "fandom",
    "bts": "fandom",
    "blackpink": "fandom",
    "아이돌": "fandom",
    # tech
    "chatgpt": "tech",
    "ai": "tech",
    "tech": "tech",
    "gadget": "tech",
    "app": "tech",
    "gpt": "tech",
    "coding": "tech",
    # game
    "game": "game",
    "gaming": "game",
    "esports": "game",
    "게임": "game",
    "플레이": "game",
    # entertainment
    "vlog": "entertainment",
    "daily": "entertainment",
    "fyp": "entertainment",
    "viral": "entertainment",
}


def _normalize_category(raw_category: str) -> Optional[str]:
    """
    Gemini 반환값을 정규화된 카테고리로 변환

    Args:
        raw_category: Gemini가 반환한 content_category 값

    Returns:
        정규화된 카테고리 (10개 중 하나) 또는 None
    """
    if not raw_category:
        return None
    lower = raw_category.lower().strip()
    return CATEGORY_MAPPING.get(lower)


def _infer_category_from_title(title: str, hashtags: Optional[List[str]] = None) -> Optional[str]:
    """
    제목/해시태그 기반으로 카테고리 추론 (fallback용)

    Args:
        title: 영상 제목
        hashtags: 해시태그 목록

    Returns:
        추론된 카테고리 또는 None
    """
    if not title:
        return None

    text = title.lower()
    if hashtags:
        text += " " + " ".join(h.lower() for h in hashtags if h)

    for keyword, category in KEYWORD_TO_CATEGORY.items():
        if keyword in text:
            return category

    return None


class VDGDatabaseSaver:
    """
    VDG 분석 결과 → 정규화된 DB 저장

    viral_kicks, keyframe_evidences, comment_evidences 테이블에
    조인 가능한 형태로 저장

    Phase 1: Cinematography Pipeline 추가
    - mise_en_scene_signals에서 composition/lighting 추출
    - hook_genome.microbeats에서 shot_type 추출
    - scenes.visual_detail에서 lighting_quality 추출
    """

    def _extract_cinematography_data(self, vdg_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        VDG 데이터에서 전체 cinematography 정보 추출

        Returns:
            {
                'mise_en_scene_signals': [...],
                'shot_type_by_time': {t_ms: shot_type, ...},
                'lighting_by_time': {t_ms: lighting_type, ...},
                'camera_physics': {...},
            }
        """
        result = {
            "mise_en_scene_signals": [],
            "shot_type_by_time": {},
            "lighting_by_time": {},
            "camera_physics": {},
            "shotlist": [],
        }

        # 1. MiseEnScene signals 추출
        signals = vdg_data.get("mise_en_scene_signals", [])
        for s in signals:
            if isinstance(s, dict):
                result["mise_en_scene_signals"].append(
                    {
                        "type": s.get("type"),
                        "description": s.get("description"),
                        "anchor_ms": s.get("anchor_ms"),
                        "why_it_matters": s.get("why_it_matters"),
                    }
                )

        # 2. Hook genome microbeats에서 shot_type 추출
        hook = vdg_data.get("hook_genome", {})
        if isinstance(hook, dict):
            for mb in hook.get("microbeats", []):
                if isinstance(mb, dict):
                    t_ms = mb.get("t_start_ms") or mb.get("t_ms")
                    if t_ms is not None and mb.get("shot_type"):
                        result["shot_type_by_time"][t_ms] = mb["shot_type"]

        # 3. Scenes의 visual_detail에서 lighting 추출
        for scene in vdg_data.get("scenes", []):
            if isinstance(scene, dict):
                vd = scene.get("visual_detail", {})
                if isinstance(vd, dict) and vd:
                    bg = vd.get("background", {})
                    if isinstance(bg, dict):
                        lighting = bg.get("lighting_quality")
                        if lighting:
                            window = scene.get("window", {})
                            start_ms = window.get("start_ms", 0) if isinstance(window, dict) else 0
                            result["lighting_by_time"][start_ms] = lighting

        # 4. Camera physics 추출
        impl = vdg_data.get("implementation_layer", {})
        if isinstance(impl, dict):
            result["camera_physics"] = impl.get("camera_physics", {}) or {}

        # 5. Capsule brief shotlist 추출
        cb = vdg_data.get("capsule_brief", {})
        if isinstance(cb, dict):
            result["shotlist"] = cb.get("shotlist", []) or []

        return result

    def _get_keyframe_cinematography(
        self,
        kf: Dict[str, Any],
        kick_window: Tuple[int, int],
        cine_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        개별 키프레임의 cinematography 데이터 계산

        Returns:
            {
                'shot_type': str or None,
                'composition_grid': str or None,
                'lighting_type': str or None,
                'lens_type': str or None,
                'camera_movement': str or None,
                'extraction_source': 'llm',
                'extraction_confidence': 0.7,
                'raw_values': {...}
            }
        """
        t_ms = kf.get("t_ms", 0) if isinstance(kf, dict) else getattr(kf, "t_ms", 0)
        raw_values = {}

        # Shot type (시간 기반 매칭 - 가장 가까운 microbeat)
        shot_type = None
        min_diff = float("inf")
        for mb_t, st in cine_data["shot_type_by_time"].items():
            diff = abs(mb_t - t_ms)
            if diff < min_diff and diff < 3000:  # 3초 이내
                min_diff = diff
                normalized, raw = normalize_shot_type(st)
                shot_type = normalized
                if raw:
                    raw_values["shot_type"] = raw

        # Composition (mise_en_scene_signals에서 - kick window 내 우선)
        composition = None
        for s in cine_data["mise_en_scene_signals"]:
            if s.get("type") == "composition":
                anchor = s.get("anchor_ms", 0)
                if kick_window[0] <= anchor <= kick_window[1]:
                    normalized, raw = infer_composition_from_description(s.get("description", ""))
                    composition = normalized
                    if raw:
                        raw_values["composition"] = raw
                    break
        # Fallback: 아무 composition signal
        if not composition:
            for s in cine_data["mise_en_scene_signals"]:
                if s.get("type") == "composition":
                    normalized, raw = infer_composition_from_description(s.get("description", ""))
                    composition = normalized
                    if raw:
                        raw_values["composition"] = raw
                    break

        # Lighting (scene visual_detail 또는 mise_en_scene_signals)
        lighting = None

        # 먼저 visual_detail에서 (시간순 폴백)
        for scene_t, lq in sorted(cine_data["lighting_by_time"].items()):
            if scene_t <= t_ms:
                normalized, raw = normalize_lighting(lq)
                lighting = normalized
                if raw:
                    raw_values["lighting"] = raw

        # 없으면 mise_en_scene_signals에서
        if not lighting:
            for s in cine_data["mise_en_scene_signals"]:
                if s.get("type") == "lighting":
                    normalized, raw = infer_lighting_from_description(s.get("description", ""))
                    lighting = normalized
                    if raw:
                        raw_values["lighting"] = raw
                    break

        # Camera physics (전체 비디오 레벨)
        cp = cine_data.get("camera_physics", {})

        lens_type = None
        if cp.get("lens_type"):
            normalized, raw = normalize_lens(cp["lens_type"])
            lens_type = normalized
            if raw:
                raw_values["lens_type"] = raw

        movement = None
        if cp.get("movement_type"):
            normalized, raw = normalize_movement(cp["movement_type"])
            movement = normalized
            if raw:
                raw_values["movement"] = raw

        return {
            "shot_type": shot_type if shot_type != "other" else None,
            "composition_grid": composition if composition != "other" else None,
            "lighting_type": lighting if lighting != "other" else None,
            "lens_type": lens_type if lens_type != "other" else None,
            "camera_movement": movement if movement != "other" else None,
            "extraction_source": "llm",
            "extraction_confidence": 0.7,
            "raw_values": raw_values if raw_values else None,
        }

    def _build_mise_en_scene_snapshot(
        self,
        kick_window: Tuple[int, int],
        cine_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        ViralKick용 mise_en_scene 스냅샷 생성
        """
        snapshot = {
            "composition": None,
            "lighting": None,
            "camera": {},
            "provenance": {
                "source": "llm",
                "confidence": 0.7,
            },
        }

        # Composition (kick window 내 우선)
        for s in cine_data["mise_en_scene_signals"]:
            if s.get("type") == "composition":
                anchor = s.get("anchor_ms", 0)
                if kick_window[0] <= anchor <= kick_window[1]:
                    normalized, _ = infer_composition_from_description(s.get("description", ""))
                    snapshot["composition"] = {
                        "type": normalized,
                        "description": s.get("description"),
                        "anchor_ms": anchor,
                    }
                    break

        # Lighting
        for s in cine_data["mise_en_scene_signals"]:
            if s.get("type") == "lighting":
                anchor = s.get("anchor_ms", 0)
                if kick_window[0] <= anchor <= kick_window[1]:
                    normalized, _ = infer_lighting_from_description(s.get("description", ""))
                    snapshot["lighting"] = {
                        "type": normalized,
                        "description": s.get("description"),
                        "anchor_ms": anchor,
                    }
                    break

        # Camera physics
        cp = cine_data.get("camera_physics", {})
        if cp:
            snapshot["camera"] = {
                "lens_type": cp.get("lens_type"),
                "movement_type": cp.get("movement_type"),
            }

        # 비어있으면 None
        if not snapshot["composition"] and not snapshot["lighting"] and not snapshot["camera"]:
            return None

        return snapshot

    def _parse_shotlist_items(self, shotlist: List[Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Capsule brief shotlist를 정규화된 형태로 파싱
        """
        if not shotlist:
            return None

        items = []
        for idx, item in enumerate(shotlist):
            if isinstance(item, str):
                # "클로즈업으로 제품 강조" → shot_type 추론
                normalized, _ = infer_composition_from_description(item)
                # shot_type 키워드 체크
                shot_type = None
                lower = item.lower()
                for kw, st in [("클로즈업", "close_up"), ("와이드", "wide"), ("미디엄", "medium")]:
                    if kw in lower:
                        shot_type = st
                        break

                items.append(
                    {
                        "idx": idx,
                        "shot_type": shot_type,
                        "action": item[:100],
                    }
                )
            elif isinstance(item, dict):
                items.append(
                    {
                        "idx": idx,
                        "shot_type": item.get("shot") or item.get("shot_type"),
                        "action": item.get("action", "")[:100],
                        "duration": item.get("duration"),
                    }
                )

        return items if items else None

    async def save_vdg_to_db(
        self,
        db: AsyncSession,
        node_id: str,
        vdg_data: Dict[str, Any],
        video_path: Optional[str] = None,
        outlier_item_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        VDG 분석 결과를 DB에 저장

        Args:
            db: Database session
            node_id: RemixNode ID (UUID string)
            vdg_data: VDG 분석 결과 (dict)
            video_path: 비디오 파일 경로 (keyframe 검증용)
            outlier_item_id: OutlierItem ID (optional)

        Returns:
            {
                "kicks_saved": int,
                "keyframes_saved": int,
                "comments_saved": int,
                "proof_ready": bool,
            }
        """
        from app.models import ViralKick, KeyframeEvidence, CommentEvidence, ViralKickStatus, RemixNode
        from app.services.vdg_2pass.quality_gate import proof_grade_gate
        from app.services.vdg_2pass.keyframe_verifier import keyframe_verifier, CV2_AVAILABLE

        logger.info(f"💾 Saving VDG to DB for node {node_id}")

        # 0. Early validation: Reject empty node_id immediately
        # This catches cases where session expiry caused node.id to return ""
        if not node_id or not node_id.strip():
            logger.error("[DataQuality] save_vdg_to_db called with empty node_id")
            return {"error": "node_id cannot be empty"}

        # 1. Node UUID 확인
        try:
            node_uuid = uuid.UUID(node_id)
        except ValueError:
            # node_id가 UUID가 아니면 DB에서 찾기
            result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
            node = result.scalar_one_or_none()
            if not node:
                logger.error(f"Node not found: {node_id}")
                return {"error": f"Node not found: {node_id}"}
            node_uuid = node.id

        # 1a. Node UUID 유효성 검증 (빈 문자열 방어)
        if not node_uuid or str(node_uuid) == "":
            logger.error(f"Invalid node_uuid for {node_id}: empty or null")
            return {"error": f"Invalid node_uuid for {node_id}"}

        # 2. OutlierItem UUID
        outlier_uuid = None
        if outlier_item_id:
            try:
                outlier_uuid = uuid.UUID(outlier_item_id)
            except ValueError:
                pass

        # 3. VDG 데이터 추출 (여러 경로에서 fallback)
        provenance = vdg_data.get("provenance", {})

        # viral_kicks: provenance에 없으면 직접 필드 체크
        viral_kicks = provenance.get("viral_kicks", [])
        if not viral_kicks:
            viral_kicks = vdg_data.get("viral_kicks", [])

        # comment_evidence: provenance에 없으면 직접 필드 체크
        comment_evidence_top5 = provenance.get("comment_evidence_top5", [])
        if not comment_evidence_top5:
            comment_evidence_top5 = vdg_data.get("comment_evidence_top5", [])

        kicks_saved = 0
        keyframes_saved = 0
        comments_saved = 0

        # 4. Comment Evidence 먼저 저장 (viral_kicks 유무와 무관하게)
        # VDG가 부분 실패해도 댓글은 저장되어야 함
        comment_map = {}  # rank → evidence_id
        for i, comment in enumerate(comment_evidence_top5[:5]):
            if isinstance(comment, str):
                text = comment
                likes = 0
            else:
                text = comment.get("text", "") or str(comment)
                likes = comment.get("likes", 0) or 0

            text_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
            node_prefix = str(node_uuid)[:8]
            evidence_id = f"ev.comment.{node_prefix}.{text_hash}"

            # 중복 체크
            existing = await db.execute(select(CommentEvidence).where(CommentEvidence.evidence_id == evidence_id))
            if existing.scalar_one_or_none():
                comment_map[i + 1] = evidence_id
                continue

            comment_evidence = CommentEvidence(
                evidence_id=evidence_id,
                node_id=node_uuid,
                text_snippet=text[:500],
                like_count=likes,
                rank=i + 1,
                matched_kick_ids=[],
            )
            db.add(comment_evidence)
            comments_saved += 1
            comment_map[i + 1] = evidence_id

        # 5. viral_kicks가 없으면 early return (댓글은 이미 저장됨)
        if not viral_kicks:
            logger.info(f"No viral_kicks for node {node_id}, but saved {comments_saved} comments")
            return {
                "kicks_saved": 0,
                "keyframes_saved": 0,
                "comments_saved": comments_saved,
                "proof_ready": False,
                "warning": "no_viral_kicks_in_vdg_data",
            }

        # 6. Quality Gate 체크 (이미 되어있으면 재사용)
        meta = vdg_data.get("meta", {})
        proof_ready = meta.get("proof_ready", False)

        if "proof_ready" not in meta:
            # Duration 추정
            duration_ms = 60000  # Default 1분
            if video_path:
                try:
                    from app.services.vdg_2pass.unified_pass import get_video_duration_ms

                    duration_ms = get_video_duration_ms(video_path)
                except ImportError as e:
                    logger.warning(f"Could not import get_video_duration_ms: {e}")
                except (OSError, FileNotFoundError) as e:
                    logger.warning(f"Video file access error for {video_path}: {e}")

            proof_ready, _ = proof_grade_gate.validate(vdg_data, duration_ms)

        # 6a. Cinematography 데이터 추출 (Phase 1)
        cine_data = self._extract_cinematography_data(vdg_data)

        # 7. Viral Kicks 저장
        for kick_data in viral_kicks:
            if isinstance(kick_data, dict):
                kick_index = kick_data.get("kick_index", 1)
                title = kick_data.get("title", f"Kick {kick_index}")
                mechanism = kick_data.get("mechanism", "")
                creator_instruction = kick_data.get("creator_instruction", "")

                # Handle both formats: window dict OR direct t_start_ms/t_end_ms
                window = kick_data.get("window", {})
                if isinstance(window, dict) and window:
                    start_ms = window.get("start_ms", 0)
                    end_ms = window.get("end_ms", 5000)
                else:
                    # VDG pipeline stores t_start_ms/t_end_ms directly
                    start_ms = kick_data.get("t_start_ms", 0)
                    end_ms = kick_data.get("t_end_ms", 5000)

                keyframes_data = kick_data.get("keyframes", [])
                evidence_ranks = kick_data.get("evidence_comment_ranks", [])
                confidence = kick_data.get("confidence", 0.7)
                missing_reason = kick_data.get("missing_reason")
            else:
                # Pydantic model
                kick_index = getattr(kick_data, "kick_index", 1)
                title = getattr(kick_data, "title", f"Kick {kick_index}")
                mechanism = getattr(kick_data, "mechanism", "")
                creator_instruction = getattr(kick_data, "creator_instruction", "")

                window = getattr(kick_data, "window", None)
                start_ms = window.start_ms if window else 0
                end_ms = window.end_ms if window else 5000

                keyframes_data = getattr(kick_data, "keyframes", []) or []
                evidence_ranks = getattr(kick_data, "evidence_comment_ranks", []) or []
                confidence = getattr(kick_data, "confidence", 0.7)
                missing_reason = getattr(kick_data, "missing_reason", None)

            # Kick ID 생성 (node_id가 8자 미만일 수 있음)
            node_prefix = str(node_id)[:8] if node_id else "unknown"
            kick_id = f"vk_{node_prefix}_{kick_index}"

            # 중복 체크
            existing_kick = await db.execute(select(ViralKick).where(ViralKick.kick_id == kick_id))
            if existing_kick.scalar_one_or_none():
                logger.warning(f"Kick already exists: {kick_id}")
                continue

            # Comment evidence refs
            comment_refs = [comment_map.get(r) for r in evidence_ranks if r in comment_map]

            # Peak MS (keyframes에서)
            peak_ms = None
            for kf in keyframes_data:
                if isinstance(kf, dict):
                    if kf.get("role") == "peak":
                        peak_ms = kf.get("t_ms")
                else:
                    if getattr(kf, "role", "") == "peak":
                        peak_ms = getattr(kf, "t_ms", None)

            # ViralKick 생성
            # Null safety for string fields
            safe_title = (title or f"Kick {kick_index}")[:200]
            safe_mechanism = (mechanism or "Unknown")[:500]
            safe_instruction = (creator_instruction or "")[:500] or None

            viral_kick = ViralKick(
                kick_id=kick_id,
                node_id=node_uuid,
                outlier_item_id=outlier_uuid,
                kick_index=kick_index,
                title=safe_title,
                mechanism=safe_mechanism,
                creator_instruction=safe_instruction,
                start_ms=start_ms,
                end_ms=end_ms,
                peak_ms=peak_ms,
                confidence=confidence,
                missing_reason=missing_reason,
                proof_ready=proof_ready and confidence >= 0.6 and len(keyframes_data) >= 3,
                comment_evidence_ids=comment_refs,
                frame_evidence_ids=[],  # CV 검증 후 채움
                evidence_comment_ranks=evidence_ranks,
                status=ViralKickStatus.PENDING,
                # Phase 1: Cinematography 필드
                mise_en_scene_snapshot=self._build_mise_en_scene_snapshot((start_ms, end_ms), cine_data),
                shotlist_items=self._parse_shotlist_items(cine_data.get("shotlist", [])),
            )
            db.add(viral_kick)
            await db.flush()  # ID 할당
            kicks_saved += 1

            # 7. Keyframe Evidences 저장 (CV 검증)
            frame_evidence_ids = []

            for kf in keyframes_data:
                if isinstance(kf, dict):
                    t_ms = kf.get("t_ms", 0)
                    role = kf.get("role", "unknown")
                    what_to_see = kf.get("what_to_see", "")
                else:
                    t_ms = getattr(kf, "t_ms", 0)
                    role = getattr(kf, "role", "unknown")
                    what_to_see = getattr(kf, "what_to_see", "")

                # Evidence ID
                frame_hash = hashlib.md5(f"{node_id}_{kick_index}_{role}_{t_ms}".encode()).hexdigest()[:8]
                evidence_id = f"ev.frame.k{kick_index}.{role}.{frame_hash}"

                # 중복 체크
                existing_kf = await db.execute(
                    select(KeyframeEvidence).where(KeyframeEvidence.evidence_id == evidence_id)
                )
                if existing_kf.scalar_one_or_none():
                    frame_evidence_ids.append(evidence_id)
                    continue

                # CV 검증 (video_path 있을 때만)
                blur_score = None
                brightness = None
                motion_proxy = None
                verified = False
                verification_reason = "no_video_path"

                if video_path and CV2_AVAILABLE:
                    try:
                        import cv2

                        cap = cv2.VideoCapture(video_path)
                        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                        frame_num = int((t_ms / 1000) * fps)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                        ret, frame = cap.read()
                        cap.release()

                        if ret and frame is not None:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                            brightness = float(gray.mean())
                            verified = True
                            verification_reason = None
                        else:
                            verification_reason = "frame_extraction_failed"
                    except Exception as e:
                        verification_reason = f"cv_error: {str(e)[:50]}"

                # Phase 1: Cinematography 필드 추출
                kf_cine = self._get_keyframe_cinematography(
                    kf if isinstance(kf, dict) else {"t_ms": t_ms, "role": role}, (start_ms, end_ms), cine_data
                )

                keyframe_evidence = KeyframeEvidence(
                    evidence_id=evidence_id,
                    kick_id=viral_kick.id,
                    node_id=node_uuid,
                    role=role,
                    t_ms=t_ms,
                    what_to_see=what_to_see[:200] if what_to_see else None,
                    blur_score=round(blur_score, 2) if blur_score else None,
                    brightness=round(brightness, 2) if brightness else None,
                    motion_proxy=motion_proxy,
                    frame_hash=frame_hash,
                    verified=verified,
                    verification_reason=verification_reason,
                    # Phase 1: Cinematography 필드
                    shot_type=kf_cine.get("shot_type"),
                    composition_grid=kf_cine.get("composition_grid"),
                    lighting_type=kf_cine.get("lighting_type"),
                    lens_type=kf_cine.get("lens_type"),
                    camera_movement=kf_cine.get("camera_movement"),
                    extraction_source=kf_cine.get("extraction_source"),
                    extraction_confidence=kf_cine.get("extraction_confidence"),
                    raw_values=kf_cine.get("raw_values"),
                )
                db.add(keyframe_evidence)
                keyframes_saved += 1
                frame_evidence_ids.append(evidence_id)

            # Frame evidence IDs 업데이트
            viral_kick.frame_evidence_ids = frame_evidence_ids

        # === P2: Feature Vector 저장 (ML Drift Detection) ===
        if outlier_uuid:
            try:
                from app.models import OutlierItem
                from app.services.vdg_2pass.quality_gate import proof_grade_gate

                extractor = get_feature_extractor()
                feature_vector = extractor.extract_features(vdg_data)
                quality_score = extractor.calculate_quality_score(feature_vector)

                outlier_item = await db.get(OutlierItem, outlier_uuid)
                if outlier_item:
                    outlier_item.vdg_feature_vector = feature_vector
                    outlier_item.vdg_quality_score = quality_score

                    # === P1: visual_empty 플래그 설정 (2026-01-20) ===
                    visual_empty = proof_grade_gate._check_visual_empty(vdg_data)
                    media_missing = proof_grade_gate._check_media_missing(vdg_data)

                    outlier_item.visual_empty = visual_empty
                    if visual_empty or media_missing:
                        reasons = []
                        if visual_empty:
                            reasons.append("entity_tracks_empty")
                        if media_missing:
                            reasons.append("media_metadata_missing")
                        outlier_item.failure_reason = ",".join(reasons)
                        logger.warning(
                            f"[VDG P1] Quality issue detected for {outlier_item_id}: "
                            f"visual_empty={visual_empty}, media_missing={media_missing}"
                        )
                    # === End P1 ===

                    # === Content Category 추출 및 저장 (2026-01-26 개선) ===
                    intent_layer = vdg_data.get("intent_layer", {})
                    content_category = intent_layer.get("content_category", "")

                    # Step 1: Gemini 응답 정규화
                    normalized_category = _normalize_category(content_category)

                    # Step 2: Fallback - 제목/해시태그 기반 추론
                    if not normalized_category and outlier_item.title:
                        hashtags = None
                        # vdg_data에서 해시태그 추출 시도
                        if vdg_data.get("hashtags"):
                            hashtags = vdg_data.get("hashtags")
                        normalized_category = _infer_category_from_title(outlier_item.title, hashtags)
                        if normalized_category:
                            logger.info(f"[VDG] Category inferred from title: {normalized_category}")

                    # Step 3: 카테고리 저장
                    if normalized_category:
                        old_category = outlier_item.category
                        outlier_item.category = normalized_category
                        logger.info(
                            f"[VDG] Content category saved: {content_category} → {normalized_category}"
                            f" (was: {old_category})"
                        )
                    # === End Content Category ===

                    logger.info(
                        f"[VDG P2] Feature vector saved: quality={quality_score:.3f}, "
                        f"features={list(feature_vector.keys())}"
                    )
            except Exception as e:
                logger.warning(f"[VDG P2] Feature extraction failed: {e}")
        # === End P2 ===

        # 8. Commit with rollback handling
        committed = False
        try:
            await db.commit()
            committed = True

            logger.info(
                f"✅ VDG saved to DB: {kicks_saved} kicks, " f"{keyframes_saved} keyframes, {comments_saved} comments"
            )

            return {
                "kicks_saved": kicks_saved,
                "keyframes_saved": keyframes_saved,
                "comments_saved": comments_saved,
                "proof_ready": proof_ready,
            }
        except Exception as e:
            if not committed:
                await db.rollback()
            logger.error(f"❌ VDG save failed for node {node_id}: {e}")
            raise

    async def get_kicks_for_node(
        self,
        db: AsyncSession,
        node_id: str,
    ) -> List[Dict[str, Any]]:
        """노드의 저장된 kicks 조회"""
        from app.models import ViralKick, RemixNode

        # Node UUID 찾기
        try:
            node_uuid = uuid.UUID(node_id)
        except ValueError:
            result = await db.execute(select(RemixNode).where(RemixNode.node_id == node_id))
            node = result.scalar_one_or_none()
            if not node:
                return []
            node_uuid = node.id

        result = await db.execute(select(ViralKick).where(ViralKick.node_id == node_uuid))
        kicks = result.scalars().all()

        return [
            {
                "kick_id": k.kick_id,
                "title": k.title,
                "mechanism": k.mechanism,
                "confidence": k.confidence,
                "proof_ready": k.proof_ready,
                "status": k.status.value if hasattr(k.status, "value") else k.status,
            }
            for k in kicks
        ]


# Singleton
vdg_db_saver = VDGDatabaseSaver()
