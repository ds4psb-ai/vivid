"""Prompty Download Router.

Download gift-package as ZIP.
"""
import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/download", tags=["prompty-download"])

# gift-package 경로 (backend/assets 내부)
GIFT_PACKAGE_PATH = Path(__file__).parent.parent.parent.parent / "assets" / "gift-package"

# 보안 상수
MAX_ZIP_SIZE = 50 * 1024 * 1024  # 50MB 제한


@router.get("/package")
async def download_package():
    """Download Prompty project package as ZIP.

    Returns the complete gift-package with:
    - start.sh (quick start)
    - scripts/ (init, extract, extract-smart)
    - templates/ (6 core templates)
    - guides/ (4 workflow guides)
    - .prompty.config.yaml

    Returns:
        StreamingResponse: ZIP file download
    """
    if not GIFT_PACKAGE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Package not found at {GIFT_PACKAGE_PATH}"
        )

    # ZIP 생성
    zip_buffer = io.BytesIO()
    total_size = 0

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in GIFT_PACKAGE_PATH.rglob('*'):
            # symlink 건너뛰기 (보안)
            if file_path.is_symlink():
                continue
            if not file_path.is_file():
                continue
            # 경로 탈출 방지 (path traversal)
            if not file_path.resolve().is_relative_to(GIFT_PACKAGE_PATH.resolve()):
                continue
            # .DS_Store 등 제외
            if file_path.name.startswith('.') and file_path.name != '.prompty.config.yaml':
                continue

            # 파일 크기 누적 체크
            file_size = file_path.stat().st_size
            total_size += file_size
            if total_size > MAX_ZIP_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"Package exceeds maximum size ({MAX_ZIP_SIZE // (1024*1024)}MB)"
                )

            arcname = f"prompty-project/{file_path.relative_to(GIFT_PACKAGE_PATH)}"
            zf.write(file_path, arcname)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=prompty-project.zip",
            "Content-Length": str(zip_buffer.getbuffer().nbytes),
        }
    )


@router.get("/package/contents")
async def list_package_contents():
    """List contents of the gift-package.

    Returns:
        dict: File tree and sizes
    """
    if not GIFT_PACKAGE_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Package not found"
        )

    files = []
    total_size = 0

    for file_path in GIFT_PACKAGE_PATH.rglob('*'):
        # symlink 건너뛰기 (보안)
        if file_path.is_symlink():
            continue
        if not file_path.is_file():
            continue
        # 경로 탈출 방지
        if not file_path.resolve().is_relative_to(GIFT_PACKAGE_PATH.resolve()):
            continue
        if file_path.name.startswith('.') and file_path.name != '.prompty.config.yaml':
            continue
        size = file_path.stat().st_size
        total_size += size
        files.append({
            "path": str(file_path.relative_to(GIFT_PACKAGE_PATH)),
            "size": size,
            "size_human": _format_size(size),
        })

    return {
        "files": sorted(files, key=lambda x: x["path"]),
        "total_files": len(files),
        "total_size": total_size,
        "total_size_human": _format_size(total_size),
    }


def _format_size(size: int) -> str:
    """Format size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
