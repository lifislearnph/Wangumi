<template>
  <div class="review-list">
    <!-- 评价列表 -->
    <div v-if="reviews && reviews.length > 0" class="reviews-container">
      <div
        v-for="review in reviews"
        :key="review.reviewId || review.createdAt"
        class="review-item"
      >
        <!-- 评价主体 -->
        <div class="review-main">
          <img
            :src="getUserAvatar(review.avatar)"
            :alt="review.user"
            class="review-avatar"
          />

          <div class="review-content">
            <!-- 评价头部信息 -->
            <div class="review-header-info">
              <span class="review-user">{{ review.user || '匿名用户' }}</span>

              <!-- 显示评分 -->
              <div class="review-rating" v-if="review.score">
                <StarRating :modelValue="review.score" :readonly="true" />
              </div>

              <span class="review-time">{{ formatTime(review.createdAt) }}</span>
            </div>

            <!-- 评价文本 -->
            <p class="review-text" v-if="review.content">
              {{ review.content }}
            </p>
            <p class="review-text no-comment" v-else>
              <i class="fas fa-comment-slash"></i>
              该用户仅评分，未留言
            </p>

            <!-- 评价操作 -->
            <div class="review-actions">
              <button
                class="action-btn like-btn"
                :class="{ liked: review.isLiked }"
                @click="handleLike(review)"
              >
                <i class="fas fa-heart"></i>
                <span>{{ review.likes || 0 }}</span>
              </button>

              <button
                class="action-btn reply-btn"
                @click="toggleReplyForm(review)"
              >
                <i class="fas fa-reply"></i>
                <span>回复 ({{ review.replyCount || 0 }})</span>
              </button>

              <!-- 展开/收起回复按钮 -->
              <button
                v-if="(review.replyCount || 0) > 0"
                class="action-btn expand-btn"
                @click="toggleReplies(review)"
              >
                <i
                  class="fas"
                  :class="
                    expandedReviews.includes(review.reviewId || review.createdAt)
                      ? 'fa-chevron-up'
                      : 'fa-chevron-down'
                  "
                ></i>
                <span>{{
                  expandedReviews.includes(review.reviewId || review.createdAt)
                    ? '收起'
                    : '查看回复'
                }}</span>
              </button>

              <!-- 举报按钮 -->
              <button
                class="action-btn report-btn"
                @click="handleReport(review)"
              >
                <i class="fas fa-flag"></i>
                <span>举报</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 回复表单 -->
        <div
          v-if="replyingTo === (review.reviewId || review.createdAt)"
          class="reply-form"
        >
          <textarea
            v-model="replyContent"
            placeholder="写下你的回复..."
            class="reply-input"
            maxlength="500"
            @keydown.enter.ctrl="submitReply(review)"
          ></textarea>
          <div class="reply-form-footer">
            <span class="reply-hint">Ctrl + Enter 快速发送</span>
            <div class="reply-actions">
              <button
                @click="submitReply(review)"
                class="submit-reply"
                :disabled="isSubmittingReply"
                :class="{ submitting: isSubmittingReply }"
              >
                <i class="fas" :class="isSubmittingReply ? 'fa-spinner fa-spin' : 'fa-paper-plane'"></i>
                {{ isSubmittingReply ? '提交中...' : '发布回复' }}
              </button>
              <button
                @click="cancelReply"
                class="cancel-reply"
                :disabled="isSubmittingReply"
              >
                <i class="fas fa-times"></i>
                取消
              </button>
            </div>
          </div>
        </div>

        <!-- 回复列表 -->
        <div
          v-if="
            expandedReviews.includes(review.reviewId || review.createdAt) &&
            review.replies &&
            review.replies.length > 0
          "
          class="replies-list"
        >
          <div
            v-for="reply in review.replies"
            :key="reply.replyId"
            class="reply-item"
          >
            <img
              :src="getUserAvatar(reply.avatar)"
              :alt="reply.user"
              class="reply-avatar"
            />
            <div class="reply-content">
              <div class="reply-header">
                <span class="reply-user">{{ reply.user || '匿名用户' }}</span>
                <span class="reply-time">{{ formatTime(reply.createdAt) }}</span>
              </div>
              <p class="reply-text">{{ reply.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-data">
      <i class="fas fa-comments"></i>
      <p>暂无评价</p>
      <span class="empty-hint">成为第一个评价的人吧！</span>
    </div>

    <!-- 举报对话框 -->
    <div v-if="showReportDialog" class="report-overlay" @click="closeReportDialog">
      <div class="report-dialog" @click.stop>
        <div class="dialog-header">
          <h3>举报评论</h3>
          <button @click="closeReportDialog" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="dialog-body">
          <p class="dialog-hint">请选择举报原因：</p>

          <div class="report-reasons">
            <label
              v-for="reason in reportReasons"
              :key="reason.value"
              class="reason-option"
              :class="{ selected: selectedReason === reason.value }"
            >
              <input
                type="radio"
                :value="reason.value"
                v-model="selectedReason"
                name="report-reason"
              />
              <span class="reason-icon">{{ reason.icon }}</span>
              <span class="reason-text">{{ reason.label }}</span>
            </label>
          </div>

          <div class="additional-info">
            <label>补充说明（选填）：</label>
            <textarea
              v-model="reportDescription"
              placeholder="请简要说明举报原因..."
              maxlength="200"
              class="report-textarea"
            ></textarea>
            <span class="char-count">{{ reportDescription.length }}/200</span>
          </div>
        </div>

        <div class="dialog-footer">
          <button
            @click="submitReport"
            class="submit-report-btn"
            :disabled="!selectedReason || isSubmittingReport"
            :class="{ submitting: isSubmittingReport }"
          >
            <i class="fas" :class="isSubmittingReport ? 'fa-spinner fa-spin' : 'fa-paper-plane'"></i>
            {{ isSubmittingReport ? '提交中...' : '提交举报' }}
          </button>
          <button @click="closeReportDialog" class="cancel-btn" :disabled="isSubmittingReport">
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import StarRating from './StarRating.vue'
import { createReply, getReplies } from '@/services/commentService.js'
import { likeReview, unlikeReview, reportReview } from '@/services/reviewService.js'

const props = defineProps({
  reviews: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['reply-submitted', 'review-liked', 'review-reported'])

// 响应式数据
const replyingTo = ref(null)
const replyContent = ref('')
const isSubmittingReply = ref(false)  // 回复提交状态
const expandedReviews = ref([])

// 举报相关
const showReportDialog = ref(false)
const reportingReview = ref(null)
const selectedReason = ref('')
const reportDescription = ref('')
const isSubmittingReport = ref(false)

const reportReasons = [
  { value: 'SPAM', label: '垃圾广告', icon: '📢' },
  { value: 'HARASSMENT', label: '违法违规', icon: '⚠️' },
  { value: 'INAPPROPRIATE', label: '人身攻击', icon: '😡' },
  { value: 'SPOILER', label: '剧透内容', icon: '🔍' },
  { value: 'OTHER', label: '其他', icon: '❓' }
]

// 获取用户头像
const getUserAvatar = (avatar) => {
  if (avatar && avatar!==''){
    console.log('使用用户头像:', avatar)
    return avatar 
  } else {
    console.log('使用默认头像')
    //使用根目录下的默认头像
    return `${import.meta.env.MEDIA_ROOT || '/media/'}default-avatar.png`

  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '未知'

  try {
    const date = new Date(timeString)
    const now = new Date()
    const diff = now - date
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 7) {
      return date.toLocaleDateString('zh-CN')
    } else if (days > 0) {
      return `${days}天前`
    } else if (hours > 0) {
      return `${hours}小时前`
    } else if (minutes > 0) {
      return `${minutes}分钟前`
    } else {
      return '刚刚'
    }
  } catch (error) {
    return '未知'
  }
}

// 切换回复表单
const toggleReplyForm = (review) => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    alert('请先登录')
    return
  }

  const reviewKey = review.reviewId || review.createdAt

  if (replyingTo.value === reviewKey) {
    replyingTo.value = null
    replyContent.value = ''
  } else {
    replyingTo.value = reviewKey
    replyContent.value = ''
  }
}

// 取消回复
const cancelReply = () => {
  replyingTo.value = null
  replyContent.value = ''
}

// 提交回复
const submitReply = async (review) => {
  if (!replyContent.value.trim()) {
    alert('请输入回复内容')
    return
  }

  // 防止重复提交
  if (isSubmittingReply.value) {
    return
  }

  isSubmittingReply.value = true

  try {
    // 调试：打印评论数据结构（展开Proxy对象）
    const reviewData = JSON.parse(JSON.stringify(review))
    console.log('完整评论数据:', reviewData)
    console.log('评论数据所有键:', Object.keys(reviewData))

    // 详细日志：检查各种可能的ID字段
    const possibleIdFields = {
      comment_id: review.comment_id,
      commentId: review.commentId,
      id: review.id,
      reviewId: review.reviewId,
      review_id: review.review_id
    }
    console.log('可能的ID字段值:', possibleIdFields)

    // 优先使用标准化后的reviewId字段，这是在AnimeDetailView中映射的
    // 如果没有，则回退到原始的comment_id字段
    const commentId = review.reviewId || review.comment_id || review.commentId || review.id || review.review_id

    if (!commentId) {
      console.error('❌ 无法找到有效的评论ID')
      console.error('完整的review对象:', reviewData)
      console.error('所有可用字段及值:', possibleIdFields)

      alert('回复功能暂时不可用（评价ID缺失）\n请查看浏览器控制台获取更多信息')
      return
    }

    console.log('✅ 使用的评论ID:', commentId)
    console.log('准备发送回复请求:', {
      commentId: commentId,
      content: replyContent.value.trim(),
      url: `/api/comments/${commentId}/replies/`
    })

    const response = await createReply(commentId, replyContent.value.trim())

    // 根据API文档，成功状态码是201
    if (response.code === 201 || response.code === 200) {
      alert(response.message || '回复发布成功！')

      // 将新回复添加到当前评论的回复列表中
      if (!review.replies) {
        review.replies = []
      }

      // 标准化新回复数据并添加到列表前端
      const newReply = {
        ...response.data,
        replyId: response.data.reply_id,
        user: response.data.author?.username || '匿名用户',
        createdAt: response.data.created_at,
        likes: 0
      }
      review.replies.unshift(newReply)

      // 更新回复数量
      review.replyCount = (review.replyCount || 0) + 1

      // 确保回复列表是展开的
      const reviewKey = review.reviewId || review.createdAt
      if (!expandedReviews.value.includes(reviewKey)) {
        expandedReviews.value.push(reviewKey)
      }

      // 触发事件通知父组件
      emit('reply-submitted', {
        commentId: commentId,
        reply: response.data
      })

      // 关闭回复表单
      cancelReply()
    } else {
      throw new Error(response.message || '回复失败')
    }
  } catch (error) {
    console.error('提交回复失败:', error)
    console.error('错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      config: error.config
    })
    alert(error.response?.data?.message || error.message || '回复失败，请稍后重试')
  } finally {
    isSubmittingReply.value = false
  }
}

