"""Weekly collection service with deterministic selection rules."""

from datetime import timedelta
from typing import List, Tuple

from django.db import transaction
from django.utils import timezone

from wangumi_app.models import Anime, SyncLog

DEFAULT_WEEKLY_LIMIT = 12


def _select_weekly_candidates(now, limit: int) -> Tuple[List[Anime], str]:
    """
    Select up to `limit` anime for inclusion in the weekly collection.

    Preference order:
    1. Titles updated within the last 7 days ordered by rating/popularity.
    2. Fallback to current season featured titles if no recent activity exists.
    """
    week_start = now - timedelta(days=7)

    recent_qs = (
        Anime.objects.filter(
            updated_at__gte=week_start,
            is_banned=False,
        )
        .order_by("-rating", "-popularity", "-updated_at")
    )
    recent_list = list(recent_qs[:limit])
    if recent_list:
        return recent_list, "recent updates"

    fallback_qs = (
        Anime.objects.filter(
            is_season_featured=True,
            is_banned=False,
        )
        .order_by("-rating", "-popularity", "-created_at")
    )
    return list(fallback_qs[:limit]), "season featured"


@transaction.atomic
def generate_weekly_collection(limit: int = DEFAULT_WEEKLY_LIMIT):
    """
    Generate weekly collections with a two-phase strategy:
    - Prefer hot titles updated this week.
    - Fall back to current season picks if there are not enough updates.
    """
    log = SyncLog.objects.create(
        job_type=SyncLog.JobType.WEEKLY,
        sync_type=SyncLog.JobType.WEEKLY,
        status=SyncLog.Status.PENDING,
        message="开始生成周合集",
    )
    try:
        now = timezone.now()
        selection, strategy = _select_weekly_candidates(now, limit)
        selected_ids = [anime.id for anime in selection]

        Anime.objects.filter(is_weekly_featured=True).update(is_weekly_featured=False)
        if selected_ids:
            Anime.objects.filter(id__in=selected_ids).update(is_weekly_featured=True)

        count = len(selection)
        log.status = SyncLog.Status.SUCCESS
        log.success = True
        log.created_count = count
        log.updated_count = count
        log.message = f"周合集生成成功，策略={strategy}，推荐数量：{count}"
    except Exception as exc:
        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = f"周合集生成失败：{exc!r}"
        raise
    finally:
        log.finished_at = timezone.now()
        log.save()
