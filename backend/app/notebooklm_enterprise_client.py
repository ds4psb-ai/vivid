"""
NotebookLM Enterprise API Client

NotebookLM Enterprise API를 사용하여 노트북 생성, 소스 추가, 
오디오 오버뷰 생성 등을 자동화하는 클라이언트.

Reference:
- https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks
- https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources
- https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-audio-overview

License: Gemini Enterprise (arkain.info@gmail.com)
Project: vivid-canvas-482303 (239259013228)
"""

import logging
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass
from pathlib import Path

import httpx
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


@dataclass
class NotebookInfo:
    """노트북 정보."""
    notebook_id: str
    title: str
    name: str  # Full resource name
    user_role: str
    is_shared: bool


@dataclass
class SourceInfo:
    """소스 정보."""
    source_id: str
    name: str


@dataclass
class AudioOverviewInfo:
    """오디오 오버뷰 정보."""
    audio_overview_id: str
    status: str
    name: str


class NotebookLMEnterpriseClient:
    """
    NotebookLM Enterprise API 클라이언트.
    
    Usage:
        client = NotebookLMEnterpriseClient(project_number="123456789")
        
        # 노트북 생성
        notebook = await client.create_notebook("CL_BONG_HOOK")
        
        # 텍스트 소스 추가
        await client.add_text_source(
            notebook.notebook_id,
            "봉준호 마스터클래스",
            "자막 텍스트..."
        )
        
        # 오디오 오버뷰 생성
        await client.create_audio_overview(
            notebook.notebook_id,
            focus="봉준호 감독의 미장센 분석"
        )
    """
    
    BASE_URL = "https://{endpoint}-discoveryengine.googleapis.com/v1alpha"
    UPLOAD_URL = "https://{endpoint}-discoveryengine.googleapis.com/upload/v1alpha"
    
    # 지원되는 콘텐츠 유형
    SUPPORTED_CONTENT_TYPES = {
        # 문서
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        # 오디오
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/m4a",
        ".ogg": "audio/ogg",
        ".aac": "audio/aac",
        # 이미지
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    
    def __init__(
        self,
        project_number: str,
        location: str = "global",
        endpoint_location: str = "global",
        credentials_path: Optional[str] = None,
    ):
        """
        Args:
            project_number: GCP 프로젝트 번호 (숫자 ID)
            location: 데이터 스토어 위치 (global, us, eu)
            endpoint_location: API 엔드포인트 리전 (global, us, eu)
            credentials_path: 서비스 계정 JSON 경로 (없으면 ADC 사용)
        """
        self.project_number = project_number
        self.location = location
        self.endpoint_location = endpoint_location
        self._credentials = None
        self._credentials_path = credentials_path
        
        # Base URLs with endpoint
        self._base_url = self.BASE_URL.format(endpoint=f"{endpoint_location}-")
        self._upload_url = self.UPLOAD_URL.format(endpoint=f"{endpoint_location}-")
    
    def _get_access_token(self) -> str:
        """Google Cloud 액세스 토큰 발급."""
        if self._credentials is None:
            if self._credentials_path:
                self._credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path,
                    scopes=[
                        "https://www.googleapis.com/auth/cloud-platform",
                        "https://www.googleapis.com/auth/drive.readonly",
                    ]
                )
            else:
                self._credentials, _ = default(
                    scopes=[
                        "https://www.googleapis.com/auth/cloud-platform",
                        "https://www.googleapis.com/auth/drive.readonly",
                    ]
                )
        
        self._credentials.refresh(Request())
        return self._credentials.token
    
    def _get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }
    
    def _notebooks_url(self, notebook_id: Optional[str] = None) -> str:
        """노트북 API URL 생성."""
        base = f"{self._base_url}/projects/{self.project_number}/locations/{self.location}/notebooks"
        if notebook_id:
            return f"{base}/{notebook_id}"
        return base
    
    # ─────────────────────────────────────────────────────────────────────
    # 노트북 관리
    # ─────────────────────────────────────────────────────────────────────
    
    async def create_notebook(self, title: str) -> NotebookInfo:
        """
        새 노트북 생성.
        
        Args:
            title: 노트북 제목 (UTF-8 인코딩)
        
        Returns:
            NotebookInfo 객체
        """
        url = self._notebooks_url()
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                headers=self._get_headers(),
                json={"title": title}
            )
            resp.raise_for_status()
            data = resp.json()
        
        logger.info(f"Created notebook: {data.get('notebookId')}")
        
        return NotebookInfo(
            notebook_id=data["notebookId"],
            title=data["title"],
            name=data["name"],
            user_role=data.get("metadata", {}).get("userRole", ""),
            is_shared=data.get("metadata", {}).get("isShared", False),
        )
    
    async def get_notebook(self, notebook_id: str) -> NotebookInfo:
        """노트북 정보 조회."""
        url = self._notebooks_url(notebook_id)
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._get_headers())
            resp.raise_for_status()
            data = resp.json()
        
        return NotebookInfo(
            notebook_id=data["notebookId"],
            title=data["title"],
            name=data["name"],
            user_role=data.get("metadata", {}).get("userRole", ""),
            is_shared=data.get("metadata", {}).get("isShared", False),
        )
    
    async def list_notebooks(self, page_size: int = 10) -> List[NotebookInfo]:
        """최근 노트북 목록 조회."""
        url = self._notebooks_url()
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                headers=self._get_headers(),
                params={"pageSize": page_size}
            )
            resp.raise_for_status()
            data = resp.json()
        
        notebooks = []
        for nb in data.get("notebooks", []):
            notebooks.append(NotebookInfo(
                notebook_id=nb["notebookId"],
                title=nb["title"],
                name=nb["name"],
                user_role=nb.get("metadata", {}).get("userRole", ""),
                is_shared=nb.get("metadata", {}).get("isShared", False),
            ))
        
        return notebooks
    
    async def delete_notebooks(self, notebook_ids: List[str]) -> bool:
        """노트북 일괄 삭제."""
        url = f"{self._notebooks_url()}:batchDelete"
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                headers=self._get_headers(),
                json={"notebookIds": notebook_ids}
            )
            resp.raise_for_status()
        
        logger.info(f"Deleted notebooks: {notebook_ids}")
        return True
    
    # ─────────────────────────────────────────────────────────────────────
    # 소스 관리
    # ─────────────────────────────────────────────────────────────────────
    
    async def add_text_source(
        self,
        notebook_id: str,
        source_name: str,
        content: str
    ) -> SourceInfo:
        """
        텍스트 소스 추가.
        
        Args:
            notebook_id: 대상 노트북 ID
            source_name: 소스 표시 이름
            content: 텍스트 내용
        """
        url = f"{self._notebooks_url(notebook_id)}/sources:batchCreate"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers=self._get_headers(),
                json={
                    "userContents": [{
                        "textContent": {
                            "sourceName": source_name,
                            "content": content
                        }
                    }]
                }
            )
            resp.raise_for_status()
            data = resp.json()
        
        source = data.get("sourceIds", [{}])[0]
        logger.info(f"Added text source: {source.get('id')}")
        
        return SourceInfo(
            source_id=source.get("id", ""),
            name=source_name
        )
    
    async def add_web_source(
        self,
        notebook_id: str,
        source_name: str,
        url: str
    ) -> SourceInfo:
        """
        웹 URL 소스 추가.
        
        Args:
            notebook_id: 대상 노트북 ID
            source_name: 소스 표시 이름
            url: 웹 페이지 URL
        """
        api_url = f"{self._notebooks_url(notebook_id)}/sources:batchCreate"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                api_url,
                headers=self._get_headers(),
                json={
                    "userContents": [{
                        "webContent": {
                            "url": url,
                            "sourceName": source_name
                        }
                    }]
                }
            )
            resp.raise_for_status()
            data = resp.json()
        
        source = data.get("sourceIds", [{}])[0]
        logger.info(f"Added web source: {source.get('id')}")
        
        return SourceInfo(
            source_id=source.get("id", ""),
            name=source_name
        )
    
    async def add_drive_source(
        self,
        notebook_id: str,
        source_name: str,
        document_id: str,
        mime_type: Literal[
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.presentation"
        ] = "application/vnd.google-apps.document"
    ) -> SourceInfo:
        """
        Google Drive 문서 소스 추가.
        
        Args:
            notebook_id: 대상 노트북 ID
            source_name: 소스 표시 이름
            document_id: Google Drive 문서 ID
            mime_type: 문서 유형 (Docs 또는 Slides)
        """
        url = f"{self._notebooks_url(notebook_id)}/sources:batchCreate"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers=self._get_headers(),
                json={
                    "userContents": [{
                        "googleDriveContent": {
                            "documentId": document_id,
                            "mimeType": mime_type,
                            "sourceName": source_name
                        }
                    }]
                }
            )
            resp.raise_for_status()
            data = resp.json()
        
        source = data.get("sourceIds", [{}])[0]
        logger.info(f"Added Drive source: {source.get('id')}")
        
        return SourceInfo(
            source_id=source.get("id", ""),
            name=source_name
        )
    
    async def upload_file_source(
        self,
        notebook_id: str,
        file_path: str,
        display_name: Optional[str] = None
    ) -> SourceInfo:
        """
        파일 업로드 소스 추가.
        
        Args:
            notebook_id: 대상 노트북 ID
            file_path: 업로드할 파일 경로
            display_name: 표시 이름 (없으면 파일명 사용)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        content_type = self.SUPPORTED_CONTENT_TYPES.get(suffix)
        if not content_type:
            raise ValueError(f"Unsupported file type: {suffix}")
        
        display_name = display_name or path.name
        
        url = (
            f"{self._upload_url}/projects/{self.project_number}"
            f"/locations/{self.location}/notebooks/{notebook_id}/sources:uploadFile"
        )
        
        with open(path, "rb") as f:
            file_content = f.read()
        
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "X-Goog-Upload-File-Name": display_name,
            "X-Goog-Upload-Protocol": "raw",
            "Content-Type": content_type,
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, content=file_content)
            resp.raise_for_status()
            data = resp.json()
        
        source_id = data.get("sourceId", {}).get("id", "")
        logger.info(f"Uploaded file source: {source_id}")
        
        return SourceInfo(
            source_id=source_id,
            name=display_name
        )
    
    async def add_sources_batch(
        self,
        notebook_id: str,
        sources: List[Dict[str, Any]]
    ) -> List[SourceInfo]:
        """
        여러 소스 일괄 추가.
        
        Args:
            notebook_id: 대상 노트북 ID
            sources: 소스 목록 (textContent, webContent, googleDriveContent 중 하나)
        """
        url = f"{self._notebooks_url(notebook_id)}/sources:batchCreate"
        
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                url,
                headers=self._get_headers(),
                json={"userContents": sources}
            )
            resp.raise_for_status()
            data = resp.json()
        
        results = []
        for source in data.get("sourceIds", []):
            results.append(SourceInfo(
                source_id=source.get("id", ""),
                name=""  # batch에서는 개별 이름 반환 안됨
            ))
        
        logger.info(f"Added {len(results)} sources in batch")
        return results
    
    async def get_source(self, notebook_id: str, source_id: str) -> Dict[str, Any]:
        """소스 정보 조회."""
        url = f"{self._notebooks_url(notebook_id)}/sources/{source_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._get_headers())
            resp.raise_for_status()
            return resp.json()
    
    async def delete_source(self, notebook_id: str, source_id: str) -> bool:
        """소스 삭제."""
        url = f"{self._notebooks_url(notebook_id)}/sources/{source_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(url, headers=self._get_headers())
            resp.raise_for_status()
        
        logger.info(f"Deleted source: {source_id}")
        return True
    
    # ─────────────────────────────────────────────────────────────────────
    # AI 오디오 오버뷰
    # ─────────────────────────────────────────────────────────────────────
    
    async def create_audio_overview(
        self,
        notebook_id: str,
        source_ids: Optional[List[str]] = None,
        focus: str = "",
        language_code: str = "ko"
    ) -> AudioOverviewInfo:
        """
        AI 오디오 오버뷰 생성.
        
        Args:
            notebook_id: 대상 노트북 ID
            source_ids: 포함할 소스 ID 목록 (없으면 전체 소스 사용)
            focus: 강조할 주제/콘텐츠 설명
            language_code: 출력 언어 코드 (ko, en, ja 등)
        
        Returns:
            AudioOverviewInfo 객체 (생성 중 상태로 반환)
        """
        url = f"{self._notebooks_url(notebook_id)}/audioOverviews"
        
        payload: Dict[str, Any] = {
            "episodeFocus": focus,
            "languageCode": language_code
        }
        
        if source_ids:
            payload["sourceIds"] = [{"id": sid} for sid in source_ids]
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            resp.raise_for_status()
            data = resp.json()
        
        overview = data.get("audioOverview", {})
        logger.info(f"Created audio overview: {overview.get('audioOverviewId')}")
        
        return AudioOverviewInfo(
            audio_overview_id=overview.get("audioOverviewId", ""),
            status=overview.get("status", ""),
            name=overview.get("name", "")
        )
    
    async def get_audio_overview(
        self,
        notebook_id: str,
        audio_overview_id: str
    ) -> AudioOverviewInfo:
        """오디오 오버뷰 상태 조회."""
        url = f"{self._notebooks_url(notebook_id)}/audioOverviews/{audio_overview_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._get_headers())
            resp.raise_for_status()
            data = resp.json()
        
        return AudioOverviewInfo(
            audio_overview_id=data.get("audioOverviewId", ""),
            status=data.get("status", ""),
            name=data.get("name", "")
        )
    
    async def delete_audio_overview(
        self,
        notebook_id: str,
        audio_overview_id: str
    ) -> bool:
        """오디오 오버뷰 삭제."""
        url = f"{self._notebooks_url(notebook_id)}/audioOverviews/{audio_overview_id}"
        
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(url, headers=self._get_headers())
            resp.raise_for_status()
        
        logger.info(f"Deleted audio overview: {audio_overview_id}")
        return True


# ─────────────────────────────────────────────────────────────────────────
# Convenience functions
# ─────────────────────────────────────────────────────────────────────────

async def create_auteur_notebook(
    client: NotebookLMEnterpriseClient,
    cluster_id: str,
    temporal_phase: str,
    sources: List[Dict[str, Any]]
) -> NotebookInfo:
    """
    거장 분석용 노트북 생성 및 소스 추가.
    
    Args:
        client: NotebookLMEnterpriseClient 인스턴스
        cluster_id: 거장 클러스터 ID (예: CL_BONG)
        temporal_phase: 시간 단계 (예: HOOK, BUILD)
        sources: 추가할 소스 목록
    
    Returns:
        생성된 NotebookInfo
    """
    from datetime import datetime
    
    title = f"{cluster_id}_{temporal_phase}_{datetime.now():%Y%m%d}"
    notebook = await client.create_notebook(title)
    
    if sources:
        await client.add_sources_batch(notebook.notebook_id, sources)
    
    logger.info(f"Created auteur notebook: {title} with {len(sources)} sources")
    return notebook
