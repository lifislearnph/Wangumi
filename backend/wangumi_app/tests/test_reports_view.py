"""
举报系统测试文件
测试评论举报的提交、查询举报状态等功能
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import (
    Anime, Comment, Report, UserProfile
)


class ReportViewTests(TestCase):
    """举报功能测试"""

    def setUp(self):
        """测试数据准备"""
        self.client = Client()

        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@test.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="user2@test.com",
            password="testpass123"
        )
        self.user3 = User.objects.create_user(
            username="testuser3",
            email="user3@test.com",
            password="testpass123"
        )

        # 创建用户档案
        UserProfile.objects.create(user=self.user1, cellphone="13800000001")
        UserProfile.objects.create(user=self.user2, cellphone="13800000002")
        UserProfile.objects.create(user=self.user3, cellphone="13800000003")

        # 生成JWT token
        self.refresh_token1 = RefreshToken.for_user(self.user1)
        self.access_token1 = str(self.refresh_token1.access_token)

        self.refresh_token2 = RefreshToken.for_user(self.user2)
        self.access_token2 = str(self.refresh_token2.access_token)

        # 创建测试番剧
        self.anime = Anime.objects.create(
            title="测试番剧",
            title_cn="测试番剧中文",
            description="这是一个测试番剧",
            rating=8.5,
            popularity=100
        )

        # 创建测试评论（被举报的评论）
        self.comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=8,
            content="这是一条将被举报的评论",
            scope='ANIME'
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_report_comment_success_spam(self):
        """测试成功举报评论 - 垃圾广告"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "SPAM",
            "reason": "这是垃圾广告内容"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 201)
        self.assertEqual(data['message'], "举报提交成功")

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['comment_id'], self.comment.id)
        self.assertEqual(response_data['category'], "SPAM")
        self.assertEqual(response_data['category_display'], "垃圾广告")
        self.assertEqual(response_data['reason'], "这是垃圾广告内容")
        self.assertEqual(response_data['status'], "PENDING")
        self.assertEqual(response_data['status_display'], "待处理")
        self.assertIsNotNone(response_data['report_id'])
        self.assertIsNotNone(response_data['created_at'])

        # 验证数据库中的记录
        report = Report.objects.get(reporter=self.user2, content_type=ContentType.objects.get_for_model(Comment))
        self.assertEqual(report.category, "SPAM")
        self.assertEqual(report.reason, "这是垃圾广告内容")
        self.assertEqual(report.status, "PENDING")
        self.assertEqual(report.object_id, self.comment.id)

    def test_report_comment_success_harassment(self):
        """测试成功举报评论 - 违法违规"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "HARASSMENT",
            "reason": "包含违法违规内容"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['category_display'], "违法违规")

    def test_report_comment_success_inappropriate(self):
        """测试成功举报评论 - 人身攻击"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "INAPPROPRIATE",
            "reason": "人身攻击言论"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['category_display'], "人身攻击")

    def test_report_comment_success_spoiler(self):
        """测试成功举报评论 - 剧透内容"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "SPOILER",
            "reason": "包含剧透内容"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['category_display'], "剧透内容")

    def test_report_comment_success_other(self):
        """测试成功举报评论 - 其他"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "OTHER",
            "reason": "其他违规内容"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['category_display'], "其他")

    def test_report_comment_without_reason(self):
        """测试举报评论时不提供补充说明"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "SPAM"
            # 没有提供 reason
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['reason'], "")  # 默认为空字符串

    def test_report_comment_missing_category(self):
        """测试举报评论缺少分类"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "reason": "没有分类的举报"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("举报分类不能为空", data['message'])

    def test_report_comment_invalid_category(self):
        """测试举报评论使用无效分类"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "INVALID_CATEGORY",
            "reason": "无效分类测试"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("举报分类必须是以下之一", data['message'])

        # 验证返回的有效分类列表
        valid_categories = data['data']['valid_categories']
        category_values = [cat['value'] for cat in valid_categories]
        expected_categories = ['SPAM', 'HARASSMENT', 'INAPPROPRIATE', 'SPOILER', 'OTHER']
        self.assertEqual(sorted(category_values), sorted(expected_categories))

    def test_report_comment_reason_too_long(self):
        """测试举报评论补充说明过长"""
        client = self.get_authenticated_client(self.access_token2)

        # 创建超过500字符的说明
        long_reason = "a" * 501
        report_data = {
            "category": "SPAM",
            "reason": long_reason
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("补充说明不能超过500字符", data['message'])

    def test_report_comment_max_reason_length(self):
        """测试举报评论最大长度补充说明"""
        client = self.get_authenticated_client(self.access_token2)

        # 创建正好500字符的说明
        max_reason = "a" * 500
        report_data = {
            "category": "SPAM",
            "reason": max_reason
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['data']['reason'], max_reason)

    def test_report_nonexistent_comment(self):
        """测试举报不存在的评论"""
        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "SPAM",
            "reason": "举报不存在的评论"
        }

        response = client.post(
            '/api/comments/99999/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_report_unauthorized(self):
        """测试未认证用户举报评论"""
        report_data = {
            "category": "SPAM",
            "reason": "未认证用户举报"
        }

        response = self.client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_report_invalid_json(self):
        """测试发送无效JSON格式"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data="invalid json",
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("请求体格式错误", data['message'])

    def test_duplicate_report_same_comment(self):
        """测试重复举报同一条评论"""
        client = self.get_authenticated_client(self.access_token2)

        # 第一次举报
        report_data1 = {
            "category": "SPAM",
            "reason": "第一次举报"
        }

        response1 = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data1),
            content_type='application/json'
        )

        self.assertEqual(response1.status_code, 201)

        # 第二次举报（应该失败）
        report_data2 = {
            "category": "HARASSMENT",
            "reason": "第二次举报"
        }

        response2 = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data2),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 400)
        data = response2.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("您已经举报过该内容", data['message'])

        # 验证返回的信息是第一次举报的信息
        response_data = data['data']
        self.assertEqual(response_data['previous_category'], "SPAM")
        self.assertEqual(response_data['previous_reason'], "第一次举报")
        self.assertIsNotNone(response_data['existing_report_id'])
        self.assertIsNotNone(response_data['submitted_at'])

        # 验证数据库中只有一个举报记录
        reports = Report.objects.filter(
            reporter=self.user2,
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.comment.id
        )
        self.assertEqual(reports.count(), 1)

    def test_different_users_report_same_comment(self):
        """测试不同用户举报同一条评论"""
        # user2 举报
        client2 = self.get_authenticated_client(self.access_token2)
        report_data2 = {
            "category": "SPAM",
            "reason": "user2的举报"
        }

        response2 = client2.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data2),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 201)

        # user3 举报
        client3 = self.get_authenticated_client(str(RefreshToken.for_user(self.user3).access_token))
        report_data3 = {
            "category": "HARASSMENT",
            "reason": "user3的举报"
        }

        response3 = client3.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data3),
            content_type='application/json'
        )

        self.assertEqual(response3.status_code, 201)

        # 验证数据库中有两个举报记录
        reports = Report.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.comment.id
        )
        self.assertEqual(reports.count(), 2)

    def test_user_report_own_comment(self):
        """测试用户举报自己的评论"""
        client = self.get_authenticated_client(self.access_token1)

        report_data = {
            "category": "SPAM",
            "reason": "举报自己的评论"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        # 系统应该允许用户举报自己的评论（虽然在业务逻辑上不太合理）
        self.assertEqual(response.status_code, 201)

    def test_get_report_status_has_reported(self):
        """测试获取举报状态 - 已举报"""
        # 先创建举报记录
        report = Report.objects.create(
            reporter=self.user2,
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.comment.id,
            category="SPAM",
            reason="测试举报",
            status="PENDING"
        )

        client = self.get_authenticated_client(self.access_token2)
        response = client.get(f'/api/comments/{self.comment.id}/reports/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "success")

        # 验证返回数据
        response_data = data['data']
        self.assertTrue(response_data['has_reported'])
        self.assertEqual(response_data['report_id'], report.id)
        self.assertEqual(response_data['category'], "SPAM")
        self.assertEqual(response_data['category_display'], "垃圾广告")
        self.assertEqual(response_data['reason'], "测试举报")
        self.assertEqual(response_data['status'], "PENDING")
        self.assertEqual(response_data['status_display'], "待处理")
        self.assertIsNotNone(response_data['created_at'])
        self.assertEqual(response_data['comment_id'], self.comment.id)

    def test_get_report_status_not_reported(self):
        """测试获取举报状态 - 未举报"""
        client = self.get_authenticated_client(self.access_token2)
        response = client.get(f'/api/comments/{self.comment.id}/reports/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)

        # 验证返回数据
        response_data = data['data']
        self.assertFalse(response_data['has_reported'])
        self.assertIsNone(response_data['report_id'])
        self.assertIsNone(response_data['category'])
        self.assertIsNone(response_data['category_display'])
        self.assertIsNone(response_data['reason'])
        self.assertIsNone(response_data['status'])
        self.assertIsNone(response_data['status_display'])
        self.assertIsNone(response_data['created_at'])
        self.assertEqual(response_data['comment_id'], self.comment.id)

    def test_get_report_status_nonexistent_comment(self):
        """测试获取不存在评论的举报状态"""
        client = self.get_authenticated_client(self.access_token2)
        response = client.get('/api/comments/99999/reports/')

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_get_report_status_unauthorized(self):
        """测试未认证用户获取举报状态"""
        response = self.client.get(f'/api/comments/{self.comment.id}/reports/')

        self.assertEqual(response.status_code, 401)

    def test_report_workflow_integration(self):
        """测试完整的举报工作流程"""
        client = self.get_authenticated_client(self.access_token2)

        # 1. 获取初始举报状态
        response = client.get(f'/api/comments/{self.comment.id}/reports/')
        self.assertEqual(response.json()['data']['has_reported'], False)

        # 2. 提交举报
        report_data = {
            "category": "SPAM",
            "reason": "工作流程测试举报"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 3. 验证举报后状态
        response = client.get(f'/api/comments/{self.comment.id}/reports/')
        self.assertEqual(response.json()['data']['has_reported'], True)
        self.assertEqual(response.json()['data']['category'], "SPAM")
        self.assertEqual(response.json()['data']['reason'], "工作流程测试举报")

    def test_unicode_content_in_report_reason(self):
        """测试举报原因中的Unicode内容"""
        client = self.get_authenticated_client(self.access_token2)

        unicode_reason = "测试中文举报原因 🚫 特殊内容 🔢"
        report_data = {
            "category": "OTHER",
            "reason": unicode_reason
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 验证Unicode内容被正确保存和返回
        report = Report.objects.get(reporter=self.user2, content_type=ContentType.objects.get_for_model(Comment))
        self.assertEqual(report.reason, unicode_reason)

        response_data = response.json()['data']
        self.assertEqual(response_data['reason'], unicode_reason)

    @patch('wangumi_app.views.reports_view.Report.objects.create')
    def test_report_database_error(self, mock_create):
        """测试举报时数据库错误"""
        mock_create.side_effect = Exception("数据库连接错误")

        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "SPAM",
            "reason": "数据库错误测试"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])

    @patch('wangumi_app.views.reports_view.Comment.objects.get')
    def test_report_comment_query_error(self, mock_get):
        """测试查询评论时数据库错误"""
        mock_get.side_effect = Exception("数据库连接错误")

        client = self.get_authenticated_client(self.access_token2)

        report_data = {
            "category": "SPAM",
            "reason": "查询错误测试"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])


class ReportViewIntegrationTests(TestCase):
    """举报系统集成测试"""

    def setUp(self):
        """测试数据准备"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="integration_user",
            email="integration@test.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, cellphone="13800000123")

        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh_token.access_token)

        self.anime = Anime.objects.create(
            title="集成测试番剧",
            title_cn="集成测试番剧中文",
            rating=8.0,
            popularity=100
        )

        self.comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user,
            score=8,
            content="集成测试评论",
            scope='ANIME'
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_multiple_reports_different_categories(self):
        """测试对同一评论的多种分类举报（不同用户）"""
        users = []
        categories = ['SPAM', 'HARASSMENT', 'INAPPROPRIATE', 'SPOILER', 'OTHER']

        # 创建多个用户，每个用户用不同分类举报
        for i, category in enumerate(categories):
            user = User.objects.create_user(
                username=f"reporter{i}",
                email=f"reporter{i}@test.com",
                password="testpass123"
            )
            UserProfile.objects.create(user=user, cellphone=f"13800000{i:02d}")
            users.append(user)

            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)
            client = self.get_authenticated_client(access_token)

            report_data = {
                "category": category,
                "reason": f"{category}分类举报"
            }

            response = client.post(
                f'/api/comments/{self.comment.id}/reports/',
                data=json.dumps(report_data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 201)

        # 验证所有举报都存在
        reports = Report.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.comment.id
        )
        self.assertEqual(reports.count(), 5)

        # 验证每个分类都有举报
        reported_categories = set(reports.values_list('category', flat=True))
        expected_categories = set(categories)
        self.assertEqual(reported_categories, expected_categories)

    def test_report_consistency_after_comment_update(self):
        """测试评论更新后举报记录的一致性"""
        client = self.get_authenticated_client(self.access_token)

        # 提交举报
        report_data = {
            "category": "SPAM",
            "reason": "原始举报"
        }

        response = client.post(
            f'/api/comments/{self.comment.id}/reports/',
            data=json.dumps(report_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 更新评论内容
        self.comment.content = "更新后的评论内容"
        self.comment.save()

        # 验证举报记录仍然存在且关联正确
        report = Report.objects.get(
            reporter=self.user,
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.comment.id
        )
        self.assertEqual(report.object_id, self.comment.id)

        # 验证举报状态查询仍然正常
        response = client.get(f'/api/comments/{self.comment.id}/reports/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['has_reported'])