// 切换回复展开/收起
const toggleReplies = async (review) => {
  const reviewKey = review.reviewId || review.createdAt
  const commentId = review.reviewId || review.comment_id || review.commentId || review.id

  console.log('点击查看回复按钮，评论ID:', commentId)

  if (!commentId) {
    console.error('❌ 无法找到有效的评论ID')
    alert('查看回复功能暂时不可用（评论ID缺失）')
    return
  }

  const index = expandedReviews.value.indexOf(reviewKey)

  if (index > -1) {
    // 收起回复
    expandedReviews.value.splice(index, 1)
    console.log('收起回复列表')
  } else {
    // 展开回复
    expandedReviews.value.push(reviewKey)
    console.log('展开回复列表，准备加载回复数据')

    // 如果还没有加载过回复，则加载
    if (!review.replies || review.replies.length === 0) {
      try {
        console.log('开始获取回复数据...')
        const response = await getReplies(commentId, {
          page: 1,
          pageSize: 20,
          orderBy: 'time_desc'
        })

        console.log('回复API响应:', response)

        if (response?.code === 200 && response.data) {
          const rawReplies = response.data.replies || []
          console.log('原始回复数据:', rawReplies)

          // 标准化回复数据结构
          review.replies = rawReplies.map(reply => ({
            ...reply,
            replyId: reply.reply_id,
            user: reply.author?.username || '匿名用户',
            createdAt: reply.created_at,
            likes: reply.likes_count || 0
          }))

          console.log('标准化后的回复数据:', review.replies)
        } else {
          console.error('回复数据响应不正确:', response)
          review.replies = []
        }
      } catch (error) {
        console.error('获取回复失败:', error)
        alert('获取回复失败，请稍后重试')
        // 如果获取失败，移除展开状态
        const failIndex = expandedReviews.value.indexOf(reviewKey)
        if (failIndex > -1) {
          expandedReviews.value.splice(failIndex, 1)
        }
      }
    } else {
      console.log('回复数据已存在，直接显示')
    }
  }
}

