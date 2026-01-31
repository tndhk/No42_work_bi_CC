"""API レスポンスラッパーヘルパー

Frontend が期待するレスポンス形式に統一するためのヘルパー関数。
"""

from typing import Any, Dict, List


def api_response(data: Any) -> Dict[str, Any]:
    """単体レスポンスを { data: T } 形式でラップ

    Args:
        data: レスポンスデータ

    Returns:
        { "data": data } 形式の辞書
    """
    return {"data": data}


def paginated_response(
    items: List[Any],
    total: int,
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """一覧レスポンスを { data: [...], pagination: {...} } 形式でラップ

    Args:
        items: アイテムのリスト
        total: 総アイテム数
        limit: 1ページあたりのアイテム数
        offset: オフセット (開始位置)

    Returns:
        {
            "data": items,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total
            }
        } 形式の辞書
    """
    return {
        "data": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }
