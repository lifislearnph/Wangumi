from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.contrib.auth.models import User

from wangumi_app.models import Anime, SyncLog, Episode, WatchStatus
from wangumi_app.services.weekly_sync_service import sync_weekly_collections

class WeeklySyncApiViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="weekly_user", password="pass123")
        # 计算本周的日期范围
        today = date.today()
        weekday = today.weekday()
        week_start = today - timedelta(days=weekday)

        self.weekly_anime = Anime.objects.create(
            title="Weekly Show",
            title_cn="周番",
            rating=8.5,
            popularity=100,
            is_weekly_featured=True,  # 周度推荐动漫
            genres=["Action"],
            release_date=week_start,  # 设置release_date在本周内
        )
        Episode.objects.create(
            anime=self.weekly_anime,
            episode_number=9,
            title="Ep9",
            release_date=week_start,
        )
        WatchStatus.objects.create(user=self.user, anime=self.weekly_anime, status="WATCHING")
        # 创建一个不在本周的动漫（应该不会被筛选出来）
        Anime.objects.create(
            title="Regular Show",
            title_cn="普通番",
            rating=7.0,
            popularity=20,
            release_date=date(2024, 1, 1),  # 很久以前的日期
        )

    def test_weekly_get_returns_featured_list(self):
        self.client.force_login(self.user)
        response = self.client.get("/api/sync/weekly/", {"include_followed": "true"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        data_list = payload["data"]["list"]
        self.assertEqual(len(data_list), 1)
        item = data_list[0]
        self.assertEqual(item["title"], "Weekly Show")
        self.assertEqual(item["episode_update"], 9)
        self.assertEqual(item["update_day"], "周一")
        self.assertTrue(item["is_followed"])


class SeasonSyncApiViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.spring = Anime.objects.create(
            title="Spring Anime",
            title_cn="春番",
            release_date=date(2025, 2, 1),  # 春季（1-3月）
            is_season_featured=True,  # 季度推荐动漫
            popularity=300,
            genres=["Drama"],
        )
        Anime.objects.create(
            title="Winter Anime",
            title_cn="冬番",
            release_date=date(2024, 12, 1),  # 冬季（10-12月）
            is_season_featured=True,
            popularity=200,
        )

    def test_season_get_filters_by_quarter(self):
        response = self.client.get("/api/sync/season/", {"quarter": "2025-1"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["Spring Anime"])
        self.assertEqual(payload["data"]["list"][0]["quarter"], "2025-1")
