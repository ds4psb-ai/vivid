"""Vivid App Registry - 범용 앱 레지스트리.

Microkernel Core + Registry Pattern.
Bounded Context 및 Capability 기반 조회 지원.

Usage:
    from app.core.app_registry import AppRegistry
    
    # 초기화 (서버 시작 시)
    AppRegistry.discover("config/apps")
    
    # 조회
    app = AppRegistry.get_by_name("bong")
    apps = AppRegistry.get_by_type(AppType.AUTEUR)
    apps = AppRegistry.get_by_capability("rag")
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import sys

# schema는 이제 backend/app/core/app_schema.py에 위치
from app.core.app_schema import (
    AppConfig,
    AppType,
    BoundedContext,
    validate_config,
)

# CONFIG_DIR is now relative to project root
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config" / "apps"


logger = logging.getLogger(__name__)


class AppRegistry:
    """범용 앱 레지스트리 (Microkernel Core).
    
    Features:
    - YAML 자동 스캔 및 등록
    - 타입, Capability, Bounded Context 기반 조회
    - 키워드 패턴 매칭
    - Hot-reload 지원
    """
    
    _apps: Dict[str, AppConfig] = {}
    _keyword_index: Dict[str, str] = {}  # pattern → app_name
    _initialized: bool = False
    
    @classmethod
    def discover(cls, config_dir: Optional[Path] = None) -> None:
        """YAML 파일 자동 스캔 및 등록.
        
        Args:
            config_dir: 설정 디렉토리 경로 (기본: config/apps)
        """
        if config_dir is None:
            config_dir = CONFIG_DIR
        
        config_dir = Path(config_dir)
        
        if not config_dir.exists():
            logger.warning(f"Config directory not found: {config_dir}")
            return
        
        cls._apps.clear()
        cls._keyword_index.clear()
        
        # 모든 YAML 파일 스캔
        yaml_files = list(config_dir.rglob("*.yaml")) + list(config_dir.rglob("*.yml"))
        
        for yaml_file in yaml_files:
            # schema.py 등 제외
            if yaml_file.stem.startswith("_") or yaml_file.stem == "schema":
                continue
            
            try:
                config = AppConfig.from_yaml(yaml_file)
                
                # 유효성 검증
                errors = validate_config(config)
                if errors:
                    logger.warning(f"Validation errors in {yaml_file}: {errors}")
                    continue
                
                # 등록
                cls._apps[config.metadata.name] = config
                
                # 키워드 인덱스 구축
                for pattern in config.keywords.patterns:
                    cls._keyword_index[pattern.lower()] = config.metadata.name
                
                logger.debug(f"Registered app: {config.metadata.name}")
                
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
        
        cls._initialized = True
        logger.info(f"AppRegistry initialized: {len(cls._apps)} apps registered")
    
    @classmethod
    def _ensure_initialized(cls) -> None:
        """자동 초기화."""
        if not cls._initialized:
            cls.discover()
    
    @classmethod
    def get_by_name(cls, name: str) -> Optional[AppConfig]:
        """이름으로 앱 조회."""
        cls._ensure_initialized()
        return cls._apps.get(name)
    
    @classmethod
    def get_by_type(cls, app_type: AppType) -> List[AppConfig]:
        """앱 타입으로 조회."""
        cls._ensure_initialized()
        return [
            app for app in cls._apps.values()
            if app.metadata.type == app_type
        ]
    
    @classmethod
    def get_by_capability(cls, capability: str) -> List[AppConfig]:
        """특정 Capability가 활성화된 앱 조회."""
        cls._ensure_initialized()
        return [
            app for app in cls._apps.values()
            if app.has_capability(capability)
        ]
    
    @classmethod
    def get_by_context(cls, context: BoundedContext) -> List[AppConfig]:
        """Bounded Context로 앱 조회."""
        cls._ensure_initialized()
        return [
            app for app in cls._apps.values()
            if app.metadata.bounded_context == context
        ]
    
    @classmethod
    def get_by_extension(cls, extension_type: str) -> List[AppConfig]:
        """특정 Extension이 설정된 앱 조회.
        
        Args:
            extension_type: 확장 타입 ("auteur", "dimension", "analytics", 
                           "integration", "utility")
        
        Returns:
            해당 확장이 있는 앱 목록
        """
        cls._ensure_initialized()
        result = []
        for app in cls._apps.values():
            ext = getattr(app.extensions, extension_type, None)
            if ext is not None:
                result.append(app)
        return result
    
    @classmethod
    def get_by_keyword(cls, text: str) -> Optional[AppConfig]:
        """텍스트에서 앱 자동 감지 (키워드 패턴 매칭)."""
        cls._ensure_initialized()
        text_lower = text.lower()
        
        for pattern, app_name in cls._keyword_index.items():
            try:
                if re.search(pattern, text_lower):
                    return cls._apps.get(app_name)
            except re.error:
                # 정규식이 아닌 경우 단순 포함 검사
                if pattern in text_lower:
                    return cls._apps.get(app_name)
        
        return None
    
    @classmethod
    def get_by_capsule_key(cls, capsule_key: str) -> Optional[AppConfig]:
        """Find app by capsule_key in execution capability.
        
        Used for SSoT credit cost lookup.
        
        Args:
            capsule_key: Capsule key (e.g., "teaching.prompt.generate")
            
        Returns:
            AppConfig if found, None otherwise
        """
        cls._ensure_initialized()
        for app in cls._apps.values():
            exec_cap = app.get_capability("execution")
            if exec_cap and exec_cap.config.get("capsule_key") == capsule_key:
                return app
        return None
    
    @classmethod
    def get_all(cls) -> List[AppConfig]:
        """모든 앱 조회."""
        cls._ensure_initialized()
        return list(cls._apps.values())
    
    @classmethod
    def hot_reload(cls) -> None:
        """설정 핫 리로드 (무중단 업데이트)."""
        logger.info("Hot-reloading AppRegistry...")
        cls.discover()
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """레지스트리 통계."""
        cls._ensure_initialized()
        type_counts = {}
        for app in cls._apps.values():
            type_name = app.metadata.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        capability_counts = {}
        for app in cls._apps.values():
            for cap in app.capabilities:
                if cap.enabled:
                    cap_name = cap.name
                    capability_counts[cap_name] = capability_counts.get(cap_name, 0) + 1
        
        return {
            "total_apps": len(cls._apps),
            "by_type": type_counts,
            "by_capability": capability_counts,
            "initialized": cls._initialized,
        }


# Auto-discover on import (optional)
def init_registry():
    """레지스트리 초기화 (서버 시작 시 호출)."""
    if not AppRegistry._initialized:
        AppRegistry.discover()


__all__ = [
    "AppRegistry",
    "init_registry",
]
