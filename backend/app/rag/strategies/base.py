from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class RetrievedDoc:
    """검색된 문서."""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any]

class BaseRetriever(ABC):
    """Retriever 인터페이스."""
    
    @abstractmethod
    async def retrieve(self, query: str) -> List[RetrievedDoc]:
        """쿼리에 맞는 문서 검색."""
        pass

class BaseGenerator(ABC):
    """Generator 인터페이스."""
    
    @abstractmethod
    async def generate(self, query: str, docs: List[RetrievedDoc]) -> str:
        """검색된 문서를 바탕으로 답변 생성."""
        pass
