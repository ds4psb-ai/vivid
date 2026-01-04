"""
App Registry Service

앱 등록, 조회, 버전 관리, 배포 상태 추적
"""
from __future__ import annotations

import json
import hashlib
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field, asdict
from pathlib import Path
import os

from app.config import settings


class AppStatus(str, Enum):
    """앱 상태"""
    PENDING = "pending"           # 검증 대기
    BUILDING = "building"         # 빌드 중
    REVIEWING = "reviewing"       # 리뷰 대기
    ACTIVE = "active"             # 활성화됨
    INACTIVE = "inactive"         # 비활성화됨
    REJECTED = "rejected"         # 거부됨
    FAILED = "failed"             # 빌드 실패


@dataclass
class DimensionTheme:
    """차원 테마 설정"""
    theme: str = "default"
    primary_color: str = "#84cc16"
    accent_color: str = "#22c55e"
    border_style: str = "solid"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "theme": self.theme,
            "primaryColor": self.primary_color,
            "accentColor": self.accent_color,
            "borderStyle": self.border_style,
        }


@dataclass
class AppCredits:
    """크레딧 설정"""
    per_run: int = 0
    per_save: int = 0
    per_minute: int = 0


@dataclass
class AppManifest:
    """앱 매니페스트 (crebit.json 파싱 결과)"""
    name: str
    version: str
    entry: str
    description: str = ""
    author: str = ""
    dimension: Optional[DimensionTheme] = None
    permissions: List[str] = field(default_factory=list)
    credits: Optional[AppCredits] = None
    icon: str = ""
    tags: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppManifest":
        """딕셔너리에서 생성"""
        dimension = None
        if data.get("dimension"):
            d = data["dimension"]
            dimension = DimensionTheme(
                theme=d.get("theme", "default"),
                primary_color=d.get("primaryColor", "#84cc16"),
                accent_color=d.get("accentColor", "#22c55e"),
                border_style=d.get("borderStyle", "solid"),
            )
        
        credits = None
        if data.get("credits"):
            c = data["credits"]
            credits = AppCredits(
                per_run=c.get("perRun", 0),
                per_save=c.get("perSave", 0),
                per_minute=c.get("perMinute", 0),
            )
        
        return cls(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            entry=data.get("entry", "index.html"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            dimension=dimension,
            permissions=data.get("permissions", []),
            credits=credits,
            icon=data.get("icon", ""),
            tags=data.get("tags", []),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "name": self.name,
            "version": self.version,
            "entry": self.entry,
            "description": self.description,
            "author": self.author,
            "permissions": self.permissions,
            "icon": self.icon,
            "tags": self.tags,
        }
        if self.dimension:
            result["dimension"] = self.dimension.to_dict()
        if self.credits:
            result["credits"] = {
                "perRun": self.credits.per_run,
                "perSave": self.credits.per_save,
                "perMinute": self.credits.per_minute,
            }
        return result


@dataclass
class AppVersion:
    """앱 버전 정보"""
    version: str
    build_hash: str
    created_at: str
    status: AppStatus
    source_hash: str = ""
    notes: str = ""


@dataclass
class RegisteredApp:
    """등록된 앱"""
    app_id: str
    manifest: AppManifest
    status: AppStatus
    current_version: str
    versions: List[AppVersion]
    created_at: str
    updated_at: str
    created_by: str
    sandbox_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "appId": self.app_id,
            "manifest": self.manifest.to_dict(),
            "status": self.status.value,
            "currentVersion": self.current_version,
            "versions": [
                {
                    "version": v.version,
                    "buildHash": v.build_hash,
                    "createdAt": v.created_at,
                    "status": v.status.value,
                    "notes": v.notes,
                }
                for v in self.versions
            ],
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "createdBy": self.created_by,
            "sandboxUrl": self.sandbox_url,
        }


