"""Season collection generation service."""

from django.db import transaction
from django.utils import timezone

from wangumi_app.models import Anime, SyncLog
from wangumi_app.services.season_sync_service import get_current_season_year_and_quarter


@transaction.atomic
def generate_season_collection() -> None:
    """
    Mark all anime that belong to the current season as season-featured.

    The rule is intentionally simple: everything in the current season
    (year + quarter) becomes part of the collection.
    """
    log = SyncLog.objects.create(
        job_type=SyncLog.JobType.SEASON,
        sync_type=SyncLog.JobType.SEASON,
        status=SyncLog.Status.PENDING,
        message="Start generating season collection",
    )

    try:
        year, quarter = get_current_season_year_and_quarter()
        current_season_qs = Anime.objects.filter(season_year=year, season_quarter=quarter)

        # Clear previous featured flags that no longer belong to the active season.
        (
            Anime.objects.filter(is_season_featured=True)
            .exclude(season_year=year, season_quarter=quarter)
            .update(is_season_featured=False)
        )

        collection_count = current_season_qs.count()
        marked_rows = current_season_qs.update(is_season_featured=True)

        log.status = SyncLog.Status.SUCCESS
        log.success = True
        log.created_count = collection_count
        log.updated_count = marked_rows
        log.message = (
            f"Season collection generated for {year} {quarter}. "
            f"entries={collection_count}"
        )
    except Exception as exc:
        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = f"Season collection generation failed: {exc!r}"
        raise
    finally:
        log.finished_at = timezone.now()
        log.save()
