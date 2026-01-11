"""Capsule Spec SSoT Service.

P5 Commit 1: Single source of truth for capsule specifications.

Priority: DB CapsuleSpec → fixtures (dimension_capsules, auteur_capsules)
Synthetic ID: fixtures use `id = capsule_key:version` when loaded

Usage:
    from app.services.capsule_specs import (
        list_specs, get_spec, resolve_latest_version, parse_capsule_id
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CapsuleSpec as CapsuleSpecModel

logger = logging.getLogger(__name__)


# =============================================================================
# Response Schema (frontend-compatible)
# =============================================================================

@dataclass
class CapsuleSpecResponse:
    """CapsuleSpec response matching frontend expectations."""
    id: str  # Synthetic ID: capsule_key:version
    capsule_key: str
    version: str
    display_name: str
    description: str
    spec: Dict[str, Any]
    is_active: bool
    category: Optional[str] = None  # auteur | teaching | dimension | generation
    credit_costs: Optional[Dict[str, int]] = None
    stage: Optional[str] = None
    route_key: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "capsule_key": self.capsule_key,
            "version": self.version,
            "display_name": self.display_name,
            "description": self.description,
            "spec": self.spec,
            "is_active": self.is_active,
            "category": self.category,
            "credit_costs": self.credit_costs,
            "stage": self.stage,
            "route_key": self.route_key,
        }


# =============================================================================
# Fixtures Loader
# =============================================================================

_fixtures_cache: Optional[Dict[str, CapsuleSpecResponse]] = None


def _load_fixtures() -> Dict[str, CapsuleSpecResponse]:
    """Load fixtures from dimension_capsules.py and auteur_capsules.py.
    
    Returns:
        Dict mapping capsule_key:version to CapsuleSpecResponse
    """
    global _fixtures_cache
    if _fixtures_cache is not None:
        return _fixtures_cache
    
    fixtures: Dict[str, CapsuleSpecResponse] = {}
    
    # Load dimension capsules
    try:
        from app.fixtures.dimension_capsules import DIMENSION_CAPSULES
        for item in DIMENSION_CAPSULES:
            key = item.get("capsule_key", "")
            version = item.get("version", "1.0.0")
            synthetic_id = f"{key}:{version}"
            
            fixtures[synthetic_id] = CapsuleSpecResponse(
                id=synthetic_id,
                capsule_key=key,
                version=version,
                display_name=item.get("display_name", key),
                description=item.get("spec", {}).get("description", ""),
                spec=item.get("spec", {}),
                is_active=True,
                category=item.get("spec", {}).get("category", "dimension"),
                credit_costs=item.get("credit_costs"),
                stage=item.get("stage"),
                route_key=item.get("route_key"),
            )
    except ImportError as e:
        logger.warning(f"Failed to load dimension_capsules: {e}")
    
    # Load auteur capsules
    try:
        from app.fixtures.auteur_capsules import CAPSULE_SPECS
        for item in CAPSULE_SPECS:
            key = item.get("capsule_key", "")
            version = item.get("version", "1.0.0")
            synthetic_id = f"{key}:{version}"
            
            fixtures[synthetic_id] = CapsuleSpecResponse(
                id=synthetic_id,
                capsule_key=key,
                version=version,
                display_name=item.get("display_name", key),
                description=item.get("description", ""),
                spec=item.get("spec", {}),
                is_active=True,
                category="auteur" if key.startswith("auteur.") else "production",
                credit_costs=item.get("credit_costs"),
                stage=item.get("stage"),
                route_key=item.get("route_key"),
            )
    except ImportError as e:
        logger.warning(f"Failed to load auteur_capsules: {e}")
    
    _fixtures_cache = fixtures
    logger.info(f"Loaded {len(fixtures)} capsule specs from fixtures")
    return fixtures


def clear_fixtures_cache() -> None:
    """Clear fixtures cache (for testing)."""
    global _fixtures_cache
    _fixtures_cache = None


# =============================================================================
# ID Parsing
# =============================================================================

def parse_capsule_id(capsule_id: str) -> Tuple[str, Optional[str]]:
    """Parse capsule_id into (capsule_key, version).
    
    Args:
        capsule_id: Format "capsule_key" or "capsule_key:version"
    
    Returns:
        Tuple of (capsule_key, version or None)
    
    Examples:
        >>> parse_capsule_id("teaching.prompt.generate:1.0.0")
        ("teaching.prompt.generate", "1.0.0")
        >>> parse_capsule_id("auteur.bong-joon-ho")
        ("auteur.bong-joon-ho", None)
    """
    if ":" in capsule_id:
        parts = capsule_id.split(":", 1)
        return parts[0], parts[1]
    return capsule_id, None


# =============================================================================
# Core Functions
# =============================================================================

async def list_specs(
    db: AsyncSession,
    category: Optional[str] = None,
    active_only: bool = True,
) -> List[CapsuleSpecResponse]:
    """List all capsule specs, merging DB and fixtures.
    
    Args:
        db: Database session
        category: Filter by category (auteur, teaching, dimension, generation)
        active_only: Only return active specs
    
    Returns:
        List of CapsuleSpecResponse
    """
    result_map: Dict[str, CapsuleSpecResponse] = {}
    
    # Step 1: Load fixtures (lower priority)
    fixtures = _load_fixtures()
    for key, spec in fixtures.items():
        if active_only and not spec.is_active:
            continue
        if category and spec.category != category:
            continue
        result_map[key] = spec
    
    # Step 2: Load DB specs (higher priority - overwrites fixtures)
    try:
        query = select(CapsuleSpecModel)
        if active_only:
            query = query.where(CapsuleSpecModel.is_active == True)
        
        db_result = await db.execute(query)
        db_specs = db_result.scalars().all()
        
        for db_spec in db_specs:
            synthetic_id = f"{db_spec.capsule_key}:{db_spec.version}"
            spec_category = db_spec.spec.get("category") if db_spec.spec else None
            
            if category and spec_category != category:
                continue
            
            result_map[synthetic_id] = CapsuleSpecResponse(
                id=synthetic_id,
                capsule_key=db_spec.capsule_key,
                version=db_spec.version,
                display_name=db_spec.display_name,
                description=db_spec.description,
                spec=db_spec.spec or {},
                is_active=db_spec.is_active,
                category=spec_category,
                credit_costs=db_spec.spec.get("credit_costs") if db_spec.spec else None,
                stage=db_spec.spec.get("stage") if db_spec.spec else None,
                route_key=db_spec.spec.get("route_key") if db_spec.spec else None,
            )
    except Exception as e:
        logger.warning(f"Failed to query DB specs: {e}")
    
    return list(result_map.values())


async def get_spec(
    db: AsyncSession,
    capsule_key: str,
    version: Optional[str] = None,
) -> Optional[CapsuleSpecResponse]:
    """Get a specific capsule spec by key and version.
    
    Args:
        db: Database session
        capsule_key: Capsule key (e.g., "teaching.prompt.generate")
        version: Optional version (defaults to latest)
    
    Returns:
        CapsuleSpecResponse or None if not found
    """
    # Resolve version if not provided
    if version is None:
        version = await resolve_latest_version(db, capsule_key)
        if version is None:
            return None
    
    synthetic_id = f"{capsule_key}:{version}"
    
    # Step 1: Try DB first (higher priority)
    try:
        query = select(CapsuleSpecModel).where(
            CapsuleSpecModel.capsule_key == capsule_key,
            CapsuleSpecModel.version == version,
        )
        result = await db.execute(query)
        db_spec = result.scalar_one_or_none()
        
        if db_spec:
            spec_category = db_spec.spec.get("category") if db_spec.spec else None
            return CapsuleSpecResponse(
                id=synthetic_id,
                capsule_key=db_spec.capsule_key,
                version=db_spec.version,
                display_name=db_spec.display_name,
                description=db_spec.description,
                spec=db_spec.spec or {},
                is_active=db_spec.is_active,
                category=spec_category,
                credit_costs=db_spec.spec.get("credit_costs") if db_spec.spec else None,
                stage=db_spec.spec.get("stage") if db_spec.spec else None,
                route_key=db_spec.spec.get("route_key") if db_spec.spec else None,
            )
    except Exception as e:
        logger.warning(f"Failed to query DB spec: {e}")
    
    # Step 2: Fallback to fixtures
    fixtures = _load_fixtures()
    return fixtures.get(synthetic_id)


async def resolve_latest_version(
    db: AsyncSession,
    capsule_key: str,
) -> Optional[str]:
    """Resolve the latest version for a capsule key.
    
    Args:
        db: Database session
        capsule_key: Capsule key
    
    Returns:
        Latest version string or None if not found
    """
    versions: List[str] = []
    
    # Check DB
    try:
        query = select(CapsuleSpecModel.version).where(
            CapsuleSpecModel.capsule_key == capsule_key,
            CapsuleSpecModel.is_active == True,
        )
        result = await db.execute(query)
        db_versions = result.scalars().all()
        versions.extend(db_versions)
    except Exception as e:
        logger.warning(f"Failed to query DB versions: {e}")
    
    # Check fixtures
    fixtures = _load_fixtures()
    for key in fixtures:
        if key.startswith(f"{capsule_key}:"):
            version = key.split(":", 1)[1]
            if version not in versions:
                versions.append(version)
    
    if not versions:
        return None
    
    # Sort by semver (simplified: string sort works for standard versions)
    versions.sort(key=_semver_key, reverse=True)
    return versions[0]


def _semver_key(version: str) -> Tuple[int, int, int]:
    """Convert version string to sortable tuple."""
    try:
        parts = version.split(".")
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0,
        )
    except (ValueError, IndexError):
        return (0, 0, 0)


async def get_spec_by_id(
    db: AsyncSession,
    capsule_id: str,
) -> Optional[CapsuleSpecResponse]:
    """Get spec by capsule_id (convenience wrapper).
    
    Args:
        db: Database session
        capsule_id: Format "capsule_key" or "capsule_key:version"
    
    Returns:
        CapsuleSpecResponse or None
    """
    capsule_key, version = parse_capsule_id(capsule_id)
    return await get_spec(db, capsule_key, version)
