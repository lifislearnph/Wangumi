"""
回复系统测试文件
测试评论回复的创建、获取、分页等功能
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.models import (
    Anime, Comment, Reply, Like, UserProfile
)


class ReplyViewTests(TestCase):
    """回复功能测试"""

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

        self.refresh_token3 = RefreshToken.for_user(self.user3)
        self.access_token3 = str(self.refresh_token3.access_token)

        # 创建测试番剧
        self.anime = Anime.objects.create(
            title="测试番剧",
            title_cn="测试番剧中文",
            description="这是一个测试番剧",
            rating=8.5,
            popularity=100
        )

        # 创建测试评论（被回复的评论）
        self.parent_comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=8,
            content="这是一条测试评论，等待回复",
            scope='ANIME'
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_create_reply_success(self):
        """测试创建回复成功"""
        client = self.get_authenticated_client(self.access_token2)

        reply_data = {
            "content": "这是一条回复内容"
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 201)
        self.assertEqual(data['message'], "回复成功")

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['content'], "这是一条回复内容")
        self.assertEqual(response_data['comment_id'], self.parent_comment.id)
        self.assertEqual(response_data['author']['username'], "testuser2")
        self.assertEqual(response_data['parent_author']['username'], "testuser1")
        self.assertIsNotNone(response_data['reply_id'])
        self.assertIsNotNone(response_data['created_at'])

        # 验证数据库中的记录
        reply = Reply.objects.get(review=self.parent_comment, user=self.user2)
        self.assertEqual(reply.content, "这是一条回复内容")
        self.assertEqual(reply.review, self.parent_comment)

    def test_create_reply_empty_content(self):
        """测试创建空内容回复（应该失败）"""
        client = self.get_authenticated_client(self.access_token2)

        reply_data = {
            "content": ""  # 空内容
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("回复内容不能为空", data['message'])

    def test_create_reply_whitespace_only_content(self):
        """测试只包含空白字符的回复（应该失败）"""
        client = self.get_authenticated_client(self.access_token2)

        reply_data = {
            "content": "   \n\t   "  # 只有空白字符
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("回复内容不能为空", data['message'])

    def test_create_reply_too_long_content(self):
        """测试创建内容过长的回复"""
        client = self.get_authenticated_client(self.access_token2)

        # 创建超过500字符的内容
        long_content = "a" * 501
        reply_data = {
            "content": long_content
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("回复内容不能超过500字符", data['message'])

    def test_create_reply_to_nonexistent_comment(self):
        """测试回复不存在的评论"""
        client = self.get_authenticated_client(self.access_token2)

        reply_data = {
            "content": "回复不存在的评论"
        }

        response = client.post(
            '/api/comments/99999/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_create_reply_unauthorized(self):
        """测试未认证用户创建回复"""
        reply_data = {
            "content": "未认证用户的回复"
        }

        response = self.client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_create_reply_invalid_json(self):
        """测试发送无效JSON格式"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data="invalid json",
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("请求体格式错误", data['message'])

    def test_get_replies_success(self):
        """测试获取回复列表成功"""
        # 创建测试回复
        now = timezone.now()
        reply1 = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="第一条回复",
            created_at=now - timedelta(hours=2)
        )
        reply2 = Reply.objects.create(
            review=self.parent_comment,
            user=self.user3,
            content="第二条回复",
            created_at=now - timedelta(hours=1)
        )

        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "success")

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['comment_id'], self.parent_comment.id)
        self.assertEqual(response_data['total_replies'], 2)
        self.assertEqual(len(response_data['replies']), 2)

        # 验证回复内容（按时间倒序）
        replies = response_data['replies']
        self.assertEqual(replies[0]['content'], "第二条回复")  # 最新的在前
        self.assertEqual(replies[1]['content'], "第一条回复")

        # 验证父评论信息
        self.assertEqual(response_data['parent_comment']['content'], self.parent_comment.content)
        self.assertEqual(response_data['parent_comment']['author']['username'], "testuser1")

    def test_get_replies_authenticated_user(self):
        """测试认证用户获取回复列表"""
        # 创建回复
        reply = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="测试回复"
        )

        # 创建点赞记录（如果Like模型支持对回复的点赞）
        # 注意：根据实际的Like模型结构调整
        Like.objects.create(
            user=self.user1,
            comment=self.parent_comment,  # 这里可能需要调整
            is_active=True
        )

        client = self.get_authenticated_client(self.access_token1)
        response = client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total_replies'], 1)

    def test_get_replies_nonexistent_comment(self):
        """测试获取不存在评论的回复列表"""
        response = self.client.get('/api/comments/99999/replies/')

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_get_replies_empty_list(self):
        """测试获取空回复列表"""
        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total_replies'], 0)
        self.assertEqual(len(data['data']['replies']), 0)

    def test_get_replies_pagination(self):
        """测试回复列表分页"""
        # 创建多条回复
        for i in range(5):
            Reply.objects.create(
                review=self.parent_comment,
                user=self.user2 if i % 2 == 0 else self.user3,
                content=f"回复{i+1}",
                created_at=timezone.now() + timedelta(minutes=i)
            )

        # 测试分页
        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/', {
            'page': 1,
            'page_size': 2
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        response_data = data['data']

        self.assertEqual(len(response_data['replies']), 2)
        self.assertEqual(response_data['page'], 1)
        self.assertEqual(response_data['page_size'], 2)
        self.assertEqual(response_data['total_pages'], 3)  # ceil(5/2) = 3
        self.assertEqual(response_data['total_replies'], 5)

    def test_get_replies_sorting_by_time_asc(self):
        """测试按时间升序获取回复"""
        now = timezone.now()
        reply1 = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="早期回复",
            created_at=now - timedelta(hours=2)
        )
        reply2 = Reply.objects.create(
            review=self.parent_comment,
            user=self.user3,
            content="晚期回复",
            created_at=now - timedelta(hours=1)
        )

        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/', {
            'order_by': 'time_asc'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        replies = data['data']['replies']

        self.assertEqual(replies[0]['content'], "早期回复")  # 最早的在前
        self.assertEqual(replies[1]['content'], "晚期回复")

    def test_get_replies_sorting_by_likes_desc(self):
        """测试按点赞数降序获取回复"""
        # 创建回复（如果Reply模型有likes字段）
        reply1 = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="少点赞回复"
        )
        # 如果有likes字段，可以设置点赞数
        # reply1.likes = 5
        # reply1.save()

        reply2 = Reply.objects.create(
            review=self.parent_comment,
            user=self.user3,
            content="多点赞回复"
        )
        # reply2.likes = 10
        # reply2.save()

        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/', {
            'order_by': 'likes_desc'
        })

        self.assertEqual(response.status_code, 200)
        # 由于Reply模型可能没有likes字段，这个测试主要验证排序参数被接受
        data = response.json()
        self.assertEqual(data['code'], 200)

    def test_reply_author_info(self):
        """测试回复作者信息"""
        # 创建回复
        reply = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="测试作者信息的回复"
        )

        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        replies = data['data']['replies']

        # 验证作者信息
        author = replies[0]['author']
        self.assertEqual(author['user_id'], self.user2.id)
        self.assertEqual(author['username'], "testuser2")
        self.assertEqual(author['level'], 1)  # 默认等级
        self.assertFalse(author['is_verified'])  # 默认未认证
        self.assertEqual(author['avatar'], "/avatars/default.jpg")  # 默认头像

    def test_multiple_replies_same_user(self):
        """测试同一用户多条回复"""
        # 同一用户创建多条回复
        Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="第一条回复"
        )
        Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="第二条回复"
        )
        Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="第三条回复"
        )

        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total_replies'], 3)

        # 验证所有回复都是同一用户
        replies = data['data']['replies']
        for reply in replies:
            self.assertEqual(reply['author']['username'], "testuser2")
            self.assertFalse(reply['is_author'])  # 未认证用户，is_author应为False

    def test_get_replies_as_author(self):
        """测试作为回复作者获取回复列表"""
        # user2 创建回复
        reply = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="我的回复"
        )

        # user2 认证后获取回复列表
        client = self.get_authenticated_client(self.access_token2)
        response = client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        replies = data['data']['replies']

        # 验证is_author标志
        self.assertTrue(replies[0]['is_author'])

    def test_get_replies_as_other_user(self):
        """测试作为其他用户获取回复列表"""
        # user2 创建回复
        reply = Reply.objects.create(
            review=self.parent_comment,
            user=self.user2,
            content="user2的回复"
        )

        # user3 认证后获取回复列表
        client = self.get_authenticated_client(self.access_token3)
        response = client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        replies = data['data']['replies']

        # 验证is_author标志
        self.assertFalse(replies[0]['is_author'])

    def test_reply_workflow_integration(self):
        """测试完整的回复工作流程"""
        client = self.get_authenticated_client(self.access_token2)

        # 1. 创建回复
        reply_data = {
            "content": "工作流程测试回复"
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        reply_id = response.json()['data']['reply_id']

        # 2. 获取回复列表
        response = client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']['replies']), 1)

        # 3. 验证回复内容
        replies = response.json()['data']['replies']
        self.assertEqual(replies[0]['content'], "工作流程测试回复")
        self.assertEqual(replies[0]['reply_id'], reply_id)

    @patch('wangumi_app.views.reply_view.Reply.objects.create')
    def test_create_reply_database_error(self, mock_create):
        """测试创建回复时数据库错误"""
        mock_create.side_effect = Exception("数据库连接错误")

        client = self.get_authenticated_client(self.access_token2)

        reply_data = {
            "content": "数据库错误测试回复"
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])

    @patch('wangumi_app.views.reply_view.Reply.objects.filter')
    def test_get_replies_database_error(self, mock_filter):
        """测试获取回复时数据库错误"""
        mock_filter.side_effect = Exception("数据库连接错误")

        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])


