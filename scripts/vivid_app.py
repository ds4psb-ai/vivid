#!/usr/bin/env python3
"""Vivid App CLI - 앱 생성 및 관리 도구.

Usage:
    # 새 거장 추가
    python scripts/vivid_app.py create auteur shinkai \
        --display-name "신카이 마코토" \
        --themes "청춘,시간" \
        --style "contemplative,vivid"
    
    # 새 차원 추가
    python scripts/vivid_app.py create dimension custom_tool \
        --display-name "커스텀 도구" \
        --rag-mode always
    
    # 앱 목록
    python scripts/vivid_app.py list
    python scripts/vivid_app.py list --type auteur
    
    # 설정 검증
    python scripts/vivid_app.py validate
    
    # Hot-reload
    python scripts/vivid_app.py reload
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

CONFIG_DIR = PROJECT_ROOT / "config" / "apps"


def create_auteur(
    name: str,
    display_name: str,
    display_name_en: Optional[str] = None,
    icon: str = "🎬",
    themes: Optional[List[str]] = None,
    style_hints: Optional[dict] = None,
) -> Path:
    """새 거장 YAML 설정 생성."""
    import yaml
    
    themes = themes or []
    style_hints = style_hints or {}
    display_name_en = display_name_en or name.capitalize()
    
    config = {
        "$schema": "vivid-app/v2",
        "metadata": {
            "name": name,
            "type": "auteur",
            "version": "1.0.0",
            "bounded_context": "content",
        },
        "display": {
            "name_ko": display_name,
            "name_en": display_name_en,
            "icon": icon,
        },
        "capabilities": [
            {
                "name": "rag",
                "enabled": True,
                "config": {
                    "mode": "auteur_only",
                    "confidence_threshold": 0.7,
                    "retrieval": {
                        "strategy": "hybrid",
                        "top_k": 10,
                    },
                },
            },
            {
                "name": "cache",
                "enabled": True,
                "config": {"ttl": 7200},
            },
        ],
        "extensions": {
            "auteur": {
                "corpus_type": "v-shape",
                "sources": [
                    {
                        "type": "source_pack",
                        "path": f"data/source_packs/{name}/*.json",
                    },
                    {
                        "type": "vertex_ai",
                        "corpus_name": f"auteur_{name}",
                    },
                ],
                "style_hints": style_hints,
                "themes": themes,
            },
        },
        "keywords": {
            "patterns": [name],
        },
    }
    
    # 디렉토리 생성
    auteur_dir = CONFIG_DIR / "content" / "auteurs"
    auteur_dir.mkdir(parents=True, exist_ok=True)
    
    # YAML 파일 생성
    yaml_path = auteur_dir / f"{name}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Created auteur config: {yaml_path}")
    return yaml_path


def create_dimension(
    name: str,
    display_name: str,
    display_name_en: Optional[str] = None,
    icon: str = "🔧",
    rag_mode: str = "auteur_only",
    corpus: Optional[str] = None,
) -> Path:
    """새 차원 YAML 설정 생성."""
    import yaml
    
    display_name_en = display_name_en or name.upper()
    
    rag_enabled = rag_mode != "disabled"
    
    config = {
        "$schema": "vivid-app/v2",
        "metadata": {
            "name": name,
            "type": "dimension",
            "version": "1.0.0",
            "bounded_context": "content",
        },
        "display": {
            "name_ko": display_name,
            "name_en": display_name_en,
            "icon": icon,
        },
        "capabilities": [
            {
                "name": "rag",
                "enabled": rag_enabled,
                "config": {
                    "mode": rag_mode,
                    "confidence_threshold": 0.5,
                },
            },
            {
                "name": "cache",
                "enabled": True,
                "config": {"ttl": 3600},
            },
        ],
        "extensions": {
            "dimension": {
                "corpus": corpus or "",
                "tool_type": "generation",
            },
        },
        "keywords": {
            "patterns": [name],
        },
    }
    
    # 디렉토리 생성
    dim_dir = CONFIG_DIR / "content" / "dimensions"
    dim_dir.mkdir(parents=True, exist_ok=True)
    
    # YAML 파일 생성
    yaml_path = dim_dir / f"{name}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Created dimension config: {yaml_path}")
    return yaml_path


def list_apps(app_type: Optional[str] = None):
    """등록된 앱 목록 출력."""
    from app.core.app_registry import AppRegistry
    from config.apps.schema import AppType
    
    AppRegistry.discover(CONFIG_DIR)
    
    if app_type:
        apps = AppRegistry.get_by_type(AppType(app_type))
    else:
        apps = AppRegistry.get_all()
    
    print(f"\n📋 Registered Apps ({len(apps)}):\n")
    
    for app in sorted(apps, key=lambda a: (a.metadata.type.value, a.metadata.name)):
        rag_status = "✅" if app.has_capability("rag") else "❌"
        print(f"  [{app.metadata.type.value:10}] {app.display.icon} {app.metadata.name:15} - {app.display.name_ko} (RAG: {rag_status})")
    
    print()


def validate_configs():
    """모든 설정 파일 검증."""
    from config.apps.schema import AppConfig, validate_config
    
    yaml_files = list(CONFIG_DIR.rglob("*.yaml")) + list(CONFIG_DIR.rglob("*.yml"))
    errors = []
    valid_count = 0
    
    print(f"\n🔍 Validating {len(yaml_files)} config files...\n")
    
    for yaml_file in yaml_files:
        if yaml_file.stem.startswith("_") or yaml_file.stem == "schema":
            continue
        
        try:
            config = AppConfig.from_yaml(yaml_file)
            config_errors = validate_config(config)
            
            if config_errors:
                errors.append((yaml_file, config_errors))
                print(f"  ❌ {yaml_file.name}: {config_errors}")
            else:
                valid_count += 1
                print(f"  ✅ {yaml_file.name}")
                
        except Exception as e:
            errors.append((yaml_file, [str(e)]))
            print(f"  ❌ {yaml_file.name}: {e}")
    
    print(f"\n📊 Results: {valid_count} valid, {len(errors)} errors")
    return len(errors) == 0


def reload_registry():
    """Registry 설정 핫 리로드."""
    from app.core.app_registry import AppRegistry
    
    print("🔄 Reloading AppRegistry...")
    
    AppRegistry.hot_reload()
    stats = AppRegistry.get_stats()
    
    print(f"✅ Reloaded: {stats['total_apps']} apps")
    print(f"   By type: {stats['by_type']}")
    print(f"   By capability: {stats['by_capability']}")


def main():
    parser = argparse.ArgumentParser(
        description="Vivid App CLI - 앱 생성 및 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # create 명령어
    create_parser = subparsers.add_parser("create", help="Create new app config")
    create_subparsers = create_parser.add_subparsers(dest="app_type")
    
    # create auteur
    auteur_parser = create_subparsers.add_parser("auteur", help="Create new auteur")
    auteur_parser.add_argument("name", help="Auteur key name (e.g., shinkai)")
    auteur_parser.add_argument("--display-name", required=True, help="Korean display name")
    auteur_parser.add_argument("--display-name-en", help="English display name")
    auteur_parser.add_argument("--icon", default="🎬", help="Emoji icon")
    auteur_parser.add_argument("--themes", help="Comma-separated themes")
    auteur_parser.add_argument("--style", help="Comma-separated style hints (key=value)")
    
    # create dimension
    dim_parser = create_subparsers.add_parser("dimension", help="Create new dimension")
    dim_parser.add_argument("name", help="Dimension code (e.g., custom_tool)")
    dim_parser.add_argument("--display-name", required=True, help="Korean display name")
    dim_parser.add_argument("--display-name-en", help="English display name")
    dim_parser.add_argument("--icon", default="🔧", help="Emoji icon")
    dim_parser.add_argument("--rag-mode", default="auteur_only", 
                           choices=["always", "auteur_only", "disabled"],
                           help="RAG mode")
    dim_parser.add_argument("--corpus", help="Corpus name")
    
    # list 명령어
    list_parser = subparsers.add_parser("list", help="List registered apps")
    list_parser.add_argument("--type", choices=["auteur", "dimension"],
                            help="Filter by app type")
    
    # validate 명령어
    subparsers.add_parser("validate", help="Validate all config files")
    
    # reload 명령어
    subparsers.add_parser("reload", help="Hot-reload registry")
    
    args = parser.parse_args()
    
    if args.command == "create":
        if args.app_type == "auteur":
            themes = args.themes.split(",") if args.themes else []
            style_hints = {}
            if args.style:
                for item in args.style.split(","):
                    if "=" in item:
                        k, v = item.split("=", 1)
                        style_hints[k.strip()] = v.strip()
            
            create_auteur(
                name=args.name,
                display_name=args.display_name,
                display_name_en=args.display_name_en,
                icon=args.icon,
                themes=themes,
                style_hints=style_hints,
            )
            
        elif args.app_type == "dimension":
            create_dimension(
                name=args.name,
                display_name=args.display_name,
                display_name_en=args.display_name_en,
                icon=args.icon,
                rag_mode=args.rag_mode,
                corpus=args.corpus,
            )
        else:
            create_parser.print_help()
            
    elif args.command == "list":
        list_apps(args.type)
        
    elif args.command == "validate":
        success = validate_configs()
        sys.exit(0 if success else 1)
        
    elif args.command == "reload":
        reload_registry()
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
