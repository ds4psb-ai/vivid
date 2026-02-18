"""Tests for rights graph core models.

TDD RED phase:
- Ensure rights graph schema enforces license metadata
- Ensure provenance events have required references
"""

import uuid


def test_rights_asset_requires_license_type():
    from app.models_rights_graph import RightsAsset

    assert RightsAsset.__table__.c.license_type.nullable is False


def test_rights_asset_derivative_allowed_default_true():
    from app.models_rights_graph import RightsAsset

    model = RightsAsset(
        asset_id="asset-1",
        source_type="script",
        license_type="cc-by",
        allowed_actions=["reference"],
        source_license="CC-BY-4.0",
    )

    assert model.derivative_allowed is True


def test_provenance_event_requires_asset_reference():
    from app.models_rights_graph import ProvenanceEvent

    assert ProvenanceEvent.__table__.c.rights_asset_id.nullable is False
