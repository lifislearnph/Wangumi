from django.core.management.base import BaseCommand

from wangumi_app.services.weekly_sync_service import sync_weekly_collections


class Command(BaseCommand):
    help = "同步周合集数据（调用 Anilist 数据源并更新 Anime.is_weekly_featured）"

    def handle(self, *args, **options):
        success, stats = sync_weekly_collections()
        created = stats.get("created", 0) if stats else 0
        updated = stats.get("updated", 0) if stats else 0

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"周合集同步完成：created={created}, updated={updated}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR("周合集同步失败，请查看 wangumi_app.models.SyncLog")
            )
