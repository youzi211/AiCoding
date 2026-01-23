"""输入验证工具"""
import re
from fastapi import HTTPException


def validate_user_id(user_id: str) -> str:
    """
    验证 user_id，防止路径遍历攻击

    规则:
    - 不允许空值
    - 长度限制 1-64 字符
    - 禁止路径分隔符 (/, \)
    - 禁止父目录引用 (..)
    - 禁止空字节
    - 只允许字母、数字、下划线、连字符

    Args:
        user_id: 用户标识符

    Returns:
        str: 验证通过的 user_id

    Raises:
        HTTPException: 400 如果验证失败
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id 不能为空")

    if len(user_id) > 64:
        raise HTTPException(
            status_code=400,
            detail=f"user_id 过长（最大 64 字符，当前 {len(user_id)} 字符）"
        )

    # 检查危险字符
    dangerous_patterns = ['..', '/', '\\', '\0']
    for pattern in dangerous_patterns:
        if pattern in user_id:
            raise HTTPException(
                status_code=400,
                detail=f"user_id 包含非法字符: {repr(pattern)}"
            )

    # 只允许安全字符（字母、数字、下划线、连字符）
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        raise HTTPException(
            status_code=400,
            detail="user_id 只能包含字母、数字、下划线或连字符"
        )

    return user_id
