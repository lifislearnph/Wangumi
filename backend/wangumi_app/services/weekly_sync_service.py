# backend/wangumi_app/services/weekly_sync_service.py

from __future__ import annotations

import logging
from typing import Dict, Any, Tuple, List

import requests
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils import timezone

from wangumi_app.models import Anime, SyncLog

logger = logging.getLogger(__name__)

ANILIST_GRAPHQL_API = getattr(settings, "ANILIST_GRAPHQL_API", "https://graphql.anilist.co")
TRENDING_QUERY = """
query ($page: Int!, $perPage: Int!) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { currentPage hasNextPage }
    media(
      type: ANIME
      sort: TRENDING_DESC
      status_in: [RELEASING, NOT_YET_RELEASED]
    ) {
      id
      title { romaji english native }
      coverImage { extraLarge large medium }
      episodes
      genres
      nextAiringEpisode { airingAt episode }
      startDate { year month day }
      siteUrl
    }
  }
}
"""


def fetch_weekly_data() -> Dict[str, Any]:
    """Fetch trending anime from Anilist GraphQL as weekly collection."""
    resp = requests.post(
        ANILIST_GRAPHQL_API,
        json={"query": TRENDING_QUERY, "variables": {"page": 1, "perPage": 20}},
        timeout=10,
    )
    resp.raise_for_status()
    page = resp.json().get("data", {}).get("Page", {})
    media_list = page.get("media") or []

    def _format_date(date_dict: Dict[str, Any]) -> str:
        if not date_dict:
            return ""
        year = date_dict.get("year")
        if not year:
            return ""
        month = date_dict.get("month") or 1
        day = date_dict.get("day") or 1
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"

    def _transform(media: Dict[str, Any]) -> Dict[str, Any]:
        title_data = media.get("title") or {}
        cover_info = media.get("coverImage") or {}
        cover = cover_info.get("extraLarge") or cover_info.get("large") or cover_info.get("medium") or ""
        return {
            "external_id": str(media.get("id")),
            "title": title_data.get("romaji") or title_data.get("english") or "Unknown Title",
            "title_cn": title_data.get("native") or title_data.get("romaji") or "",
            "cover": cover,
            "platform": "anilist",
            "genres": media.get("genres") or [],
            "airtime": "",
            "total_episodes": media.get("episodes") or 0,
            "release_date": _format_date(media.get("startDate") or {}),
        }

    cover_preview = ""
    if media_list:
        cover_meta = media_list[0].get("coverImage") or {}
        cover_preview = (
            cover_meta.get("extraLarge")
            or cover_meta.get("large")
            or cover_meta.get("medium")
            or ""
        )

    collection = {
        "title": "Anilist Trending Weekly",
        "platform": "anilist",
        "cover": cover_preview,
        "items": [_transform(media) for media in media_list],
    }
    return {"collections": [collection]}


def _normalize_item(item: Dict[str, Any], collection: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    external_id = item.get("external_id") or item.get("id")
    if not external_id:
        raise ValueError(f"missing external_id field: {item}")

    title = item.get("title") or item.get("name") or item.get("name_cn") or "Untitled"
    title_cn = item.get("title_cn") or item.get("name_cn") or title

    cover = item.get("cover") or item.get("image") or collection.get("cover") or ""
    platform = item.get("platform") or collection.get("platform") or ""

    release_date_str = item.get("release_date")
    release_date = parse_date(release_date_str) if release_date_str else None

    defaults = {
        "title": title,
        "title_cn": title_cn,
        "cover_url": cover or "",
        "platform": platform,
        "genres": item.get("genres") or [],
        "airtime": item.get("airtime") or "",
        "total_episodes": item.get("total_episodes") or item.get("episodes") or 0,
        "is_weekly_featured": True,
    }

    if release_date:
        defaults["release_date"] = release_date

    return str(external_id), defaults


def _iter_items(collections: List[Dict[str, Any]]):
    for collection in collections:
        items = collection.get("items") or collection.get("anime_list") or []
        for raw_item in items:
            yield collection, raw_item


def sync_weekly_collections() -> Tuple[bool, Dict[str, Any]]:
    """Weekly sync: consume GraphQL data and update Anime flags."""
    log = SyncLog.objects.create(
        job_type=SyncLog.JobType.WEEKLY,
        sync_type=SyncLog.JobType.WEEKLY,
        status=SyncLog.Status.PENDING,
        message="Start weekly sync",
    )
    created, updated = 0, 0
    try:
        payload = fetch_weekly_data()
        collections = payload.get("collections", [])

        for collection, raw_item in _iter_items(collections):
            try:
                external_id, defaults = _normalize_item(raw_item, collection)
            except Exception as exc:  # pragma: no cover
                logger.exception("skip invalid item", extra={"item": raw_item, "reason": str(exc)})
                continue

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
        log.message = f"Weekly sync finished created={created}, updated={updated}"
    except Exception as exc:
        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = str(exc)
        logger.exception("weekly sync failed")

    log.finished_at = timezone.now()
    log.save()
    return (
        log.status == SyncLog.Status.SUCCESS,
        {"log_id": log.id, "created": created, "updated": updated}
    )
