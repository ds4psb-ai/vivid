"""Prompty Download Router.

Download gift-package as ZIP.
"""
import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/download", tags=["prompty-download"])

# gift-package 경로 (상대 경로로 설정)
GIFT_PACKAGE_PATH = Path(__file__).parent.parent.parent.parent.parent / "viral-video-automation" / "gift-package"


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
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in GIFT_PACKAGE_PATH.rglob('*'):
            if file_path.is_file():
                # .DS_Store 등 제외
                if file_path.name.startswith('.') and file_path.name != '.prompty.config.yaml':
                    continue
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
        if file_path.is_file():
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
