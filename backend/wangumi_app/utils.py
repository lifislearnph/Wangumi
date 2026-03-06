# -*- coding: utf-8 -*-

import jwt
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()


def _ok(data=None, message="success", code=0):
    return {
        "code": code,
        "message": message,
        "data": data or {}
    }


def _err(message="error", code=1, data=None):
    return {
        "code": code,
        "message": message,
        "data": data or {}
    }


def generate_jwt(user: User):
    
    payload = {
        "user_id": user.id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def parse_jwt(request: HttpRequest):
    """
    解析 Authorization: Bearer <token>
    并返回 User 对象。
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None

    token = auth.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return User.objects.filter(id=user_id).first()
    except Exception:
        return None


# 通用的view工具函数
from django.http import JsonResponse


def build_error_response(message: str, status: int = 400) -> JsonResponse:
    """
    构建标准错误响应

    Args:
        message: 错误信息
        status: HTTP状态码，默认为400

    Returns:
        JsonResponse: 标准格式的错误响应
    """
    payload = {"code": 1, "message": message, "data": None}
    return JsonResponse(payload, status=status, json_dumps_params={'ensure_ascii': False})


def resolve_cover_url(anime) -> str:
    """
    解析动漫封面URL，优先使用上传的图片，其次使用cover_url字段

    Args:
        anime: Anime模型实例

    Returns:
        str: 封面图片的URL
    """
    cover_image = getattr(anime, "cover_image", None)
    if cover_image:
        raw_name = getattr(cover_image, "name", "") or ""
        try:
            url = cover_image.url
        except (ValueError, AttributeError):
            url = raw_name
        if url.startswith("/media/http") and raw_name.startswith(("http://", "https://")):
            return raw_name
        if url:
            return url
    cover_url = getattr(anime, "cover_url", "") or ""
    return cover_url


def resolve_avatar_url(user) -> str:
    """
    解析用户头像URL，优先使用用户上传的头像，其次使用默认头像

    Args:
        user: User模型实例

    Returns:
        str: 头像图片的URL
    """
    try:
        userP = user.userprofile
        if userP.avatar:
            return userP.avatar.url
    except (AttributeError, ValueError):
        pass

    # 返回默认头像路径
    return "default-avatar.png"  # 默认头像存放在/media/default-avatar.png
