<template>
  <!-- 模态框遮罩 -->
  <div v-if="visible" class="modal-overlay" @click.self="handleClose">
    <div class="modal-container">
      <!-- 模态框头部 -->
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-file-alt"></i>
          举报详情
        </h2>
        <button class="close-btn" @click="handleClose">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="modal-loading">
        <div class="loading-spinner">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <p>加载详情中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="modal-error">
        <div class="error-icon">
          <i class="fas fa-exclamation-triangle"></i>
        </div>
        <p>{{ error }}</p>
        <button class="retry-btn" @click="fetchDetail">
          <i class="fas fa-redo"></i>
          重试
        </button>
      </div>

      <!-- 模态框内容 -->
      <div v-else-if="detail" class="modal-content">
        <!-- 举报信息概览 -->
        <div class="report-overview">
          <div class="overview-row">
            <div class="overview-item">
              <span class="label">举报ID</span>
              <span class="value report-id">#{{ detail.id }}</span>
            </div>
            <div class="overview-item">
              <span class="label">状态</span>
              <ReportStatusBadge :status="detail.status" size="medium" />
            </div>
            <div class="overview-item">
              <span class="label">举报时间</span>
              <span class="value">{{ formatDateTime(detail.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 举报人信息 -->
        <div class="info-section">
          <h3 class="section-title">
            <i class="fas fa-user"></i>
            举报人信息
          </h3>
          <div class="reporter-info">
            <div class="user-avatar-large">
              <img
                :src="detail.reporter.avatar || '/default-avatar.png'"
                :alt="detail.reporter.username"
                class="avatar-large"
              />
            </div>
            <div class="user-details">
              <div class="username-large">{{ detail.reporter.username }}</div>
              <div class="user-meta">
                <span class="meta-item">
                  <i class="fas fa-id-badge"></i>
                  ID: {{ detail.reporter.user_id }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 举报对象信息 -->
        <div class="info-section">
          <h3 class="section-title">
            <i class="fas fa-bullseye"></i>
            举报对象
          </h3>
          <div class="target-info">
            <div class="info-row">
              <span class="info-label">对象类型</span>
              <span class="info-value target-type-badge">{{ detail.target_type }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">对象ID</span>
              <span class="info-value">{{ detail.target_id }}</span>
            </div>
            <div v-if="detail.target_content" class="target-content-section">
              <div class="content-header">
                <span class="content-label">对象内容</span>
                <div v-if="detail.target_content.author" class="content-author">
                  <i class="fas fa-user-circle"></i>
                  作者: {{ detail.target_content.author.username }}
                  (ID: {{ detail.target_content.author.user_id }})
                </div>
              </div>
              <div class="content-box">
                {{ detail.target_content.content }}
              </div>
              <div v-if="detail.target_content.created_at" class="content-meta">
                <i class="fas fa-clock"></i>
                创建于 {{ formatDateTime(detail.target_content.created_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 举报类型和理由 -->
        <div class="info-section">
          <h3 class="section-title">
            <i class="fas fa-clipboard-list"></i>
            举报类型和理由
          </h3>
          <div class="report-reason-section">
            <div class="info-row">
              <span class="info-label">举报类型</span>
              <span :class="['category-badge-large', `category-${detail.category.toLowerCase()}`]">
                {{ detail.category_display }}
              </span>
            </div>
            <div class="reason-box">
              <div class="reason-label">举报理由</div>
              <div class="reason-content">{{ detail.reason }}</div>
            </div>
          </div>
        </div>

        <!-- 处理信息（如果已处理） -->
        <div v-if="detail.status !== 'PENDING'" class="info-section">
          <h3 class="section-title">
            <i class="fas fa-gavel"></i>
            处理信息
          </h3>
          <div class="resolution-info">
            <div class="info-row">
              <span class="info-label">处理人</span>
              <span class="info-value">{{ detail.moderator || '系统' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">处理时间</span>
              <span class="info-value">{{ formatDateTime(detail.handled_at) }}</span>
            </div>
            <div v-if="detail.resolution" class="resolution-box">
              <div class="resolution-label">处理说明</div>
              <div class="resolution-content">{{ detail.resolution }}</div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="modal-actions">
          <button
            class="btn btn-secondary"
            @click="handleClose"
          >
            <i class="fas fa-times"></i>
            关闭
          </button>
          <button
            v-if="detail.status === 'PENDING'"
            class="btn btn-primary"
            @click="handleAction"
          >
            <i class="fas fa-gavel"></i>
            处理举报
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getReportDetail } from '@/services/reportService.js'
import ReportStatusBadge from './ReportStatusBadge.vue'

const props = defineProps({
  // 模态框是否可见
  visible: {
    type: Boolean,
    required: true
  },
  // 举报ID
  reportId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['close', 'handle', 'update:visible'])

// 状态管理
const loading = ref(false)
const error = ref('')
const detail = ref(null)

// 获取举报详情
const fetchDetail = async () => {
  if (!props.reportId) return

  loading.value = true
  error.value = ''
  detail.value = null

  try {
    const response = await getReportDetail(props.reportId)

    if (response?.code === 200 && response.data) {
      detail.value = response.data
    } else {
      throw new Error(response?.message || '获取详情失败')
    }
  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('获取举报详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 处理关闭
const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

// 处理举报
const handleAction = () => {
  if (detail.value) {
    emit('handle', detail.value)
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 监听visible和reportId变化
watch(() => [props.visible, props.reportId], ([newVisible, newReportId]) => {
  if (newVisible && newReportId) {
    fetchDetail()
  }
})
</script>

<style scoped>
.modal-overlay {
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
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-container {
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
  border-radius: 20px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  border-radius: 20px 20px 0 0;
  color: white;
  position: sticky;
  top: 0;
  z-index: 10;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  font-size: 16px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

/* 加载和错误状态 */
.modal-loading,
.modal-error {
  padding: 60px 24px;
  text-align: center;
}

.loading-spinner i,
.error-icon i {
  font-size: 48px;
  margin-bottom: 16px;
}

.loading-spinner i {
  color: #ff6b9d;
}

.error-icon i {
  color: #ff4081;
}

.modal-loading p,
.modal-error p {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.retry-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-2px);
}

/* 模态框内容 */
.modal-content {
  padding: 24px;
}

/* 举报信息概览 */
.report-overview {
  background: rgba(255, 107, 157, 0.05);
  border: 1px solid rgba(255, 107, 157, 0.1);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
}

.overview-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.overview-item .label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.overview-item .value {
  font-size: 15px;
  color: #333;
  font-weight: 600;
}

.report-id {
  color: #ff6b9d;
  font-size: 18px;
}

/* 信息区块 */
.info-section {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e9ecef;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid #ffc2d9;
}

.section-title i {
  color: #ff6b9d;
}

/* 举报人信息 */
.reporter-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #ff6b9d;
  flex-shrink: 0;
}

.avatar-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.username-large {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.user-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

.meta-item i {
  color: #ff6b9d;
  font-size: 12px;
}

/* 信息行 */
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.target-type-badge {
  background: linear-gradient(135deg, #42a5f5, #64b5f6);
  color: white;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 13px;
}

/* 举报对象内容 */
.target-content-section {
  margin-top: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  padding: 16px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.content-label {
  font-size: 13px;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.content-author {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}

.content-author i {
  color: #ff6b9d;
}

.content-box {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 8px;
}

.content-meta {
  font-size: 11px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 6px;
}

.content-meta i {
  color: #ff6b9d;
}

/* 举报类型标识 */
.category-badge-large {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  color: white;
}

.category-harassment {
  background: linear-gradient(135deg, #e91e63, #f06292);
}

.category-spam {
  background: linear-gradient(135deg, #ff9800, #ffb74d);
}

.category-inappropriate {
  background: linear-gradient(135deg, #9c27b0, #ba68c8);
}

.category-copyright {
  background: linear-gradient(135deg, #3f51b5, #7986cb);
}

.category-other {
  background: linear-gradient(135deg, #607d8b, #90a4ae);
}

/* 举报理由 */
.reason-box {
  margin-top: 16px;
}

.reason-label {
  font-size: 13px;
  color: #666;
  font-weight: 600;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.reason-content {
  background: rgba(255, 193, 7, 0.05);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 处理信息 */
.resolution-box {
  margin-top: 16px;
}

.resolution-label {
  font-size: 13px;
  color: #666;
  font-weight: 600;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.resolution-content {
  background: rgba(76, 175, 80, 0.05);
  border: 1px solid rgba(76, 175, 80, 0.2);
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 操作按钮 */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
  position: sticky;
  bottom: 0;
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover:not(:disabled) {
  background: #e0e0e0;
  transform: translateY(-2px);
}

.btn-primary {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff4081, #ff6b9d);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-container {
    max-width: 95%;
    margin: 10px;
  }

  .modal-header {
    padding: 16px 20px;
  }

  .modal-title {
    font-size: 18px;
  }

  .modal-content {
    padding: 20px;
  }

  .overview-row {
    grid-template-columns: 1fr;
  }

  .reporter-info {
    flex-direction: column;
    text-align: center;
  }

  .user-details {
    text-align: center;
  }

  .user-meta {
    justify-content: center;
  }

  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .content-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .modal-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .modal-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .close-btn {
    align-self: flex-end;
    margin-top: -40px;
  }

  .section-title {
    font-size: 14px;
  }

  .username-large {
    font-size: 16px;
  }
}
</style>
