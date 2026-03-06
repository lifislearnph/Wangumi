from functools import reduce
from typing import Any, Dict, Optional
from datetime import  date, timedelta

from django.core.paginator import Paginator
from django.db.models import Q

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.authentication import SessionAuthentication

from wangumi_app.models import SyncLog, Anime, Episode, WatchStatus
from wangumi_app.services.season_sync_service import get_current_season_year_and_quarter
from wangumi_app.utils import resolve_cover_url

class WeeklySyncView(APIView):
    """手动触发周合集同步，返回本次日志信息。"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Anime.objects.all()  # 获取所有动漫，后续会进行周度筛选
        payload = _build_anime_list_payload(request, queryset, view_mode="weekly")
        return Response(payload, status=status.HTTP_200_OK)


class SeasonSyncView(APIView):
    """手动触发季度番同步，返回本次日志信息。"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Anime.objects.all()  # 获取所有动漫，后续会进行季度筛选
        payload = _build_anime_list_payload(request, queryset, view_mode="season")
        return Response(payload, status=status.HTTP_200_OK)


def _build_anime_list_payload(request, base_queryset, view_mode: str) -> Dict[str, Any]:
    raw_sort = (request.GET.get("sort") or "").strip()
    sort_map = {
        "热度": "-popularity",
        "hot": "-popularity",
        "popularity": "-popularity",
        "时间": "-updated_at",
        "time": "-updated_at",
        "updated_at": "-updated_at",
        "评分": "-rating",
        "rating": "-rating",
        "score": "-rating",
    }
    if raw_sort:
        order_by = sort_map.get(raw_sort) or sort_map.get(raw_sort.lower())
        if order_by is None:
            return {
                "code": 1,
                "message": "sort 参数仅支持热度/时间/评分",
                "data": {},
            }
    else:
        order_by = "-popularity"

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 20))
    except ValueError:
        return {
            "code": 1,
            "message": "page 和 limit 需要是正整数",
            "data": {},
        }

    if page <= 0 or limit <= 0:
        return {
            "code": 1,
            "message": "page 和 limit 需要是正整数",
            "data": {},
        }

    limit = min(limit, 100)

    raw_category = (request.GET.get("category") or "").strip()
    categories = [item.strip() for item in raw_category.split(",") if item.strip()] if raw_category else []

    queryset = base_queryset
    if view_mode == "weekly":
        queryset = queryset.filter(is_weekly_featured=True)
        # 添加基于release_date的本周筛选
        # 获取本周的起始和结束日期
        today = date.today()
        weekday = today.weekday()
        week_start = today - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)

        # 筛选本周内发布的动漫
        # 找出这周更新的集数
        weekly_episodes = Episode.objects.filter(
            release_date__gte=week_start,
            release_date__lte=week_end
        )

        # 提取有更新的 anime_id
        anime_ids = weekly_episodes.values_list("anime_id", flat=True).distinct()
        queryset = queryset.filter(id__in=anime_ids)
    elif view_mode == "season":
        quarter_param = (request.GET.get("quarter") or "").strip()
        if quarter_param:
            parsed = _parse_quarter_param(quarter_param)
            if parsed:
                year, quarter_text = parsed
               
                quarter_months = {
                    "winter": [1, 2, 3],
                    "spring": [4, 5, 6],
                    "summer": [7, 8, 9],
                    "autumn": [10, 11, 12],
                }
                months = quarter_months.get(quarter_text.lower())
                if months:
                    queryset = queryset.filter(release_date__year=year, release_date__month__in=months)
        else:
            # 如果没有指定季度，获取当前季度
            year, quarter = get_current_season_year_and_quarter()
            quarter_months = {
                "winter": [1, 2, 3],
                "spring": [4, 5, 6],
                "summer": [7, 8, 9],
                "autumn": [10, 11, 12],
            }
            months = quarter_months.get(quarter.lower())
            if months:
                queryset = queryset.filter(release_date__year=year, release_date__month__in=months)

    if categories:
        q_objects = [
            Q(genres__contains=[category_name])
            for category_name in categories
        ]
        combined = reduce(lambda acc, curr: acc | curr, q_objects)
        queryset = queryset.filter(combined)

    queryset = queryset.order_by(order_by)

    paginator = Paginator(queryset, limit)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)
    anime_list = list(page_obj.object_list)

    anime_ids = [anime.id for anime in anime_list]
    latest_episode_map = {}
    if view_mode == "weekly" and anime_ids:
        episodes = (
            Episode.objects.filter(anime_id__in=anime_ids)
            .order_by("-episode_number", "-id")
        )
        for ep in episodes:
            if ep.anime_id not in latest_episode_map:
                latest_episode_map[ep.anime_id] = ep

    user = _authenticate_user_if_possible(request)
    followed_ids = set()
    if user and anime_ids and view_mode == "weekly":
        followed_ids = set(
            WatchStatus.objects.filter(user=user, anime_id__in=anime_ids).values_list("anime_id", flat=True)
        )

    results = []
    for anime in anime_list:
        latest_episode = latest_episode_map.get(anime.id)
        episode_number = latest_episode.episode_number if latest_episode else None
        episode_day = _weekday_label(getattr(latest_episode, "release_date", None))
        results.append(
            {
                "id": anime.id,
                "title": anime.title,
                "cover": resolve_cover_url(anime),
                "rating": anime.rating,
                "popularity": anime.popularity,
                "summary": anime.description,
                "time": anime.updated_at.isoformat() if anime.updated_at else None,
                "category": anime.genres or [],
                "isAdmin": anime.is_admin,
                "quarter": _convert_quarter_value(anime),
                "episode_update": episode_number,
                "update_day": episode_day,
                "is_followed": anime.id in followed_ids,
            }
        )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "list": results,
            "pagination": {
                "page": page_obj.number if paginator.count else page,
                "limit": limit,
                "total": paginator.count,
                "pages": paginator.num_pages,
            },
            "sort": raw_sort or "热度",
            "category_filter": categories,
        },
    }



