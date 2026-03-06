"""Season collection sync service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import requests
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils import timezone

from wangumi_app.models import Anime, SyncLog

logger = logging.getLogger(__name__)

ANILIST_GRAPHQL_API = getattr(settings, "ANILIST_GRAPHQL_API", "https://graphql.anilist.co")
SEASON_QUERY = """
query ($page: Int!, $perPage: Int!, $season: MediaSeason!, $seasonYear: Int!) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { currentPage hasNextPage }
    media(
      type: ANIME
      season: $season
      seasonYear: $seasonYear
      sort: POPULARITY_DESC
    ) {
      id
      title { romaji english native }
      coverImage { extraLarge large medium }
      startDate { year month day }
      status
      episodes
      genres
      siteUrl
    }
  }
}
"""

SEASON_ENUM = {
    "spring": "SPRING",
    "summer": "SUMMER",
    "autumn": "FALL",
    "winter": "WINTER",
}


def get_current_season_year_and_quarter() -> Tuple[int, str]:
    now = datetime.now()
    year = now.year
    month = now.month
    if month in (1, 2, 3):
        quarter = "winter"
    elif month in (4, 5, 6):
        quarter = "spring"
    elif month in (7, 8, 9):
        quarter = "summer"
    else:
        quarter = "autumn"
    return year, quarter


def _format_date(date_dict: Dict[str, Any]) -> str:
    if not date_dict:
        return ""
    year = date_dict.get("year")
    if not year:
        return ""
    month = date_dict.get("month") or 1
    day = date_dict.get("day") or 1
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def fetch_raw_season_data(year: int, quarter: str) -> List[Dict[str, Any]]:
    season = SEASON_ENUM.get(quarter.lower())
    if not season:
        raise ValueError(f"Unsupported quarter: {quarter}")

    page = 1
    per_page = 50
    results: List[Dict[str, Any]] = []

    while True:
        variables = {
            "page": page,
            "perPage": per_page,
            "season": season,
            "seasonYear": year,
        }
        resp = requests.post(
            ANILIST_GRAPHQL_API,
            json={"query": SEASON_QUERY, "variables": variables},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json().get("data", {}).get("Page", {})
        media_list = payload.get("media") or []

        for media in media_list:
            title_info = media.get("title") or {}
            cover_info = media.get("coverImage") or {}
            cover = cover_info.get("extraLarge") or cover_info.get("large") or cover_info.get("medium") or ""
            results.append(
                {
                    "external_id": str(media.get("id")),
                    "title": title_info.get("romaji") or title_info.get("english") or "Unknown Title",
                    "title_cn": title_info.get("native") or title_info.get("romaji") or "",
                    "cover": cover,
                    "status": media.get("status") or "unknown",
                    "total_episodes": media.get("episodes") or 0,
                    "platform": "anilist",
                    "genres": media.get("genres") or [],
                    "airtime": "",
                    "release_date": _format_date(media.get("startDate") or {}),
                }
            )

        if not payload.get("pageInfo", {}).get("hasNextPage"):
            break
        page += 1

    return results


def _normalize_item(item: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    external_id = item.get("external_id") or item.get("id")
    if not external_id:
        raise ValueError(f"missing external_id field: {item}")

    title = item.get("title") or item.get("name") or "Untitled"
    title_cn = item.get("title_cn") or item.get("name_cn") or title
    cover = item.get("cover") or item.get("image") or item.get("cover_url") or ""

    release_date_str = item.get("release_date")
    release_date = parse_date(release_date_str) if release_date_str else None

    defaults: Dict[str, Any] = {
        "title": title,
        "title_cn": title_cn,
        "cover_url": cover,
        "status": item.get("status") or "unknown",
        "total_episodes": item.get("total_episodes") or item.get("episodes") or 0,
        "platform": item.get("platform") or "",
        "genres": item.get("genres") or [],
        "airtime": item.get("airtime") or "",
        "is_season_featured": True,
    }

    if release_date:
        defaults["release_date"] = release_date

    return str(external_id), defaults


@transaction.atomic
def sync_current_season_anime() -> Tuple[bool, Dict[str, Any]]:
    log: SyncLog | None = None
    created, updated = 0, 0

    try:
        log = SyncLog.objects.create(
            job_type=SyncLog.JobType.SEASON,
            sync_type=SyncLog.JobType.SEASON,
            status=SyncLog.Status.PENDING,
            message="Start season sync",
        )

        year, quarter = get_current_season_year_and_quarter()
        raw_list = fetch_raw_season_data(year, quarter)

        Anime.objects.filter(season_year=year, season_quarter=quarter).update(
            is_season_featured=False
        )

        for raw_item in raw_list:
            external_id, defaults = _normalize_item(raw_item)
            defaults.update({
                "season_year": year,
                "season_quarter": quarter,
            })

            anime, is_created = Anime.objects.update_or_create(
                external_id=external_id,
                defaults=defaults,
            )

            created += int(is_created)
            updated += int(not is_created)

        log.status = SyncLog.Status.SUCCESS
        log.success = True
        log.created_count = created
        log.updated_count = updated
        log.message = f"Season sync succeeded created={created}, updated={updated}"
    except Exception as exc:
        if log is None:
            logger.exception("failed to init season sync log")
            raise
        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = str(exc)
        logger.exception("season sync failed")
    finally:
        if log is not None:
            log.finished_at = timezone.now()
            log.save()

    return log.status == SyncLog.Status.SUCCESS, {"log_id": log.id, "created": created, "updated": updated}
