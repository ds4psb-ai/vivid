"""
Foreshadow Agent - 복선 회수 분석기

장편 콘텐츠에서 설정된 복선과 회수 여부를 추적하고,
미회수 복선에 대한 활용 제안을 생성합니다.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
import re

from pydantic import BaseModel

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("foreshadow_agent")


# =============================================================================
# Schemas
# =============================================================================

class NarrativeSeed(BaseModel):
    """서사적 씨앗 (복선)"""
    id: str
    description: str
    planted_at: str  # "1막", "씬 3" 등
    planted_text: str  # 복선이 심어진 원문
    importance: str  # 'major', 'minor'
    expected_payoff: Optional[str] = None


class Payoff(BaseModel):
    """복선의 회수"""
    seed_id: str
    resolved_at: str  # "3막", "씬 12" 등
    resolved_text: str
    resolution_quality: str  # 'strong', 'weak', 'partial'


class ForeshadowAnalysis(BaseModel):
    """복선 분석 결과"""
    total_seeds: int
    resolved_seeds: int
    orphaned_seeds: List[NarrativeSeed]  # 미회수 복선
    weak_resolutions: List[Dict[str, Any]]  # 약한 회수
    suggestions: List[Dict[str, Any]]  # 활용 제안
    analysis_score: float  # 0-1


# =============================================================================
# Pattern Detection
# =============================================================================

FORESHADOW_PATTERNS = [
    # 물건/소품 언급
    (r"(낡은|오래된|mysterious|이상한|특별한)\s+(\w+)(을|를|이|가)", "object"),
    # 과거 언급
    (r"(예전에|그때|어릴 적|오래전)", "backstory"),
    # 비밀/숨김
    (r"(비밀|숨기|감추|몰래)", "secret"),
    # 예고/암시
    (r"(언젠가|곧|조만간|머지않아)", "foreshadow"),
    # 반복 모티프
    (r"(항상|매번|늘|계속)", "motif"),
    # 의미심장한 대사
    (r"(기억해|잊지 마|명심해)", "reminder"),
]

PAYOFF_PATTERNS = [
    # 회상/플래시백
    (r"(떠올리|기억하|회상)", "flashback"),
    # 발견/깨달음
    (r"(알아차리|깨달|발견하|눈치)", "revelation"),
    # 진실 폭로
    (r"(사실은|알고 보니|결국|드디어)", "truth"),
    # 물건 재등장
    (r"(그때 그|그 (낡은|오래된))", "object_return"),
]


# =============================================================================
# Foreshadow Agent
# =============================================================================

class ForeshadowAgent:
    """
    복선 회수 추적 에이전트
    
    장편 시나리오에서 복선을 식별하고 회수 여부를 분석합니다.
    """
    
    async def analyze_narrative(
        self,
        full_script: str,
        segments: Optional[List[Dict[str, str]]] = None,
    ) -> ForeshadowAnalysis:
        """
        시나리오 전체를 분석하여 복선과 회수를 추적합니다.
        
        Args:
            full_script: 전체 시나리오 텍스트
            segments: 선택적 세그먼트 정보 [{"label": "1막", "content": "..."}]
        """
        logger.info(
            "Analyzing narrative for foreshadowing",
            extra={"script_length": len(full_script)}
        )
        
        # 1. 복선 탐지
        seeds = self._detect_seeds(full_script, segments)
        
        # 2. 회수 탐지
        payoffs = self._detect_payoffs(full_script, segments)
        
        # 3. 매칭 분석
        matched, orphaned, weak = self._analyze_matches(seeds, payoffs, full_script)
        
        # 4. 제안 생성
        suggestions = self._generate_suggestions(orphaned, weak)
        
        # 5. 점수 계산
        score = self._calculate_score(len(seeds), len(matched), len(weak))
        
        result = ForeshadowAnalysis(
            total_seeds=len(seeds),
            resolved_seeds=len(matched),
            orphaned_seeds=orphaned,
            weak_resolutions=weak,
            suggestions=suggestions,
            analysis_score=score,
        )
        
        logger.info(
            "Foreshadow analysis complete",
            extra={
                "total_seeds": len(seeds),
                "orphaned": len(orphaned),
                "score": score,
            }
        )
        
        return result
    
    def _detect_seeds(
        self,
        text: str,
        segments: Optional[List[Dict[str, str]]] = None,
    ) -> List[NarrativeSeed]:
        """복선 패턴을 탐지합니다."""
        seeds = []
        
        for pattern, seed_type in FORESHADOW_PATTERNS:
            for match in re.finditer(pattern, text):
                # 문맥 추출 (매치 전후 50자)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                # 세그먼트 위치 찾기
                location = self._find_segment(match.start(), text, segments)
                
                seed = NarrativeSeed(
                    id=f"seed_{uuid4().hex[:8]}",
                    description=f"{seed_type}: {match.group()}",
                    planted_at=location,
                    planted_text=context,
                    importance="minor" if seed_type == "motif" else "major",
                )
                seeds.append(seed)
        
        return seeds[:20]  # 상위 20개로 제한
    
    def _detect_payoffs(
        self,
        text: str,
        segments: Optional[List[Dict[str, str]]] = None,
    ) -> List[Payoff]:
        """회수 패턴을 탐지합니다."""
        payoffs = []
        
        for pattern, payoff_type in PAYOFF_PATTERNS:
            for match in re.finditer(pattern, text):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                location = self._find_segment(match.start(), text, segments)
                
                payoff = Payoff(
                    seed_id="",  # 매칭 시 설정
                    resolved_at=location,
                    resolved_text=context,
                    resolution_quality="partial",
                )
                payoffs.append(payoff)
        
        return payoffs
    
    def _find_segment(
        self,
        position: int,
        text: str,
        segments: Optional[List[Dict[str, str]]],
    ) -> str:
        """텍스트 위치에 해당하는 세그먼트를 찾습니다."""
        if segments:
            current_pos = 0
            for i, seg in enumerate(segments):
                seg_len = len(seg.get("content", ""))
                if current_pos + seg_len > position:
                    return seg.get("label", f"세그먼트 {i+1}")
                current_pos += seg_len
        
        # 세그먼트 없으면 대략적인 위치 (1/3 기준)
        relative_pos = position / len(text) if text else 0
        if relative_pos < 0.33:
            return "1막 (도입)"
        elif relative_pos < 0.66:
            return "2막 (전개)"
        else:
            return "3막 (결말)"
    
    def _analyze_matches(
        self,
        seeds: List[NarrativeSeed],
        payoffs: List[Payoff],
        text: str,
    ) -> Tuple[List[Tuple[NarrativeSeed, Payoff]], List[NarrativeSeed], List[Dict]]:
        """복선과 회수를 매칭합니다."""
        matched = []
        orphaned = []
        weak = []
        
        used_payoffs = set()
        
        for seed in seeds:
            # 씨앗의 키워드 추출
            seed_keywords = set(re.findall(r'\w{2,}', seed.planted_text))
            
            best_payoff = None
            best_overlap = 0
            
            for i, payoff in enumerate(payoffs):
                if i in used_payoffs:
                    continue
                    
                payoff_keywords = set(re.findall(r'\w{2,}', payoff.resolved_text))
                overlap = len(seed_keywords & payoff_keywords)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_payoff = (i, payoff)
            
            if best_payoff and best_overlap >= 2:
                idx, payoff = best_payoff
                used_payoffs.add(idx)
                payoff.seed_id = seed.id
                
                # 회수 품질 평가
                if best_overlap >= 4:
                    payoff.resolution_quality = "strong"
                    matched.append((seed, payoff))
                else:
                    payoff.resolution_quality = "weak"
                    matched.append((seed, payoff))
                    weak.append({
                        "seed": seed.model_dump(),
                        "payoff": payoff.model_dump(),
                        "overlap_score": best_overlap,
                    })
            else:
                orphaned.append(seed)
        
        return matched, orphaned, weak
    
    def _generate_suggestions(
        self,
        orphaned: List[NarrativeSeed],
        weak: List[Dict],
    ) -> List[Dict[str, Any]]:
        """미회수 복선에 대한 활용 제안을 생성합니다."""
        suggestions = []
        
        for seed in orphaned:
            suggestion = {
                "id": f"sug_{uuid4().hex[:8]}",
                "type": "opportunity",
                "title": f"미회수 복선: {seed.description[:30]}",
                "message": f"{seed.planted_at}에 심어진 '{seed.planted_text[:50]}...'이 회수되지 않았습니다.",
                "targetNodeId": None,
                "suggestedAction": {
                    "type": "add_payoff",
                    "params": {
                        "seed_id": seed.id,
                        "seed_text": seed.planted_text,
                        "suggested_location": "3막 클라이막스",
                    },
                    "label": "회수 장면 추가",
                },
                "confidence": 0.85 if seed.importance == "major" else 0.6,
                "timestamp": 0,
            }
            suggestions.append(suggestion)
        
        for w in weak[:5]:  # 약한 회수 상위 5개
            suggestion = {
                "id": f"sug_{uuid4().hex[:8]}",
                "type": "improvement",
                "title": "복선 회수 강화 필요",
                "message": f"'{w['seed']['description'][:30]}'의 회수가 약합니다. 더 명확한 연결이 필요합니다.",
                "suggestedAction": {
                    "type": "strengthen_payoff",
                    "params": w,
                    "label": "회수 강화",
                },
                "confidence": 0.7,
                "timestamp": 0,
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_score(
        self,
        total_seeds: int,
        resolved: int,
        weak: int,
    ) -> float:
        """복선 활용 점수를 계산합니다."""
        if total_seeds == 0:
            return 1.0
        
        resolution_rate = resolved / total_seeds
        weak_penalty = (weak / total_seeds) * 0.2 if weak else 0
        
        score = resolution_rate - weak_penalty
        return round(max(0.0, min(1.0, score)), 2)


# Singleton instance
foreshadow_agent = ForeshadowAgent()
