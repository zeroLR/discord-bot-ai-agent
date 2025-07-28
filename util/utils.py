def transform_response_content(content: str, chunk_size: int = 2000) -> list[str]:
    """
    將 content 依 chunk_size 分割為多個字串，回傳 list[str]
    """
    return [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
