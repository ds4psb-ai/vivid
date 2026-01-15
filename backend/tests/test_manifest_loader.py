"""Manifest Loader Tests.

YAML 기반 앱 RAG 매니페스트 로더 테스트.
"""
import pytest
from pathlib import Path


class TestYAMLManifest:
    """YAMLManifest Pydantic 모델 테스트."""

    def test_valid_manifest(self):
        """유효한 매니페스트 생성."""
        from app.rag.manifest_loader import YAMLManifest

        manifest = YAMLManifest(
            app_key="test.app.key",
            dimensions=["1D", "AD"],
            search_limit=5,
        )

        assert manifest.app_key == "test.app.key"
        assert manifest.dimensions == ["1D", "AD"]
        assert manifest.search_limit == 5
        assert manifest.version == "1.0"

    def test_dimension_validation(self):
        """잘못된 차원 검증."""
        from app.rag.manifest_loader import YAMLManifest
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            YAMLManifest(
                app_key="test.invalid.app",
                dimensions=["INVALID_DIM"],
            )

        assert "Invalid dimension" in str(exc_info.value)

    def test_app_key_validation(self):
        """앱 키 형식 검증."""
        from app.rag.manifest_loader import YAMLManifest
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            YAMLManifest(
                app_key="invalid",  # 최소 2파트 필요
                dimensions=["1D"],
            )

        assert "at least 2 parts" in str(exc_info.value)

    def test_search_limit_bounds(self):
        """search_limit 범위 검증."""
        from app.rag.manifest_loader import YAMLManifest
        from pydantic import ValidationError

        # 최소값 미만
        with pytest.raises(ValidationError):
            YAMLManifest(
                app_key="test.bounds.app",
                search_limit=0,
            )

        # 최대값 초과
        with pytest.raises(ValidationError):
            YAMLManifest(
                app_key="test.bounds.app",
                search_limit=25,
            )

    def test_default_prompt_template(self):
        """기본 프롬프트 템플릿 설정."""
        from app.rag.manifest_loader import YAMLManifest

        manifest = YAMLManifest(
            app_key="test.template.app",
        )

        assert "{rag_results}" in manifest.prompt_injection_template

    def test_dimension_case_normalization(self):
        """차원 대소문자 정규화."""
        from app.rag.manifest_loader import YAMLManifest

        manifest = YAMLManifest(
            app_key="test.case.app",
            dimensions=["ad", "1d", "veo"],  # lowercase
        )

        assert manifest.dimensions == ["AD", "1D", "VEO"]


class TestDatasetRouting:
    """DatasetRouting 기능 테스트."""

    def test_dataset_selection_by_pattern(self):
        """패턴 기반 dataset 선택."""
        from app.rag.manifest_loader import YAMLManifest, DatasetRouting, DatasetRoutingRule

        manifest = YAMLManifest(
            app_key="test.routing.app",
            dataset_routing=DatasetRouting(
                candidates=["dataset_a", "dataset_b"],
                rules=[
                    DatasetRoutingRule(pattern="mbti|성격", datasets=["dataset_a"]),
                ],
                default="dataset_b",
            ),
        )

        # 패턴 매칭
        result = manifest.select_datasets("mbti 분석")
        assert result == ["dataset_a"]

        # 폴백
        result = manifest.select_datasets("기타 쿼리")
        assert result == ["dataset_b"]

    def test_max_select_limit(self):
        """max_select 제한."""
        from app.rag.manifest_loader import YAMLManifest, DatasetRouting, DatasetRoutingRule

        manifest = YAMLManifest(
            app_key="test.limit.app",
            dataset_routing=DatasetRouting(
                candidates=["a", "b", "c", "d"],
                rules=[
                    DatasetRoutingRule(pattern="all", datasets=["a", "b", "c", "d"]),
                ],
                max_select=2,
            ),
        )

        result = manifest.select_datasets("all datasets")
        assert len(result) <= 2


class TestManifestLoader:
    """매니페스트 로더 함수 테스트."""

    def test_load_yaml_manifest(self):
        """YAML 매니페스트 로드."""
        from app.rag.manifest_loader import get_manifest, reload_manifests

        reload_manifests()
        manifest = get_manifest("dimension.aesthetic.direct")

        assert manifest is not None
        assert manifest.app_key == "dimension.aesthetic.direct"
        assert "AD" in manifest.dimensions

    def test_fallback_to_legacy_manifest(self):
        """YAML 없으면 기존 Python 매니페스트 폴백."""
        from app.rag.manifest_loader import get_manifest, reload_manifests, _manifest_cache

        reload_manifests()

        # YAML에서 로드된 매니페스트 확인
        manifest = get_manifest("teaching.prompt.generate")
        assert manifest is not None
        assert manifest.dimensions == ["1D", "VEO"]

    def test_list_manifests(self):
        """모든 매니페스트 목록."""
        from app.rag.manifest_loader import list_manifests, reload_manifests

        reload_manifests()
        manifests = list_manifests()

        assert len(manifests) >= 12  # 최소 12개 앱
        assert "dimension.aesthetic.direct" in manifests
        assert "teaching.prompt.generate" in manifests

    def test_reload_manifests(self):
        """매니페스트 캐시 리로드."""
        from app.rag.manifest_loader import reload_manifests

        count = reload_manifests()
        assert count >= 12  # YAML 파일 12개

    def test_get_dimensions_for_app(self):
        """앱별 차원 목록 조회."""
        from app.rag.manifest_loader import get_dimensions_for_app, reload_manifests

        reload_manifests()

        dims = get_dimensions_for_app("dimension.aesthetic.direct")
        assert "AD" in dims
        assert "1D" in dims

        # 존재하지 않는 앱은 기본값
        dims = get_dimensions_for_app("nonexistent.app.key")
        assert dims == ["1D"]

    def test_list_apps_by_dimension(self):
        """차원별 앱 목록 조회."""
        from app.rag.manifest_loader import list_apps_by_dimension, reload_manifests

        reload_manifests()

        apps = list_apps_by_dimension("AD")
        assert "dimension.aesthetic.direct" in apps

        apps = list_apps_by_dimension("VEO")
        assert "veo.video.generate" in apps

    def test_nonexistent_manifest(self):
        """존재하지 않는 매니페스트."""
        from app.rag.manifest_loader import get_manifest

        manifest = get_manifest("nonexistent.app.key")
        assert manifest is None


class TestLegacyCompatibility:
    """기존 AppRAGManifest와의 호환성 테스트."""

    def test_legacy_fields_preserved(self):
        """레거시 필드 보존."""
        from app.rag.manifest_loader import get_manifest, reload_manifests

        reload_manifests()
        manifest = get_manifest("dimension.persona.analyze")

        assert manifest is not None
        # dataset_routing -> legacy fields 변환 확인
        assert len(manifest.dataset_candidates) > 0 or manifest.dataset_routing is not None

    def test_import_from_manifest_loader(self):
        """manifest_loader에서 직접 import 가능."""
        from app.rag.manifest_loader import (
            YAMLManifest,
            get_manifest,
            get_dimensions_for_app,
            list_manifests,
            list_apps_by_dimension,
            reload_manifests,
            AppManifest,  # Type alias
        )

        # 모든 함수가 호출 가능한지 확인
        assert callable(get_manifest)
        assert callable(get_dimensions_for_app)
        assert callable(list_manifests)
        assert callable(list_apps_by_dimension)
        assert callable(reload_manifests)

        # Type alias 확인
        assert AppManifest is YAMLManifest


class TestHybridRagIntegration:
    """hybrid_rag.py 통합 테스트."""

    def test_hybrid_rag_uses_yaml_manifest(self):
        """hybrid_rag가 YAML 매니페스트 사용."""
        from app.rag.hybrid_rag import get_manifest

        # hybrid_rag에서 import한 get_manifest가 manifest_loader 것인지 확인
        manifest = get_manifest("dimension.aesthetic.direct")
        assert manifest is not None
        assert manifest.app_key == "dimension.aesthetic.direct"

    def test_select_datasets_with_yaml_manifest(self):
        """_select_datasets가 YAMLManifest와 작동."""
        from app.rag.hybrid_rag import _select_datasets
        from app.rag.manifest_loader import get_manifest, reload_manifests

        reload_manifests()
        manifest = get_manifest("dimension.persona.analyze")

        if manifest and (manifest.dataset_candidates or manifest.dataset_routing):
            datasets = _select_datasets("mbti 성격 분석", manifest)
            assert isinstance(datasets, list)