// 点赞评价
const handleLike = async (review) => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    alert('请先登录')
    return
  }

  try {
    // 调试：打印完整的评论数据结构
    const reviewData = JSON.parse(JSON.stringify(review))
    console.log('完整的评论数据结构:', reviewData)
    console.log('所有可用字段:', Object.keys(reviewData))
    
    // 优先使用标准化后的reviewId字段，这是在AnimeDetailView中映射的
    // 如果没有，则回退到原始的comment_id字段
    const commentId = review.reviewId || review.comment_id || review.commentId || review.id

    if (!commentId) {
      console.error('❌ 无法找到有效的评论ID')
      console.error('完整的评论对象:', reviewData)
      console.error('所有字段及值:', Object.entries(reviewData))
      alert('点赞功能暂时不可用（评论ID缺失）\n请查看浏览器控制台获取详细信息')
      return
    }

    console.log('✅ 使用的评论ID:', commentId)
    console.log('准备发送点赞请求:', {
      commentId: commentId,
      isLiked: review.isLiked,
      url: `/api/comments/${commentId}/like/`
    })

    let response
    if (review.isLiked) {
      // 取消点赞
      response = await unlikeReview(commentId)
    } else {
      // 点赞
      response = await likeReview(commentId)
    }

    if (response.code === 200) {
      // 更新本地状态
      review.isLiked = !review.isLiked
      // 使用后端返回的点赞数，如果没有则本地计算
      review.likes = response.data.likes_count || (review.isLiked ? (review.likes || 0) + 1 : Math.max((review.likes || 0) - 1, 0))

      // 触发事件通知父组件
      emit('review-liked', {
        reviewId: commentId,
        liked: review.isLiked,
        likes: review.likes
      })

      // 显示提示
      alert(response.message || (review.isLiked ? '点赞成功！' : '已取消点赞'))
    } else {
      console.error('点赞API返回错误:', response)
      alert(response.message || '操作失败')
    }
  } catch (error) {
    console.error('点赞操作失败:', error)
    console.error('错误详情:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      config: error.config
    })
    
    if (error.response?.status === 401) {
      alert('登录已过期，请重新登录')
    } else if (error.response?.status === 404) {
      alert('评论不存在或已被删除')
    } else {
      alert(error.response?.data?.message || error.message || '操作失败，请稍后重试')
    }
  }
}