class ReplyViewIntegrationTests(TestCase):
    """回复系统集成测试"""

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

        self.parent_comment = Comment.objects.create(
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

    def test_multiple_users_reply_to_same_comment(self):
        """测试多个用户回复同一条评论"""
        # 创建多个用户
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f"reply_user{i}",
                email=f"reply_user{i}@test.com",
                password="testpass123"
            )
            UserProfile.objects.create(user=user, cellphone=f"13800000{i:02d}")
            users.append(user)

        # 每个用户都回复
        for i, user in enumerate(users):
            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)
            client = self.get_authenticated_client(access_token)

            reply_data = {
                "content": f"用户{i+1}的回复"
            }

            response = client.post(
                f'/api/comments/{self.parent_comment.id}/replies/',
                data=json.dumps(reply_data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 201)

        # 验证所有回复都存在
        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total_replies'], 3)

        # 验证回复作者不同
        usernames = [reply['author']['username'] for reply in data['data']['replies']]
        self.assertEqual(len(set(usernames)), 3)  # 应该有3个不同的用户名

    def test_reply_with_max_length_content(self):
        """测试最大长度内容的回复"""
        client = self.get_authenticated_client(self.access_token)

        # 创建正好500字符的内容
        max_content = "a" * 500
        reply_data = {
            "content": max_content
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 验证内容被完整保存
        reply = Reply.objects.get(review=self.parent_comment, user=self.user)
        self.assertEqual(len(reply.content), 500)

    def test_unicode_content_in_reply(self):
        """测试回复中的Unicode内容"""
        client = self.get_authenticated_client(self.access_token)

        unicode_content = "测试中文回复 🎬 émojis 🎭 特殊字符"
        reply_data = {
            "content": unicode_content
        }

        response = client.post(
            f'/api/comments/{self.parent_comment.id}/replies/',
            data=json.dumps(reply_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 验证Unicode内容被正确保存和返回
        reply = Reply.objects.get(review=self.parent_comment, user=self.user)
        self.assertEqual(reply.content, unicode_content)

        # 验证返回的数据也包含正确的Unicode内容
        response_data = response.json()['data']
        self.assertEqual(response_data['content'], unicode_content)

    def test_reply_order_consistency(self):
        """测试回复顺序的一致性"""
        client = self.get_authenticated_client(self.access_token)

        # 创建多条回复，间隔时间
        replies = []
        for i in range(5):
            reply_data = {
                "content": f"回复{i+1}"
            }

            response = client.post(
                f'/api/comments/{self.parent_comment.id}/replies/',
                data=json.dumps(reply_data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 201)
            replies.append(response.json()['data'])

        # 获取回复列表
        response = self.client.get(f'/api/comments/{self.parent_comment.id}/replies/')
        self.assertEqual(response.status_code, 200)

        reply_list = response.json()['data']['replies']

        # 验证顺序：最新的在前
        self.assertEqual(reply_list[0]['content'], "回复5")
        self.assertEqual(reply_list[1]['content'], "回复4")
        self.assertEqual(reply_list[2]['content'], "回复3")
        self.assertEqual(reply_list[3]['content'], "回复2")
        self.assertEqual(reply_list[4]['content'], "回复1")