class AppRegistryService:
    """앱 레지스트리 서비스"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.path.join(
            settings.DATA_DIR if hasattr(settings, 'DATA_DIR') else "/tmp",
            "app_registry"
        ))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._apps: Dict[str, RegisteredApp] = {}
        self._load_registry()
    
    def _registry_file(self) -> Path:
        return self.storage_path / "registry.json"
    
    def _apps_dir(self) -> Path:
        return self.storage_path / "apps"
    
    def _load_registry(self) -> None:
        """레지스트리 로드"""
        registry_file = self._registry_file()
        if registry_file.exists():
            try:
                with open(registry_file, "r") as f:
                    data = json.load(f)
                    for app_id, app_data in data.get("apps", {}).items():
                        self._apps[app_id] = self._deserialize_app(app_data)
            except Exception:
                self._apps = {}
    
    def _save_registry(self) -> None:
        """레지스트리 저장"""
        registry_file = self._registry_file()
        data = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "apps": {
                app_id: self._serialize_app(app)
                for app_id, app in self._apps.items()
            }
        }
        with open(registry_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _serialize_app(self, app: RegisteredApp) -> Dict[str, Any]:
        """앱 직렬화"""
        return app.to_dict()
    
    def _deserialize_app(self, data: Dict[str, Any]) -> RegisteredApp:
        """앱 역직렬화"""
        manifest = AppManifest.from_dict(data.get("manifest", {}))
        versions = [
            AppVersion(
                version=v["version"],
                build_hash=v["buildHash"],
                created_at=v["createdAt"],
                status=AppStatus(v["status"]),
                notes=v.get("notes", ""),
            )
            for v in data.get("versions", [])
        ]
        return RegisteredApp(
            app_id=data["appId"],
            manifest=manifest,
            status=AppStatus(data["status"]),
            current_version=data["currentVersion"],
            versions=versions,
            created_at=data["createdAt"],
            updated_at=data["updatedAt"],
            created_by=data.get("createdBy", "unknown"),
            sandbox_url=data.get("sandboxUrl", ""),
        )
    
    def generate_app_id(self, manifest: AppManifest) -> str:
        """앱 ID 생성"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        name_hash = hashlib.md5(manifest.name.encode()).hexdigest()[:6]
        return f"app_{timestamp}_{name_hash}"
    
    def generate_build_hash(self, source: bytes) -> str:
        """빌드 해시 생성"""
        return hashlib.sha256(source).hexdigest()[:16]
    
    def validate_manifest(self, manifest_data: Dict[str, Any]) -> tuple[bool, List[str], List[str]]:
        """매니페스트 검증"""
        errors: List[str] = []
        warnings: List[str] = []
        
        # Required fields
        if not manifest_data.get("name"):
            errors.append("name 필드가 필요합니다")
        elif len(manifest_data["name"]) > 100:
            errors.append("name은 100자 이하여야 합니다")
        
        if not manifest_data.get("version"):
            errors.append("version 필드가 필요합니다")
        elif not self._is_valid_semver(manifest_data["version"]):
            errors.append("version은 semver 형식이어야 합니다 (예: 1.0.0)")
        
        if not manifest_data.get("entry"):
            errors.append("entry 필드가 필요합니다")
        
        # Color validation
        if manifest_data.get("dimension"):
            dim = manifest_data["dimension"]
            for color_key in ["primaryColor", "accentColor"]:
                if dim.get(color_key):
                    if not self._is_valid_hex_color(dim[color_key]):
                        errors.append(f"{color_key}는 #RRGGBB 형식이어야 합니다")
        
        # Warnings
        if not manifest_data.get("description"):
            warnings.append("description 추가를 권장합니다")
        
        if not manifest_data.get("dimension"):
            warnings.append("dimension이 없으면 기본 테마가 적용됩니다")
        
        return len(errors) == 0, errors, warnings
    
    def _is_valid_semver(self, version: str) -> bool:
        import re
        return bool(re.match(r'^\d+\.\d+\.\d+$', version))
    
    def _is_valid_hex_color(self, color: str) -> bool:
        import re
        return bool(re.match(r'^#[0-9a-fA-F]{6}$', color))
    
    async def register_app(
        self,
        manifest_data: Dict[str, Any],
        source_content: bytes,
        user_id: str,
    ) -> tuple[bool, Optional[RegisteredApp], Optional[str]]:
        """앱 등록"""
        # 1. Validate manifest
        valid, errors, _ = self.validate_manifest(manifest_data)
        if not valid:
            return False, None, "; ".join(errors)
        
        # 2. Create manifest
        manifest = AppManifest.from_dict(manifest_data)
        
        # 3. Generate IDs
        app_id = self.generate_app_id(manifest)
        build_hash = self.generate_build_hash(source_content)
        now = datetime.now(timezone.utc).isoformat()
        
        # 4. Save source (in production: run build pipeline)
        app_dir = self._apps_dir() / app_id / manifest.version
        app_dir.mkdir(parents=True, exist_ok=True)
        
        source_file = app_dir / "source.zip"
        with open(source_file, "wb") as f:
            f.write(source_content)
        
        # 5. Create version
        version = AppVersion(
            version=manifest.version,
            build_hash=build_hash,
            created_at=now,
            status=AppStatus.PENDING,
        )
        
        # 6. Create app
        app = RegisteredApp(
            app_id=app_id,
            manifest=manifest,
            status=AppStatus.PENDING,
            current_version=manifest.version,
            versions=[version],
            created_at=now,
            updated_at=now,
            created_by=user_id,
            sandbox_url=f"/sandbox/{app_id}",
        )
        
        # 7. Save to registry
        self._apps[app_id] = app
        self._save_registry()
        
        return True, app, None
    
    async def build_app(self, app_id: str) -> tuple[bool, Optional[str]]:
        """앱 빌드 (난독화 + SDK 주입)"""
        app = self._apps.get(app_id)
        if not app:
            return False, "App not found"
        
        # Update status
        app.status = AppStatus.BUILDING
        self._save_registry()
        
        try:
            # In production: Run actual build pipeline
            # - Load source
            # - Bundle with esbuild
            # - Obfuscate with javascript-obfuscator
            # - Inject SDK
            # - Save built files
            
            # For now: simulate
            import asyncio
            await asyncio.sleep(1)
            
            # Update status
            app.status = AppStatus.ACTIVE
            for v in app.versions:
                if v.version == app.current_version:
                    v.status = AppStatus.ACTIVE
            app.updated_at = datetime.now(timezone.utc).isoformat()
            self._save_registry()
            
            return True, None
            
        except Exception as e:
            app.status = AppStatus.FAILED
            self._save_registry()
            return False, str(e)
    
    def get_app(self, app_id: str) -> Optional[RegisteredApp]:
        """앱 조회"""
        return self._apps.get(app_id)
    
    def list_apps(
        self,
        status: Optional[AppStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[RegisteredApp], int]:
        """앱 목록"""
        apps = list(self._apps.values())
        
        if status:
            apps = [a for a in apps if a.status == status]
        
        # Sort by updated_at desc
        apps.sort(key=lambda a: a.updated_at, reverse=True)
        
        total = len(apps)
        apps = apps[offset:offset + limit]
        
        return apps, total
    
    def update_status(self, app_id: str, status: AppStatus) -> bool:
        """상태 업데이트"""
        app = self._apps.get(app_id)
        if not app:
            return False
        
        app.status = status
        app.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_registry()
        return True
    
    def delete_app(self, app_id: str) -> bool:
        """앱 삭제"""
        if app_id not in self._apps:
            return False
        
        del self._apps[app_id]
        self._save_registry()
        
        # Delete files
        app_dir = self._apps_dir() / app_id
        if app_dir.exists():
            import shutil
            shutil.rmtree(app_dir)
        
        return True


# Singleton instance
_registry_service: Optional[AppRegistryService] = None


def get_app_registry() -> AppRegistryService:
    """레지스트리 서비스 인스턴스"""
    global _registry_service
    if _registry_service is None:
        _registry_service = AppRegistryService()
    return _registry_service