// 举报评价
const handleReport = (review) => {
  // 检查登录状态
  const token = localStorage.getItem('access_token')
  if (!token) {
    alert('请先登录')
    return
  }

  // 打开举报对话框
  reportingReview.value = review
  selectedReason.value = ''
  reportDescription.value = ''
  showReportDialog.value = true
}

// 关闭举报对话框
const closeReportDialog = () => {
  if (isSubmittingReport.value) return

  showReportDialog.value = false
  reportingReview.value = null
  selectedReason.value = ''
  reportDescription.value = ''
}

// 提交举报
const submitReport = async () => {
  if (!selectedReason.value) {
    alert('请选择举报原因')
    return
  }

  if (isSubmittingReport.value) return

  isSubmittingReport.value = true

  try {
    // 尝试多种可能的ID字段
    const reviewId = reportingReview.value?.reviewId || reportingReview.value?.id || reportingReview.value?.comment_id

    if (!reviewId) {
      console.warn('评论数据缺少ID字段:', reportingReview.value)
      alert('举报功能暂时不可用')
      return
    }

    const response = await reportReview(reviewId, selectedReason.value, reportDescription.value.trim())

    if (response.code === 201 || response.code === 200) {
      alert('举报已提交，我们会尽快处理')

      // 触发事件通知父组件
      emit('review-reported', {
        reviewId: reviewId,
        reason: selectedReason.value
      })

      // 关闭对话框
      closeReportDialog()
    } else {
      throw new Error(response.message || '举报失败')
    }
  } catch (error) {
    console.error('举报失败:', error)
    if (error.response?.status === 400) {
      alert('你已经举报过该评论')
    } else {
      alert(error.response?.data?.message || error.message || '举报失败，请稍后重试')
    }
  } finally {
    isSubmittingReport.value = false
  }
}

