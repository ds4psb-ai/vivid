"""Go/No-Go gate validators for NotebookLM loading pipeline.

Implements validation checks from the pilot metrics spec.
"""
from typing import Optional
from datetime import datetime


async def validate_evidence_gate(claims: list[dict]) -> dict:
    """
    Validate that claims meet evidence requirements.
    
    Rule: Each claim must have evidence_refs >= 2
    Pass criteria: 95% of claims must pass
    
    Args:
        claims: List of claim dicts with evidence_refs field
        
    Returns:
        {
            "pass": bool,
            "total_claims": int,
            "claims_with_2_refs": int,
            "claims_with_insufficient_refs": int,
            "pass_rate": float,
            "threshold": float,
            "details": list[dict]  # Failed claims
        }
    """
    if not claims:
        return {
            "pass": True,
            "total_claims": 0,
            "claims_with_2_refs": 0,
            "claims_with_insufficient_refs": 0,
            "pass_rate": 1.0,
            "threshold": 0.95,
            "details": [],
        }
    
    claims_with_2_refs = 0
    failed_claims = []
    
    for claim in claims:
        refs = claim.get("evidence_refs", [])
        if len(refs) >= 2:
            claims_with_2_refs += 1
        else:
            failed_claims.append({
                "claim_id": claim.get("claim_id", "unknown"),
                "statement": claim.get("statement", "")[:100],
                "evidence_count": len(refs),
            })
    
    pass_rate = claims_with_2_refs / len(claims)
    
    return {
        "pass": pass_rate >= 0.95,
        "total_claims": len(claims),
        "claims_with_2_refs": claims_with_2_refs,
        "claims_with_insufficient_refs": len(failed_claims),
        "pass_rate": round(pass_rate, 4),
        "threshold": 0.95,
        "details": failed_claims[:10],  # Limit to 10 for readability
    }


async def validate_template_seed(template: dict) -> dict:
    """
    Validate that a template has all required components.
    
    Required: story, beat_sheet, storyboard
    Pass criteria: All three must exist and be non-empty
    
    Args:
        template: Template dict with story, beat_sheet, storyboard fields
        
    Returns:
        {
            "pass": bool,
            "has_story": bool,
            "has_beat": bool,
            "has_storyboard": bool,
            "missing": list[str]
        }
    """
    has_story = bool(template.get("story"))
    has_beat = bool(template.get("beat_sheet") or template.get("story_beats"))
    has_storyboard = bool(template.get("storyboard") or template.get("storyboard_cards"))
    
    missing = []
    if not has_story:
        missing.append("story")
    if not has_beat:
        missing.append("beat_sheet")
    if not has_storyboard:
        missing.append("storyboard")
    
    return {
        "pass": has_story and has_beat and has_storyboard,
        "has_story": has_story,
        "has_beat": has_beat,
        "has_storyboard": has_storyboard,
        "missing": missing,
    }


async def validate_batch_templates(templates: list[dict]) -> dict:
    """
    Validate a batch of templates for seed completeness.
    
    Pass criteria: 90% of templates must have all components
    
    Args:
        templates: List of template dicts
        
    Returns:
        {
            "pass": bool,
            "total": int,
            "valid": int,
            "invalid": int,
            "pass_rate": float,
            "threshold": float,
            "invalid_templates": list[dict]
        }
    """
    if not templates:
        return {
            "pass": True,
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "pass_rate": 1.0,
            "threshold": 0.90,
            "invalid_templates": [],
        }
    
    valid_count = 0
    invalid_templates = []
    
    for template in templates:
        result = await validate_template_seed(template)
        if result["pass"]:
            valid_count += 1
        else:
            invalid_templates.append({
                "template_id": template.get("id", template.get("slug", "unknown")),
                "missing": result["missing"],
            })
    
    pass_rate = valid_count / len(templates)
    
    return {
        "pass": pass_rate >= 0.90,
        "total": len(templates),
        "valid": valid_count,
        "invalid": len(invalid_templates),
        "pass_rate": round(pass_rate, 4),
        "threshold": 0.90,
        "invalid_templates": invalid_templates[:10],
    }


async def calculate_pilot_go_nogo(
    evidence_gate_result: dict,
    template_seed_result: dict,
    template_run_success_rate: float,
    evidence_click_rate: Optional[float],
) -> dict:
    """
    Calculate overall Go/No-Go decision for pilot.
    
    Criteria:
    - Evidence Gate pass rate >= 95%
    - Template seed success rate >= 90%
    - Template run success rate >= 98%
    - Evidence click rate >= 15% (target, not blocker)
    
    Returns:
        {
            "decision": "GO" | "NO_GO" | "CONDITIONAL",
            "blockers": list[str],
            "warnings": list[str],
            "summary": dict
        }
    """
    blockers = []
    warnings = []
    
    # Check evidence gate (BLOCKER if fail)
    if not evidence_gate_result.get("pass", False):
        blockers.append(
            f"Evidence Gate: {evidence_gate_result.get('pass_rate', 0)*100:.1f}% < 95%"
        )
    
    # Check template seed (BLOCKER if fail)
    if not template_seed_result.get("pass", False):
        blockers.append(
            f"Template Seed: {template_seed_result.get('pass_rate', 0)*100:.1f}% < 90%"
        )
    
    # Check template run success (BLOCKER if fail)
    if template_run_success_rate < 0.98:
        blockers.append(
            f"Template Run: {template_run_success_rate*100:.1f}% < 98%"
        )
    
    # Check evidence click rate (WARNING, not blocker)
    if evidence_click_rate is not None and evidence_click_rate < 0.15:
        warnings.append(
            f"Evidence Click Rate: {evidence_click_rate*100:.1f}% < 15% target"
        )
    
    # Determine decision
    if blockers:
        decision = "NO_GO"
    elif warnings:
        decision = "CONDITIONAL"
    else:
        decision = "GO"
    
    return {
        "decision": decision,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "evidence_gate_pass_rate": evidence_gate_result.get("pass_rate"),
            "template_seed_pass_rate": template_seed_result.get("pass_rate"),
            "template_run_success_rate": template_run_success_rate,
            "evidence_click_rate": evidence_click_rate,
        },
        "evaluated_at": datetime.utcnow().isoformat(),
    }
