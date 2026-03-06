<template>
  <div class="report-management-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-flag"></i>
        举报管理
      </h1>
      <p class="page-subtitle">查看并处理用户提交的举报，维护良好社区环境</p>
    </div>

    <!-- 筛选和搜索栏 -->
    <div class="filter-section">
      <div class="filter-controls">
        <button
          v-for="statusOption in statusOptions"
          :key="statusOption.value"
          :class="['status-filter-btn', { active: statusFilter === statusOption.value }]"
          @click="changeStatusFilter(statusOption.value)"
        >
          <i :class="statusOption.icon"></i>
          {{ statusOption.label }}
          <span v-if="statusOption.value === ''" class="count-badge">{{ stats.pending_count + stats.resolved_count + stats.rejected_count }}</span>
          <span v-else-if="statusOption.value === 'PENDING'" class="count-badge pending">{{ stats.pending_count }}</span>
          <span v-else-if="statusOption.value === 'RESOLVED'" class="count-badge resolved">{{ stats.resolved_count }}</span>
          <span v-else-if="statusOption.value === 'REJECTED'" class="count-badge rejected">{{ stats.rejected_count }}</span>
        </button>
      </div>

      <button class="refresh-btn" @click="fetchReportList(true)" :disabled="loading">
        <i class="fas fa-redo" :class="{ 'fa-spin': loading }"></i>
        刷新
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && reports.length === 0" class="loading-state">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
      </div>
      <p>加载举报数据中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="fetchReportList(true)">
        <i class="fas fa-redo"></i>
        重试
      </button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && reports.length === 0" class="empty-state">
      <div class="empty-icon">
        <i class="fas fa-check-circle"></i>
      </div>
      <h3>暂无举报</h3>
      <p>当前没有{{ statusFilterText }}的举报</p>
    </div>

    <!-- 举报列表 -->
    <div v-else class="report-list-container">
      <!-- 统计信息 -->
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-icon pending">
            <i class="fas fa-clock"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pending_count }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon resolved">
            <i class="fas fa-check"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.resolved_count }}</div>
            <div class="stat-label">已处理</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon rejected">
            <i class="fas fa-times"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.rejected_count }}</div>
            <div class="stat-label">已驳回</div>
          </div>
        </div>
      </div>

      <!-- 举报表格 -->
      <div class="report-table-wrapper">
        <table class="report-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th class="col-reporter">举报人</th>
              <th class="col-target">举报对象</th>
              <th class="col-category">举报类型</th>
              <th class="col-reason">举报理由</th>
              <th class="col-status">状态</th>
              <th class="col-date">举报时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in reports" :key="report.id" :class="{ 'row-pending': report.status === 'PENDING' }">
              <!-- ID列 -->
              <td class="col-id">
                <span class="report-id">#{{ report.id }}</span>
              </td>

              <!-- 举报人列 -->
              <td class="col-reporter">
                <div class="user-cell">
                  <div class="user-info-small">
                    <div class="username">{{ report.reporter.username }}</div>
                    <div class="user-id">ID: {{ report.reporter.user_id }}</div>
                  </div>
                </div>
              </td>

              <!-- 举报对象列 -->
              <td class="col-target">
                <div class="target-cell">
                  <span class="target-type">{{ report.target_type }}</span>
                  <span class="target-id">ID: {{ report.target_id }}</span>
                  <div class="target-preview" :title="report.target_preview">
                    {{ truncateText(report.target_preview, 30) }}
                  </div>
                </div>
              </td>

              <!-- 举报类型列 -->
              <td class="col-category">
                <span class="category-badge" :class="`category-${report.category.toLowerCase()}`">
                  {{ report.category_display }}
                </span>
              </td>

              <!-- 举报理由列 -->
              <td class="col-reason">
                <div class="reason-text" :title="report.reason">
                  {{ truncateText(report.reason, 40) }}
                </div>
              </td>

              <!-- 状态列 -->
              <td class="col-status">
                <ReportStatusBadge :status="report.status" size="small" />
              </td>

              <!-- 举报时间列 -->
              <td class="col-date">
                <div class="date-cell">
                  <div class="date-value">{{ formatDate(report.created_at) }}</div>
                  <div class="date-ago">{{ timeAgo(report.created_at) }}</div>
                </div>
              </td>

              <!-- 操作列 -->
              <td class="col-actions">
                <div class="action-buttons">
                  <button
                    class="btn-action btn-view"
                    @click="viewReportDetail(report.id)"
                    :title="'查看详情'"
                  >
                    <i class="fas fa-eye"></i>
                    详情
                  </button>
                  <button
                    v-if="report.status === 'PENDING'"
                    class="btn-action btn-handle"
                    @click="openHandleModal(report)"
                    :disabled="actionLoading[report.id]"
                    :title="'处理举报'"
                  >
                    <i class="fas fa-gavel"></i>
                    处理
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div v-if="pagination.total_pages > 1" class="pagination">
        <div class="pagination-info">
          显示 {{ (pagination.page - 1) * pagination.page_size + 1 }}-{{ Math.min(pagination.page * pagination.page_size, pagination.total) }} 条，共 {{ pagination.total }} 条
        </div>
        <div class="pagination-controls">
          <button
            class="page-btn"
            :disabled="pagination.page <= 1"
            @click="goToPage(pagination.page - 1)"
          >
            <i class="fas fa-chevron-left"></i>
            上一页
          </button>

          <div class="page-numbers">
            <button
              v-for="page in visiblePages"
              :key="page"
              :class="['page-number', { active: page === pagination.page }]"
              @click="goToPage(page)"
            >
              {{ page }}
            </button>
          </div>

          <button
            class="page-btn"
            :disabled="pagination.page >= pagination.total_pages"
            @click="goToPage(pagination.page + 1)"
          >
            下一页
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 举报详情模态框 -->
    <ReportDetailModal
      v-model:visible="showDetailModal"
      :report-id="selectedReportId"
      @close="closeDetailModal"
      @handle="handleFromDetail"
    />

    <!-- 举报处理模态框 -->
    <ReportActionModal
      v-model:visible="showActionModal"
      :report="selectedReport"
      @confirm="handleReportAction"
      @close="closeActionModal"
    />

    <!-- 消息提示 -->
    <div v-if="message.show" :class="['message-alert', message.type]">
      <i :class="message.icon"></i>
      <span>{{ message.text }}</span>
      <button class="close-message" @click="message.show = false">
        <i class="fas fa-times"></i>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getReportList, handleReport, getReportDetail } from '@/services/reportService.js'