</script>

<style scoped>
.review-list {
  margin-top: 20px;
}

.reviews-container {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

/* 评价项 */
.review-item {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  border: 2px solid #ffc2d9;
  padding: 25px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.review-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(255, 107, 157, 0.15);
}

.review-main {
  display: flex;
  gap: 20px;
}

.review-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #ff6b9d;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(255, 107, 157, 0.3);
}

.review-content {
  flex: 1;
}

.review-header-info {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.review-user {
  color: #333;
  font-weight: 600;
  font-size: 16px;
}

.review-rating {
  display: flex;
  align-items: center;
}

.review-time {
  color: #999;
  font-size: 13px;
  margin-left: auto;
}

.review-text {
  color: #666;
  line-height: 1.8;
  font-size: 14px;
  margin-bottom: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  border-left: 4px solid #ff6b9d;
  white-space: pre-wrap;
  word-break: break-word;
}

.review-text.no-comment {
  color: #999;
  font-style: italic;
  border-left-color: #e0e0e0;
  background: rgba(0, 0, 0, 0.02);
}

.review-text.no-comment i {
  margin-right: 8px;
}

/* 评价操作按钮 */
.review-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.8);
  border: 1.5px solid #ffc2d9;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.action-btn:hover {
  background: rgba(255, 107, 157, 0.1);
  border-color: #ff6b9d;
  color: #ff6b9d;
  transform: translateY(-2px);
}

.action-btn i {
  font-size: 13px;
}

.like-btn.liked {
  background: rgba(255, 107, 157, 0.1);
  border-color: #ff6b9d;
  color: #ff6b9d;
}

.like-btn.liked i {
  animation: heartbeat 0.6s ease;
}

@keyframes heartbeat {
  0%,
  100% {
    transform: scale(1);
  }
  25% {
    transform: scale(1.3);
  }
  50% {
    transform: scale(1.1);
  }
}

/* 回复表单 */
.reply-form {
  margin-top: 20px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(162, 210, 255, 0.08), rgba(189, 224, 254, 0.08));
  border-radius: 15px;
  border: 2px solid #a2d2ff;
  animation: slideDown 0.3s ease;
  
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.reply-input {
  width: 100%;
  min-height: 90px;
  padding: 12px;
  border: 2px solid #a2d2ff;
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.reply-input:focus {
  outline: none;
  border-color: #6ba3d8;
  box-shadow: 0 0 0 4px rgba(162, 210, 255, 0.2);
}

.reply-form-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reply-hint {
  color: #999;
  font-size: 12px;
  font-style: italic;
}

.reply-actions {
  display: flex;
  gap: 10px;
}

.submit-reply,
.cancel-reply {
  padding: 10px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.submit-reply {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  box-shadow: 0 2px 8px rgba(162, 210, 255, 0.3);
}

.submit-reply:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.4);
}