QUARTER_NUM_TO_TEXT = {1: "winter",2: "spring", 3: "summer", 4: "autumn" }
QUARTER_TEXT_TO_NUM = {value: key for key, value in QUARTER_NUM_TO_TEXT.items()}
WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _parse_quarter_param(raw_value: str) -> Optional[tuple[int, str]]:
    try:
        year_str, quarter_str = raw_value.split("-", 1)
        year = int(year_str)
        quarter_num = int(quarter_str)
        quarter_text = QUARTER_NUM_TO_TEXT.get(quarter_num)
        if quarter_text is None:
            return None
        return year, quarter_text
    except Exception:
        return None


def _convert_quarter_value(anime: Anime) -> Optional[str]:
    """根据anime的release_date计算季度"""
    if not anime.release_date:
        return None

    # 新的季度划分：spring(1,2,3), summer(4,5,6), autumn(7,8,9), winter(10,11,12)
    month = anime.release_date.month
    if month >= 1 and month <= 3:
        quarter_num = 1  # spring
    elif month >= 4 and month <= 6:
        quarter_num = 2  # summer
    elif month >= 7 and month <= 9:
        quarter_num = 3  # autumn
    else:  # month >= 10 and month <= 12
        quarter_num = 4  # winter

    year = anime.release_date.year

    return f"{year}-{quarter_num}"


def _weekday_label(date_obj):
    if not date_obj:
        return ""
    try:
        return WEEKDAY_LABELS[date_obj.weekday()]
    except Exception:
        return ""


def _authenticate_user_if_possible(request):
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        return user

    # 尝试从 Django 原始 request 中获取 session 登录用户
    raw_request = getattr(request, "_request", None)
    if raw_request is not None:
        raw_user = getattr(raw_request, "user", None)
        if getattr(raw_user, "is_authenticated", False):
            return raw_user

    authenticator = JWTAuthentication()
    try:
        auth_result = authenticator.authenticate(request)
    except (AuthenticationFailed, InvalidToken):
        return None
    if not auth_result:
        return None
    return auth_result[0]
