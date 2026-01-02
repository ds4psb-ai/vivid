"""STPF v3.1 Engine - Safe Math Implementation."""
from __future__ import annotations

import logging
import math
from copy import deepcopy
from typing import Any, Dict, List, Optional

from app.schemas.stpf_schemas import (
    KellyResult,
    MultipliersResult,
    ScenarioResult,
    SensitivityResult,
    STPFInputs,
    STPFResult,
)

logger = logging.getLogger(__name__)


def _clamp_1_10(x: float) -> float:
    """Clamp value to 1~10 range."""
    return max(1.0, min(10.0, float(x)))


def _norm01(x: float) -> float:
    """Normalize 1~10 to 0~1."""
    return (_clamp_1_10(x) - 1.0) / 9.0


def _sigmoid(z: float) -> float:
    """Numerically stable sigmoid."""
    z = float(z)
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


class STPFv31Engine:
    """
    STPF v3.1 Safe Math Engine
    
    Safe Math Fixes:
    - Division-by-zero 방지: 분모는 (1 + w*norm01(x))로 구성 (최소 1)
    - Vanishing gradient 방지: 분자는 1~10 Raw를 사용 (0~1 소수 거듭제곱 금지)
    - Score 스케일 안정화: log10(RawScore) 위에서 sigmoid로 0~1000 매핑
    """
    
    # Configuration
    LOG_MID = 4.0
    SCORE_K = 1.2
    FRICTION_EXP = 0.8
    
    def compute(self, inputs: STPFInputs) -> STPFResult:
        """
        STPF v3.1 메인 계산
        
        Args:
            inputs: STPF 입력 변수
            
        Returns:
            STPFResult with score, probability, and components
        """
        x = self._to_dict(inputs)
        
        # 1. Gate Kill Switch
        gates = [x["trust"], x["legality"], x["hygiene"]]
        gate_min = min(gates)
        
        if gate_min < 4.0:
            logger.warning(f"STPF Gate failed: min={gate_min}")
            return STPFResult(
                status="GATE_FAIL",
                raw_score=0.0,
                score_1000=0.0,
                p_success=0.0,
                gate_factor=0.0,
                gate_min=gate_min,
                v=0.0,
                f_total=0.0,
                f_eff=0.0,
                grade="Gate Failed"
            )
        
        # Soft gate factor (0~1)
        gate_factor = (x["trust"] / 10.0) * (x["legality"] / 10.0) * (x["hygiene"] / 10.0)
        
        # 2. Numerator (Raw 1~10, Essence²)
        V = (
            (x["essence"] ** 2.0) *
            (x["capability"] ** 1.2) *
            (x["novelty"] ** 1.1) *
            (x["connection"] ** 1.0) *
            (x["proof"] ** 1.3)
        )
        
        # 3. Denominator (Safe: 1 + w*norm01)
        F_list = [
            (1.0 + 1.0 * _norm01(x["cost"])),
            (1.0 + 1.2 * _norm01(x["risk"])),
            (1.0 + 1.0 * _norm01(x["threat"])),
            (1.0 + 1.0 * _norm01(x["pressure"])),
            (1.0 + 0.9 * _norm01(x["lag"])),
            (1.0 + 1.1 * _norm01(x["uncertainty"])),
        ]
        F_total = 1.0
        for f in F_list:
            F_total *= f
        F_eff = F_total ** self.FRICTION_EXP
        
        # 4. Multipliers
        S_boost = 1.0 + 0.6 * _norm01(x["scarcity"])
        LV_boost = 1.0 + 0.5 * _norm01(x["leverage"])
        
        # Network: threshold 이후 지수형
        nw = x["network"]
        if nw <= 5.0:
            NW_boost = 1.0
        else:
            NW_boost = 1.0 + 0.25 * (2.0 ** ((nw - 5.0) / 2.0) - 1.0)
        
        # 5. Entropy / Gap
        gap = max(0.0, x["reality"] - x["expectation"])
        Entropy_boost = 1.0 + 0.5 * math.log1p(gap)
        
        # 6. Base Raw Score
        raw = gate_factor * (V / F_eff) * S_boost * LV_boost * NW_boost * Entropy_boost
        
        # 7. Patches
        # Trust soft crash
        if x["trust"] < 6.0:
            raw *= 0.2
        
        # Capital patch (optional)
        capital = x.get("capital")
        if capital and capital > 0 and x["essence"] <= 3.0:
            raw *= (1.0 + 0.15 * math.log10(1.0 + capital))
        
        # Confidence paradox (optional)
        confidence = x.get("confidence")
        if confidence and x["proof"] < 5.0 and confidence >= 7.0:
            raw *= (1.0 - 0.30 * _norm01(confidence))
            raw = max(raw, 0.0)
        
        # 8. Score_1000 (log-scale sigmoid)
        if raw <= 0.0:
            score_1000 = 0.0
        else:
            log_raw = math.log10(raw)
            score_1000 = 1000.0 * _sigmoid(self.SCORE_K * (log_raw - self.LOG_MID))
        
        # 9. Probability (logistic model)
        z = -2.197224577  # logit(0.1)
        z += 0.25 * (x["trust"] - 5.0)
        z += 0.30 * (x["proof"] - 5.0)
        z += 0.15 * (x["essence"] - 5.0)
        z += 0.10 * (x["network"] - 5.0)
        z -= 0.25 * (x["risk"] - 5.0)
        z -= 0.15 * (x["uncertainty"] - 5.0)
        z -= 0.10 * (x["cost"] - 5.0)
        p_success = _sigmoid(z)
        
        # 10. Kelly (optional)
        kelly = self._calculate_kelly(p_success, x.get("upside"), x.get("downside"))
        
        return STPFResult(
            status="OK",
            raw_score=raw,
            score_1000=score_1000,
            p_success=p_success,
            gate_factor=gate_factor,
            v=V,
            f_total=F_total,
            f_eff=F_eff,
            multipliers=MultipliersResult(
                s_boost=S_boost,
                lv_boost=LV_boost,
                nw_boost=NW_boost,
                entropy_boost=Entropy_boost,
                gap=gap
            ),
            kelly=kelly
        )
    
    def sensitivity(self, inputs: STPFInputs) -> SensitivityResult:
        """
        민감도 분석: Leverage Point & Fatal Friction 식별
        """
        base = self.compute(inputs)
        if base.status != "OK":
            return SensitivityResult(
                status="NOT_OK",
                base_score=0.0,
                leverage_point={"var": "none", "delta": 0.0},
                fatal_friction={"var": "none", "delta": 0.0}
            )
        
        base_score = base.score_1000
        x = self._to_dict(inputs)
        
        # Variables to test
        up_vars = ["essence", "capability", "novelty", "connection", "proof",
                   "network", "scarcity", "leverage", "reality",
                   "trust", "legality", "hygiene"]
        down_vars = ["cost", "risk", "threat", "pressure", "lag", "uncertainty"]
        
        deltas_up = {}
        for var in up_vars:
            y = deepcopy(x)
            y[var] = _clamp_1_10(y[var] + 1.0)
            test_inputs = self._from_dict(y)
            result = self.compute(test_inputs)
            if result.status == "OK":
                deltas_up[var] = result.score_1000 - base_score
            else:
                deltas_up[var] = -1e9
        
        deltas_down = {}
        for var in down_vars:
            y = deepcopy(x)
            y[var] = _clamp_1_10(y[var] - 1.0)
            test_inputs = self._from_dict(y)
            result = self.compute(test_inputs)
            if result.status == "OK":
                deltas_down[var] = result.score_1000 - base_score
            else:
                deltas_down[var] = -1e9
        
        leverage_var = max(deltas_up, key=deltas_up.get)
        friction_var = max(deltas_down, key=deltas_down.get)
        
        return SensitivityResult(
            status="OK",
            base_score=base_score,
            leverage_point={"var": leverage_var, "delta": deltas_up[leverage_var]},
            fatal_friction={"var": friction_var, "delta": deltas_down[friction_var]},
            deltas_up=deltas_up,
            deltas_down=deltas_down
        )
    
    def scenarios(self, inputs: STPFInputs) -> ScenarioResult:
        """
        Worst / Base / Best 3분기 시나리오 시뮬레이션
        """
        x = self._to_dict(inputs)
        
        def adjust(inp: dict, n: float = 0, d: float = 0, m: float = 0, 
                   g: float = 0, gap: float = 0) -> dict:
            y = deepcopy(inp)
            # Gates
            for k in ["trust", "legality", "hygiene"]:
                y[k] = _clamp_1_10(y[k] + g)
            # Numerator
            for k in ["essence", "capability", "novelty", "connection", "proof"]:
                y[k] = _clamp_1_10(y[k] + n)
            # Denominator
            for k in ["cost", "risk", "threat", "pressure", "lag", "uncertainty"]:
                y[k] = _clamp_1_10(y[k] + d)
            # Multipliers
            for k in ["network", "scarcity", "leverage"]:
                y[k] = _clamp_1_10(y[k] + m)
            # Gap
            y["reality"] = _clamp_1_10(y["reality"] + gap)
            return y
        
        worst = self.compute(self._from_dict(adjust(x, n=-2, d=+2, m=-2, g=-2, gap=-1)))
        base = self.compute(inputs)
        best = self.compute(self._from_dict(adjust(x, n=+2, d=-2, m=+2, g=+1, gap=+1)))
        
        # Weighted recommendation
        final_score = 0.3 * worst.score_1000 + 0.4 * base.score_1000 + 0.3 * best.score_1000
        
        return ScenarioResult(
            worst=worst,
            base=base,
            best=best,
            final_recommendation_score=final_score
        )
    
    def _calculate_kelly(
        self, 
        p_success: float,
        upside: Optional[float],
        downside: Optional[float]
    ) -> KellyResult:
        """Kelly Criterion 계산"""
        if not upside or not downside or downside <= 0:
            return KellyResult()
        
        b = upside / downside
        f = (b * p_success - (1.0 - p_success)) / b
        f = max(0.0, min(1.0, f))
        
        return KellyResult(
            b=b,
            f=f,
            f_safe=0.5 * f  # Fractional Kelly
        )
    
    def _to_dict(self, inputs: STPFInputs) -> dict:
        """Convert STPFInputs to dict"""
        return {
            "trust": inputs.trust,
            "legality": inputs.legality,
            "hygiene": inputs.hygiene,
            "essence": inputs.essence,
            "capability": inputs.capability,
            "novelty": inputs.novelty,
            "connection": inputs.connection,
            "proof": inputs.proof,
            "cost": inputs.cost,
            "risk": inputs.risk,
            "threat": inputs.threat,
            "pressure": inputs.pressure,
            "lag": inputs.lag,
            "uncertainty": inputs.uncertainty,
            "network": inputs.network,
            "scarcity": inputs.scarcity,
            "leverage": inputs.leverage,
            "expectation": inputs.expectation,
            "reality": inputs.reality,
            "upside": inputs.upside,
            "downside": inputs.downside,
            "capital": inputs.capital,
            "confidence": inputs.confidence,
        }
    
    def _from_dict(self, d: dict) -> STPFInputs:
        """Convert dict to STPFInputs"""
        return STPFInputs(
            Trust=d["trust"],
            Legality=d["legality"],
            Hygiene=d["hygiene"],
            E=d["essence"],
            K=d["capability"],
            Nv=d["novelty"],
            Cn=d["connection"],
            Prf=d["proof"],
            Cost=d["cost"],
            Risk=d["risk"],
            Threat=d["threat"],
            Pressure=d["pressure"],
            Lag=d["lag"],
            Uncertainty=d["uncertainty"],
            Network=d["network"],
            Scarcity=d["scarcity"],
            Leverage=d["leverage"],
            Expectation=d["expectation"],
            Reality=d["reality"],
            Upside=d.get("upside"),
            Downside=d.get("downside"),
            Capital=d.get("capital"),
            Confidence=d.get("confidence"),
        )


# Singleton instance
stpf_engine = STPFv31Engine()