.submit-reply:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.submit-reply.submitting {
  background: linear-gradient(135deg, #8bb8e8, #9fc9ed);
}

.cancel-reply {
  background: rgba(255, 255, 255, 0.9);
  color: #999;
  border: 1.5px solid #e0e0e0;
}

.cancel-reply:hover:not(:disabled) {
  background: #f5f5f5;
  color: #666;
  border-color: #ccc;
}

.cancel-reply:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 回复列表 */
.replies-list {
  margin-top: 20px;
  padding-left: 50px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  animation: slideDown 0.3s ease;
}

.reply-item {
  display: flex;
  gap: 12px;
  padding: 15px;
  background: rgba(162, 210, 255, 0.06);
  border-radius: 12px;
  border-left: 3px solid #a2d2ff;
  transition: all 0.3s ease;
}

.reply-item:hover {
  background: rgba(162, 210, 255, 0.12);
  transform: translateX(5px);
}

.reply-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #a2d2ff;
  flex-shrink: 0;
}

.reply-content {
  flex: 1;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.reply-user {
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.reply-time {
  color: #999;
  font-size: 12px;
}

.reply-text {
  color: #666;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 空状态 */
.empty-data {
  text-align: center;
  padding: 80px 30px;
  color: #999;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  border: 2px dashed #ffc2d9;
}

.empty-data i {
  font-size: 64px;
  margin-bottom: 20px;
  color: #ffc2d9;
  opacity: 0.6;
}

.empty-data p {
  font-size: 18px;
  margin: 0 0 10px 0;
  font-weight: 500;
  color: #999;
}

.empty-hint {
  font-size: 14px;
  color: #bbb;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .review-item {
    padding: 20px 15px;
  }

  .review-main {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .review-avatar {
    margin: 0 auto;
  }

  .review-header-info {
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }

  .review-time {
    margin-left: 0;
  }

  .review-actions {
    justify-content: center;
  }

  .replies-list {
    padding-left: 20px;
  }

  .reply-form-footer {
    flex-direction: column;
    gap: 10px;
  }

  .reply-actions {
    width: 100%;
  }

  .submit-reply,
  .cancel-reply {
    flex: 1;
  }
}

/* 举报对话框样式 */
.report-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.report-dialog {
  background: white;
  border-radius: 20px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-bottom: 2px solid #ffc2d9;
  background: linear-gradient(135deg, rgba(255, 194, 217, 0.1), rgba(255, 107, 157, 0.05));
}

.dialog-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 5px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.close-btn:hover {
  background: rgba(255, 107, 157, 0.1);
  color: #ff6b9d;
}

.dialog-body {
  padding: 25px;
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-hint {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

.report-reasons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.reason-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.reason-option:hover {
  border-color: #ffc2d9;
  background: rgba(255, 194, 217, 0.05);
}

.reason-option.selected {
  border-color: #ff6b9d;
  background: rgba(255, 107, 157, 0.08);
}

.reason-option input[type="radio"] {
  margin: 0;
  cursor: pointer;
}

.reason-icon {
  font-size: 20px;
}

.reason-text {
  flex: 1;
  color: #333;
  font-weight: 500;
}

.additional-info {
  margin-top: 20px;
}

.additional-info label {
  display: block;
  margin-bottom: 10px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
}

.report-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  transition: all 0.3s ease;
}

.report-textarea:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

.char-count {
  display: block;
  text-align: right;
  margin-top: 5px;
  color: #999;
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  padding: 20px 25px;
  border-top: 2px solid #f0f0f0;
  background: rgba(0, 0, 0, 0.02);
}

.submit-report-btn,
.cancel-btn {
  flex: 1;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-report-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8fab);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 107, 157, 0.3);
}

.submit-report-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.4);
}

.submit-report-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.submit-report-btn.submitting {
  background: linear-gradient(135deg, #e85a8a, #e87799);
}

.cancel-btn {
  background: white;
  color: #666;
  border: 2px solid #e0e0e0;
}

.cancel-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #ccc;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

</style>
