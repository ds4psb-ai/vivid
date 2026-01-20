"""
Error Message Translations (i18n Support) (H3.3)

Provides localized error messages in English, Korean, and Japanese.
Messages are keyed by error_code and include both title and detail variations.

Usage:
    from app.i18n.errors import get_localized_message

    # Get title in Korean
    title = get_localized_message("INSUFFICIENT_CREDITS", "title", lang="ko")

    # Get detail in English (default)
    detail = get_localized_message("INSUFFICIENT_CREDITS", "detail")
"""
from typing import Dict, Optional


# Error message translations
# Format: error_code -> {lang -> {title, detail}}
ERROR_MESSAGES: Dict[str, Dict[str, Dict[str, str]]] = {
    "INSUFFICIENT_CREDITS": {
        "en": {
            "title": "Insufficient Credits",
            "detail": "This operation requires more credits than you have available",
        },
        "ko": {
            "title": "크레딧 부족",
            "detail": "이 작업을 수행하기 위한 크레딧이 부족합니다",
        },
        "ja": {
            "title": "クレジット不足",
            "detail": "この操作を実行するためのクレジットが不足しています",
        },
    },
    "TOKEN_EXPIRED": {
        "en": {
            "title": "Token Expired",
            "detail": "Your session token has expired",
        },
        "ko": {
            "title": "토큰 만료",
            "detail": "세션 토큰이 만료되었습니다",
        },
        "ja": {
            "title": "トークン期限切れ",
            "detail": "セッショントークンが期限切れです",
        },
    },
    "RATE_LIMITED": {
        "en": {
            "title": "Rate Limit Exceeded",
            "detail": "Too many requests. Please try again later",
        },
        "ko": {
            "title": "요청 한도 초과",
            "detail": "요청이 너무 많습니다. 나중에 다시 시도해주세요",
        },
        "ja": {
            "title": "レート制限超過",
            "detail": "リクエストが多すぎます。後でもう一度お試しください",
        },
    },
    "VALIDATION_ERROR": {
        "en": {
            "title": "Validation Error",
            "detail": "Request validation failed",
        },
        "ko": {
            "title": "유효성 검사 오류",
            "detail": "요청 유효성 검사에 실패했습니다",
        },
        "ja": {
            "title": "バリデーションエラー",
            "detail": "リクエストのバリデーションに失敗しました",
        },
    },
    "AUTHENTICATION_REQUIRED": {
        "en": {
            "title": "Authentication Required",
            "detail": "You must be logged in to access this resource",
        },
        "ko": {
            "title": "인증 필요",
            "detail": "이 리소스에 접근하려면 로그인해야 합니다",
        },
        "ja": {
            "title": "認証が必要です",
            "detail": "このリソースにアクセスするにはログインが必要です",
        },
    },
    "PERMISSION_DENIED": {
        "en": {
            "title": "Permission Denied",
            "detail": "You don't have permission to perform this action",
        },
        "ko": {
            "title": "권한 거부",
            "detail": "이 작업을 수행할 권한이 없습니다",
        },
        "ja": {
            "title": "権限がありません",
            "detail": "この操作を実行する権限がありません",
        },
    },
    "TOKEN_INVALID": {
        "en": {
            "title": "Invalid Token",
            "detail": "The provided token is invalid or malformed",
        },
        "ko": {
            "title": "잘못된 토큰",
            "detail": "제공된 토큰이 유효하지 않거나 형식이 잘못되었습니다",
        },
        "ja": {
            "title": "無効なトークン",
            "detail": "提供されたトークンが無効か、形式が正しくありません",
        },
    },
    "RESOURCE_NOT_FOUND": {
        "en": {
            "title": "Resource Not Found",
            "detail": "The requested resource was not found",
        },
        "ko": {
            "title": "리소스를 찾을 수 없음",
            "detail": "요청한 리소스를 찾을 수 없습니다",
        },
        "ja": {
            "title": "リソースが見つかりません",
            "detail": "リクエストされたリソースが見つかりませんでした",
        },
    },
    "RESOURCE_CONFLICT": {
        "en": {
            "title": "Resource Conflict",
            "detail": "The operation conflicts with the current state of the resource",
        },
        "ko": {
            "title": "리소스 충돌",
            "detail": "작업이 리소스의 현재 상태와 충돌합니다",
        },
        "ja": {
            "title": "リソースの競合",
            "detail": "操作がリソースの現在の状態と競合しています",
        },
    },
    "CAPSULE_EXECUTION_FAILED": {
        "en": {
            "title": "Capsule Execution Failed",
            "detail": "Failed to execute the capsule",
        },
        "ko": {
            "title": "캡슐 실행 실패",
            "detail": "캡슐 실행에 실패했습니다",
        },
        "ja": {
            "title": "カプセル実行失敗",
            "detail": "カプセルの実行に失敗しました",
        },
    },
    "GENERATION_FAILED": {
        "en": {
            "title": "Generation Failed",
            "detail": "Content generation failed",
        },
        "ko": {
            "title": "생성 실패",
            "detail": "콘텐츠 생성에 실패했습니다",
        },
        "ja": {
            "title": "生成失敗",
            "detail": "コンテンツの生成に失敗しました",
        },
    },
    "RAG_QUERY_FAILED": {
        "en": {
            "title": "RAG Query Failed",
            "detail": "Knowledge retrieval query failed",
        },
        "ko": {
            "title": "RAG 쿼리 실패",
            "detail": "지식 검색 쿼리가 실패했습니다",
        },
        "ja": {
            "title": "RAGクエリ失敗",
            "detail": "知識検索クエリに失敗しました",
        },
    },
    "SERVICE_UNAVAILABLE": {
        "en": {
            "title": "Service Unavailable",
            "detail": "The service is temporarily unavailable",
        },
        "ko": {
            "title": "서비스 이용 불가",
            "detail": "서비스가 일시적으로 이용 불가능합니다",
        },
        "ja": {
            "title": "サービス利用不可",
            "detail": "サービスは一時的に利用できません",
        },
    },
    "UPSTREAM_ERROR": {
        "en": {
            "title": "Upstream Error",
            "detail": "An upstream service returned an error",
        },
        "ko": {
            "title": "업스트림 오류",
            "detail": "업스트림 서비스에서 오류가 발생했습니다",
        },
        "ja": {
            "title": "アップストリームエラー",
            "detail": "アップストリームサービスがエラーを返しました",
        },
    },
    "TIMEOUT": {
        "en": {
            "title": "Operation Timeout",
            "detail": "The operation timed out",
        },
        "ko": {
            "title": "작업 시간 초과",
            "detail": "작업 시간이 초과되었습니다",
        },
        "ja": {
            "title": "操作タイムアウト",
            "detail": "操作がタイムアウトしました",
        },
    },
    "INTERNAL_ERROR": {
        "en": {
            "title": "Internal Server Error",
            "detail": "An unexpected error occurred",
        },
        "ko": {
            "title": "내부 서버 오류",
            "detail": "예기치 않은 오류가 발생했습니다",
        },
        "ja": {
            "title": "内部サーバーエラー",
            "detail": "予期しないエラーが発生しました",
        },
    },
    "SUBSCRIPTION_REQUIRED": {
        "en": {
            "title": "Subscription Required",
            "detail": "A subscription is required to access this feature",
        },
        "ko": {
            "title": "구독 필요",
            "detail": "이 기능을 사용하려면 구독이 필요합니다",
        },
        "ja": {
            "title": "サブスクリプションが必要です",
            "detail": "この機能を利用するにはサブスクリプションが必要です",
        },
    },
}