import { banUser } from '@/services/adminService.js'
import ReportStatusBadge from './ReportStatusBadge.vue'
import ReportDetailModal from './ReportDetailModal.vue'
import ReportActionModal from './ReportActionModal.vue'

// 状态管理
const loading = ref(false)
const error = ref('')
const reports = ref([])
const statusFilter = ref('')

// 统计信息
const stats = reactive({
  pending_count: 0,
  resolved_count: 0,
  rejected_count: 0
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

// 模态框状态
const showDetailModal = ref(false)
const showActionModal = ref(false)
const selectedReportId = ref(null)
const selectedReport = ref(null)
const actionLoading = ref({})

// 消息提示
const message = reactive({
  show: false,
  type: 'success',
  text: '',
  icon: 'fas fa-check-circle'
})

// 状态筛选选项
const statusOptions = [
  { value: '', label: '全部', icon: 'fas fa-list' },
  { value: 'PENDING', label: '待处理', icon: 'fas fa-clock' },
  { value: 'RESOLVED', label: '已处理', icon: 'fas fa-check' },
  { value: 'REJECTED', label: '已驳回', icon: 'fas fa-times' }
]

// 计算属性
const visiblePages = computed(() => {
  const current = pagination.page
  const total = pagination.total_pages
  const delta = 2
  const pages = []

  for (let i = Math.max(1, current - delta); i <= Math.min(total, current + delta); i++) {
    pages.push(i)
  }

  return pages
})

const statusFilterText = computed(() => {
  const option = statusOptions.find(opt => opt.value === statusFilter.value)
  return option ? option.label : ''
})

// 获取举报列表
const fetchReportList = async (resetPage = false) => {
  if (resetPage) {
    pagination.page = 1
  }

  loading.value = true
  error.value = ''

  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      status: statusFilter.value || undefined
    }

    const response = await getReportList(params)

    if (response?.code === 200 && response.data) {
      const data = response.data

      // 提取举报列表
      reports.value = data.reports || []

      // 更新分页信息
      if (data.pagination) {
        pagination.page = data.pagination.page || 1
        pagination.page_size = data.pagination.page_size || 20
        pagination.total = data.pagination.total || 0
        pagination.total_pages = data.pagination.total_pages || 0
      }

      // 更新统计信息
      if (data.stats) {
        stats.pending_count = data.stats.pending_count || 0
        stats.resolved_count = data.stats.resolved_count || 0
        stats.rejected_count = data.stats.rejected_count || 0
      }
    } else {
      throw new Error(response?.message || '获取举报列表失败')
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('获取举报列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 改变状态筛选
const changeStatusFilter = (status) => {
  statusFilter.value = status
  fetchReportList(true)
}

// 跳转到指定页
const goToPage = (page) => {
  if (page < 1 || page > pagination.total_pages) return
  pagination.page = page
  fetchReportList()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 查看举报详情
const viewReportDetail = (reportId) => {
  selectedReportId.value = reportId
  showDetailModal.value = true
}

// 关闭详情模态框
const closeDetailModal = () => {
  showDetailModal.value = false
  selectedReportId.value = null
}

// 从详情页打开处理模态框
const handleFromDetail = (report) => {
  closeDetailModal()
  selectedReport.value = report
  showActionModal.value = true
}

// 打开处理模态框
const openHandleModal = (report) => {
  selectedReport.value = report
  showActionModal.value = true
}

// 关闭处理模态框
const closeActionModal = () => {
  showActionModal.value = false
  selectedReport.value = null
}

// 处理举报
const handleReportAction = async (actionData) => {
  if (!selectedReport.value) return

  const reportId = selectedReport.value.id
  actionLoading.value[reportId] = true

  try {
    // 1. 如果是同意举报且需要封禁用户，先获取举报详情以获取被举报用户ID
    let targetUserId = null
    if (actionData.action === 'RESOLVED' && actionData.ban_user) {
      const detailResponse = await getReportDetail(reportId)
      if (detailResponse?.code === 200 && detailResponse.data) {
        const detail = detailResponse.data
        // 从举报对象内容中获取作者ID
        if (detail.target_content && detail.target_content.author) {
          targetUserId = detail.target_content.author.user_id
        }
      }

      if (!targetUserId) {
        throw new Error('无法获取被举报用户信息')
      }
    }

    // 2. 处理举报（标记举报状态）
    const response = await handleReport(reportId, actionData)

    if (response?.code === 200) {
      // 3. 如果需要封禁用户，调用封禁API
      if (actionData.action === 'RESOLVED' && actionData.ban_user && targetUserId) {
        const banResponse = await banUser(targetUserId, {
          reason: actionData.resolution || '违反社区规定（来自举报处理）',
          ban_duration: actionData.ban_duration || 7,
        })

        if (banResponse?.code === 200) {
          showMessage(
            '举报处理成功，用户已被封禁',
            'success',
            'fas fa-check-circle'
          )
        } else {
          // 举报已处理，但封禁失败
          showMessage(
            '举报已处理，但封禁用户失败: ' + (banResponse?.message || '未知错误'),
            'error',
            'fas fa-exclamation-circle'
          )
        }
      } else {
        showMessage(
          '举报处理成功',
          'success',
          'fas fa-check-circle'
        )
      }

      closeActionModal()

      // 刷新列表
      setTimeout(() => {
        fetchReportList()
      }, 500)
    } else {
      throw new Error(response?.message || '处理失败')
    }

  } catch (err) {
    showMessage(
      err.message || '处理失败，请稍后重试',
      'error',
      'fas fa-exclamation-circle'
    )
    console.error('举报处理失败:', err)
  } finally {
    actionLoading.value[reportId] = false
  }
}

// 显示消息提示
const showMessage = (text, type = 'success', icon = 'fas fa-check-circle') => {
  message.text = text
  message.type = type
  message.icon = icon
  message.show = true

  setTimeout(() => {
    message.show = false
  }, 3000)
}

// 工具函数
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const timeAgo = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor(diffMs / (1000 * 60))

  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}周前`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)}个月前`
  return `${Math.floor(diffDays / 365)}年前`
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 生命周期
onMounted(() => {
  fetchReportList()
})
</script>

<style scoped>
.report-management-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
}

/* 页面头部 */
.page-header {
  max-width: 1400px;
  margin: 0 auto 30px;
  text-align: center;
}

.page-title {
  color: #333;
  font-size: 36px;
  text-shadow: 2px 2px 0 #ffc2d9;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.page-title i {
  color: #ff6b9d;
}

.page-subtitle {
  color: #666;
  font-size: 16px;
  margin: 0;
}

/* 筛选栏 */
.filter-section {
  max-width: 1400px;
  margin: 0 auto 30px;
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-controls {
  flex: 1;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.status-filter-btn {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #ffc2d9;
  border-radius: 25px;
  padding: 12px 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  position: relative;
}

.status-filter-btn:hover {
  border-color: #ff6b9d;
  color: #ff6b9d;
  transform: translateY(-2px);
}

.status-filter-btn.active {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  border-color: #ff6b9d;
  color: white;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.count-badge {
  background: rgba(0, 0, 0, 0.2);
  color: white;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
}

.status-filter-btn:not(.active) .count-badge {
  background: #ff6b9d;
}

.status-filter-btn:not(.active) .count-badge.pending {
  background: #ffa726;
}

.status-filter-btn:not(.active) .count-badge.resolved {
  background: #66bb6a;
}

.status-filter-btn:not(.active) .count-badge.rejected {
  background: #ef5350;
}

.refresh-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 25px;
  padding: 12px 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

.refresh-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载、错误和空状态 */
.loading-state,
.error-state,
.empty-state {
  max-width: 1400px;
  margin: 60px auto;
  text-align: center;
  padding: 60px 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 25px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
}

.loading-spinner i,
.error-icon i,
.empty-icon i {
  font-size: 64px;
  margin-bottom: 20px;
}

.loading-spinner i {
  color: #ff6b9d;
}

.error-icon i {
  color: #ff4081;
}

.empty-icon i {
  color: #66bb6a;
}

.error-state h3,
.empty-state h3 {
  color: #333;
  margin: 20px 0 10px;
  font-size: 24px;
}

.error-state p,
.empty-state p {
  color: #666;
  margin-bottom: 30px;
  font-size: 16px;
}

.retry-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 12px 24px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-2px);
}

/* 统计信息 */
.stats-section {
  max-width: 1400px;
  margin: 0 auto 30px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 30px rgba(255, 107, 157, 0.2);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #ffa726, #ffb74d);
}

.stat-icon.resolved {
  background: linear-gradient(135deg, #66bb6a, #81c784);
}

.stat-icon.rejected {
  background: linear-gradient(135deg, #ef5350, #e57373);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 举报列表容器 */
.report-list-container {
  max-width: 1400px;
  margin: 0 auto;
}

/* 举报表格 */
.report-table-wrapper {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
}

.report-table th {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  font-weight: 600;
  text-align: left;
  padding: 20px;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.report-table th:first-child {
  border-radius: 20px 0 0 0;
}

.report-table th:last-child {
  border-radius: 0 20px 0 0;
}

.report-table td {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.report-table tr:last-child td {
  border-bottom: none;
}

.report-table tbody tr:hover {
  background: rgba(255, 107, 157, 0.05);
}

.report-table tbody tr.row-pending {
  background: rgba(255, 167, 38, 0.05);
}

.report-table tbody tr.row-pending:hover {
  background: rgba(255, 167, 38, 0.1);
}

/* ID列 */
.col-id {
  width: 80px;
}

.report-id {
  font-weight: 600;
  color: #ff6b9d;
  font-size: 14px;
}

/* 举报人列 */
.col-reporter {
  width: 150px;
}

.user-cell {
  display: flex;
  align-items: center;
}

.user-info-small {
  flex: 1;
}

.username {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  font-size: 14px;
}

.user-id {
  color: #999;
  font-size: 12px;
}

/* 举报对象列 */
.col-target {
  min-width: 200px;
}

.target-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.target-type {
  font-weight: 600;
  color: #666;
  font-size: 13px;
}

.target-id {
  color: #999;
  font-size: 11px;
}

.target-preview {
  color: #666;
  font-size: 12px;
  line-height: 1.4;
  background: rgba(0, 0, 0, 0.03);
  padding: 4px 8px;
  border-radius: 6px;
  margin-top: 4px;
}

/* 举报类型列 */
.col-category {
  width: 120px;
}

.category-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  position: relative;
  min-width: 80px;
  text-align: center;
  letter-spacing: 0.3px;
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

.category-spoiler {
  background: linear-gradient(135deg, #0033ff, #4d53ff);
  border: 2px solid #00b3ff;
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.category-spoiler::after {
  content: "";
  position: absolute;
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: 6px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  box-shadow: 0 0 4px rgba(255, 152, 0, 0.5);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: translateY(-50%) scale(1);
    opacity: 0.8;
  }
  50% {
    transform: translateY(-50%) scale(1.3);
    opacity: 1;
  }
}

/* 举报理由列 */
.col-reason {
  min-width: 200px;
  max-width: 300px;
}

.reason-text {
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}

/* 状态列 */
.col-status {
  width: 100px;
}

/* 日期列 */
.col-date {
  width: 140px;
}

.date-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.date-value {
  color: #333;
  font-size: 13px;
  font-weight: 500;
}

.date-ago {
  color: #999;
  font-size: 11px;
}

/* 操作列 */
.col-actions {
  width: 160px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-action {
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-view {
  background: linear-gradient(135deg, #42a5f5, #64b5f6);
  color: white;
}

.btn-view:hover {
  background: linear-gradient(135deg, #1e88e5, #42a5f5);
  transform: translateY(-2px);
}

.btn-handle {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.btn-handle:hover:not(:disabled) {
  background: linear-gradient(135deg, #ff4081, #ff6b9d);
  transform: translateY(-2px);
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.pagination-info {
  color: #666;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-btn {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #ffc2d9;
  border-radius: 20px;
  padding: 10px 16px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #ff6b9d;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  background: #ff6b9d;
  color: white;
  transform: translateY(-2px);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number {
  background: rgba(255, 255, 255, 0.95);
  border: 2px solid #ffc2d9;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  color: #ff6b9d;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.page-number:hover {
  background: rgba(255, 107, 157, 0.2);
  transform: scale(1.1);
}

.page-number.active {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border-color: #ff6b9d;
}

/* 消息提示 */
.message-alert {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 2000;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  animation: slideInRight 0.3s ease;
  max-width: 400px;
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.message-alert.success {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

.message-alert.error {
  background: linear-gradient(135deg, #ff4081, #ff6b9d);
  color: white;
}

.message-alert.info {
  background: linear-gradient(135deg, #2196f3, #42a5f5);
  color: white;
}

.message-alert i {
  font-size: 18px;
}

.close-message {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 14px;
  margin-left: auto;
  padding: 4px;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.close-message:hover {
  opacity: 1;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .report-table {
    display: block;
    overflow-x: auto;
  }

  .report-table th,
  .report-table td {
    white-space: nowrap;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 28px;
  }

  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-controls {
    width: 100%;
  }

  .status-filter-btn {
    flex: 1;
    justify-content: center;
  }

  .refresh-btn {
    width: 100%;
    justify-content: center;
  }

  .stats-section {
    grid-template-columns: 1fr;
  }

  .pagination {
    flex-direction: column;
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 24px;
    flex-direction: column;
    gap: 10px;
  }

  .message-alert {
    left: 10px;
    right: 10px;
    max-width: none;
  }
}
</style>
