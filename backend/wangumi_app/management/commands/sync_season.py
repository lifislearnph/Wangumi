from django.core.management.base import BaseCommand

from wangumi_app.services.season_sync_service import sync_current_season_anime


class Command(BaseCommand):
    help = "同步季度番数据（调用 Anilist 数据源并更新当季 Anime）"

    def handle(self, *args, **options):
        success, stats = sync_current_season_anime()
        created = stats.get("created", 0) if stats else 0
        updated = stats.get("updated", 0) if stats else 0

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"季度番同步完成：created={created}, updated={updated}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR("季度番同步失败，请查看 wangumi_app.models.SyncLog")
            )