# Supported languages (BCP-47 codes)
SUPPORTED_LANGUAGES = ["en", "ko", "ja"]
DEFAULT_LANGUAGE = "en"


def get_localized_message(
    error_code: str,
    field: str = "detail",
    lang: str = DEFAULT_LANGUAGE,
) -> str:
    """
    Get localized error message.

    Args:
        error_code: The error code (e.g., "INSUFFICIENT_CREDITS")
        field: The field to get ("title" or "detail")
        lang: Language code (en, ko, ja)

    Returns:
        Localized message string, or falls back to English if not found.
    """
    messages = ERROR_MESSAGES.get(error_code, {})

    # Try requested language
    if lang in messages and field in messages[lang]:
        return messages[lang][field]

    # Fallback to English
    if DEFAULT_LANGUAGE in messages and field in messages[DEFAULT_LANGUAGE]:
        return messages[DEFAULT_LANGUAGE][field]

    # Ultimate fallback
    return error_code


def get_localized_error(
    error_code: str,
    lang: str = DEFAULT_LANGUAGE,
) -> Dict[str, str]:
    """
    Get both title and detail for an error code.

    Args:
        error_code: The error code
        lang: Language code

    Returns:
        Dict with "title" and "detail" keys.
    """
    return {
        "title": get_localized_message(error_code, "title", lang),
        "detail": get_localized_message(error_code, "detail", lang),
    }


def get_supported_languages() -> list:
    """Get list of supported language codes."""
    return SUPPORTED_LANGUAGES.copy()


def detect_language_from_header(accept_language: Optional[str]) -> str:
    """
    Detect preferred language from Accept-Language header.

    Args:
        accept_language: Accept-Language header value

    Returns:
        Best matching language code.
    """
    if not accept_language:
        return DEFAULT_LANGUAGE

    # Simple parsing - take first supported language
    for lang in accept_language.lower().replace(" ", "").split(","):
        # Handle quality values (e.g., "ko;q=0.9")
        lang_code = lang.split(";")[0].split("-")[0]
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code

    return DEFAULT_LANGUAGE
