<template>
  <div class="user-management-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <i class="fas fa-users-cog"></i>
        用户管理
      </h1>
      <p class="page-subtitle">管理用户账号状态，维护平台秩序</p>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="filter-section">
      <div class="search-box">
        <i class="fas fa-search"></i>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索用户名、邮箱或昵称..."
          @input="handleSearch"
        />
        <button
          v-if="searchQuery"
          class="clear-btn"
          @click="clearSearch"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="filter-controls">
        <select v-model="statusFilter" @change="handleFilterChange" class="filter-select">
          <option value="">全部状态</option>
          <option value="active">正常用户</option>
          <option value="banned">已封禁用户</option>
        </select>

        <select v-model="sortBy" @change="handleFilterChange" class="filter-select">
          <option value="-date_joined">最新注册</option>
          <option value="date_joined">最早注册</option>
          <option value="-last_login">最近登录</option>
          <option value="last_login">最早登录</option>
          <option value="username">用户名 A-Z</option>
          <option value="-username">用户名 Z-A</option>
        </select>

        <button class="refresh-btn" @click="fetchUserList(true)" :disabled="loading">
          <i class="fas fa-redo" :class="{ 'fa-spin': loading }"></i>
          刷新
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && users.length === 0" class="loading-state">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
      </div>
      <p>加载用户数据中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="fetchUserList(true)">
        <i class="fas fa-redo"></i>
        重试
      </button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && users.length === 0" class="empty-state">
      <div class="empty-icon">
        <i class="fas fa-user-slash"></i>
      </div>
      <h3>暂无用户</h3>
      <p>{{ searchQuery ? '没有找到匹配的用户' : '还没有任何用户数据' }}</p>
    </div>

    <!-- 用户列表 -->
    <div v-else class="user-list-container">
      <!-- 统计信息 -->
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ pagination.total }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon active">
            <i class="fas fa-user-check"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ activeUsersCount }}</div>
            <div class="stat-label">正常用户</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon banned">
            <i class="fas fa-user-slash"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ bannedUsersCount }}</div>
            <div class="stat-label">已封禁用户</div>
          </div>
        </div>
      </div>

      <!-- 用户表格 -->
      <div class="user-table-wrapper">
        <table class="user-table">
          <thead>
            <tr>
              <th class="col-user">用户</th>
              <th class="col-status">状态</th>
              <th class="col-stats">统计数据</th>
              <th class="col-date">注册时间</th>
              <th class="col-last-login">最后登录</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.user_id">
              <!-- 用户信息列 -->
              <td class="col-user">
                <div class="user-cell">
                  <div class="user-avatar-small">
                    <img 
                      :src="user.profile?.avatar || '/default-avatar.png'" 
                      :alt="user.username"
                      class="avatar-small"
                    />
                  </div>
                  <div class="user-info-small">
                    <div class="username">{{ user.username }}</div>
                    <div class="user-email-small">{{ user.email }}</div>
                    <div class="user-id">ID: {{ user.user_id }}</div>
                  </div>
                </div>
              </td>

              <!-- 状态列 -->
              <td class="col-status">
                <UserStatusBadge 
                  :status="user.status" 
                  :text="user.status"
                  size="small"
                />
                <div v-if="user.recent_ban_info && !user.is_active" class="ban-info">
                  <small class="ban-reason" :title="user.recent_ban_info.reason">
                    <i class="fas fa-info-circle"></i>
                    {{ truncateText(user.recent_ban_info.reason, 20) }}
                  </small>
                </div>
              </td>

              <!-- 统计数据列 -->
              <td class="col-stats">
                <div class="user-stats">
                  <div class="stat-item">
                    <i class="fas fa-comment"></i>
                    <span>{{ user.stats?.total_comments || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-reply"></i>
                    <span>{{ user.stats?.total_replies || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <i class="fas fa-film"></i>
                    <span>{{ user.stats?.animes_created || 0 }}</span>
                  </div>
                </div>
              </td>

              <!-- 注册时间列 -->
              <td class="col-date">
                <div class="date-cell">
                  <div class="date-value">{{ formatDate(user.date_joined) }}</div>
                  <div class="date-ago">{{ timeAgo(user.date_joined) }}</div>
                </div>
              </td>

              <!-- 最后登录列 -->
              <td class="col-last-login">
                <div class="date-cell">
                  <div class="date-value">{{ formatDate(user.last_login) }}</div>
                  <div class="date-ago">{{ timeAgo(user.last_login) }}</div>
                </div>
              </td>

              <!-- 操作列 -->
              <td class="col-actions">
                <div class="action-buttons">
                  <button
                    v-if="user.is_active"
                    class="btn-action btn-ban"
                    @click="openBanModal(user)"
                    :disabled="actionLoading[user.user_id]"
                  >
                    <i class="fas fa-ban"></i>
                    封禁
                  </button>
                  <button
                    v-else
                    class="btn-action btn-unban"
                    @click="openUnbanModal(user)"
                    :disabled="actionLoading[user.user_id]"
                  >
                    <i class="fas fa-check-circle"></i>
                    解封
                  </button>
                  <button
                    class="btn-action btn-details"
                    @click="viewUserDetails(user.user_id)"
                  >
                    <i class="fas fa-info-circle"></i>
                    详情
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

    <!-- 操作模态框 -->
    <UserActionModal
      v-model:visible="showActionModal"
      :action-type="currentAction"
      :user="selectedUser"
      @confirm="handleActionConfirm"
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
import { useRouter } from 'vue-router'
import { getUserList, banUser, unbanUser } from '@/services/adminService.js'
import UserStatusBadge from './UserStatusBadge.vue'
import UserActionModal from './UserActionModal.vue'

const router = useRouter()

// 状态管理
const loading = ref(false)
const error = ref('')
const users = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('-date_joined')

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 120,
  total: 0,
  total_pages: 0
})

// 操作状态
const showActionModal = ref(false)
const currentAction = ref('ban') // 'ban' 或 'unban'
const selectedUser = ref(null)
const actionLoading = ref({}) // 记录每个用户的操作加载状态
const message = reactive({
  show: false,
  type: 'success', // 'success' 或 'error'
  text: '',
  icon: 'fas fa-check-circle'
})

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

const activeUsersCount = computed(() => {
  return users.value.filter(user => user.is_active).length
})

const bannedUsersCount = computed(() => {
  return users.value.filter(user => !user.is_active).length
})

// 获取用户列表
const fetchUserList = async (resetPage = false) => {
  if (resetPage) {
    pagination.page = 1
  }

  loading.value = true
  error.value = ''

  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      search: searchQuery.value || undefined,
      status: statusFilter.value || undefined,
      order_by: sortBy.value
    }

    const response = await getUserList(params)

    if (response?.code === 200 && response.data) {
      const data = response.data
      
      // 提取用户列表
      users.value = data.users || []
      
      // 更新分页信息
      if (data.pagination) {
        pagination.page = data.pagination.page || 1
        pagination.page_size = data.pagination.page_size || 20
        pagination.total = data.pagination.total || 0
        pagination.total_pages = data.pagination.total_pages || 0
      }
    } else {
      throw new Error(response?.message || '获取用户列表失败')
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('获取用户列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 处理搜索
let searchTimeout = null
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchUserList(true)
  }, 500)
}

// 清除搜索
const clearSearch = () => {
  searchQuery.value = ''
  fetchUserList(true)
}

// 处理筛选变化
const handleFilterChange = () => {
  fetchUserList(true)
}

// 跳转到指定页
const goToPage = (page) => {
  if (page < 1 || page > pagination.total_pages) return
  pagination.page = page
  fetchUserList()
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 打开封禁模态框
const openBanModal = (user) => {
  selectedUser.value = {
    ...user,
    status: user.is_active ? '正常' : '已封禁'
  }
  currentAction.value = 'ban'
  showActionModal.value = true
}

// 打开解封模态框
const openUnbanModal = (user) => {
  selectedUser.value = {
    ...user,
    status: user.is_active ? '正常' : '已封禁'
  }
  currentAction.value = 'unban'
  showActionModal.value = true
}

// 关闭操作模态框
const closeActionModal = () => {
  showActionModal.value = false
  selectedUser.value = null
}

// 处理操作确认
const handleActionConfirm = async (actionData) => {
  if (!selectedUser.value) return

  const userId = selectedUser.value.user_id
  actionLoading.value[userId] = true

  try {
    let response
    if (currentAction.value === 'ban') {
      response = await banUser(userId, actionData)
    } else {
      response = await unbanUser(userId, actionData)
    }

    if (response?.code === 200) {
      // 显示成功消息
      showMessage(
        currentAction.value === 'ban' ? '用户封禁成功' : '用户解封成功',
        'success',
        currentAction.value === 'ban' ? 'fas fa-ban' : 'fas fa-check-circle'
      )
      
      // 关闭模态框
      closeActionModal()
      
      // 刷新用户列表
      setTimeout(() => {
        fetchUserList()
      }, 500)
    } else {
      throw new Error(response?.message || '操作失败')
    }

  } catch (err) {
    showMessage(
      err.message || '操作失败，请稍后重试',
      'error',
      'fas fa-exclamation-circle'
    )
    console.error('用户操作失败:', err)
  } finally {
    actionLoading.value[userId] = false
  }
}

// 查看用户详情
const viewUserDetails = (userId) => {
  // 这里可以跳转到用户详情页面
  // router.push(`/admin/users/${userId}/details`)
  showMessage('用户详情功能开发中', 'info', 'fas fa-info-circle')
}

// 显示消息提示
const showMessage = (text, type = 'success', icon = 'fas fa-check-circle') => {
  message.text = text
  message.type = type
  message.icon = icon
  message.show = true
  
  // 3秒后自动隐藏
  setTimeout(() => {
    message.show = false
  }, 3000)
}

// 工具函数
const formatDate = (dateString) => {
  if (!dateString) return '从未'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const timeAgo = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

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
  fetchUserList()
})
</script>

<style scoped>
.user-management-page {
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

/* 搜索和筛选 */
.filter-section {
  max-width: 1400px;
  margin: 0 auto 30px;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 300px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-box i.fa-search {
  position: absolute;
  left: 20px;
  color: #ff6b9d;
  font-size: 18px;
}

.search-box input {
  width: 100%;
  padding: 15px 50px 15px 50px;
  border: 2px solid #ffc2d9;
  border-radius: 25px;
  font-family: inherit;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.95);
  transition: all 0.3s ease;
}

.search-box input:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

.clear-btn {
  position: absolute;
  right: 15px;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 16px;
  padding: 5px;
  transition: color 0.3s ease;
}

.clear-btn:hover {
  color: #ff6b9d;
}

.filter-controls {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.filter-select {
  padding: 15px 20px;
  border: 2px solid #ffc2d9;
  border-radius: 25px;
  font-family: inherit;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.95);
  cursor: pointer;
  transition: all 0.3s ease;
  color: #333;
  min-width: 150px;
}

.filter-select:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

.refresh-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 25px;
  padding: 15px 24px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
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

/* 加载和错误状态 */
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
  color: #ffc2d9;
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
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
}

.stat-icon.active {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
}

.stat-icon.banned {
  background: linear-gradient(135deg, #ff4081, #ff6b9d);
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

/* 用户表格 */
.user-list-container {
  max-width: 1400px;
  margin: 0 auto;
}

.user-table-wrapper {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  font-weight: 600;
  text-align: left;
  padding: 20px;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.user-table th:first-child {
  border-radius: 20px 0 0 0;
}

.user-table th:last-child {
  border-radius: 0 20px 0 0;
}

.user-table td {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.user-table tr:last-child td {
  border-bottom: none;
}

.user-table tr:hover {
  background: rgba(255, 107, 157, 0.05);
}

/* 用户信息列 */
.user-cell {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-avatar-small {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #ff6b9d;
}

.avatar-small {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info-small {
  flex: 1;
}

.username {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  font-size: 16px;
}

.user-email-small {
  color: #666;
  font-size: 13px;
  margin-bottom: 4px;
}

.user-id {
  color: #999;
  font-size: 12px;
}

/* 状态列 */
.col-status {
  min-width: 120px;
}

.ban-info {
  margin-top: 8px;
}

.ban-reason {
  color: #ff4081;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 统计数据列 */
.user-stats {
  display: flex;
  gap: 15px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  font-size: 13px;
}

.stat-item i {
  color: #ff6b9d;
  font-size: 12px;
}

/* 日期列 */
.date-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.date-value {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.date-ago {
  color: #999;
  font-size: 12px;
}

/* 操作列 */
.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-action {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ban {
  background: linear-gradient(135deg, #ff4081, #ff6b9d);
  color: white;
}

.btn-ban:hover:not(:disabled) {
  background: linear-gradient(135deg, #e91e63, #ff4081);
  transform: translateY(-2px);
}

.btn-unban {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

.btn-unban:hover:not(:disabled) {
  background: linear-gradient(135deg, #388e3c, #4caf50);
  transform: translateY(-2px);
}

.btn-details {
  background: #f5f5f5;
  color: #666;
}

.btn-details:hover {
  background: #e0e0e0;
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
  .user-table {
    display: block;
    overflow-x: auto;
  }
  
  .user-table th,
  .user-table td {
    white-space: nowrap;
  }
}

@media (max-width: 768px) {
  .page-header {
    margin-bottom: 20px;
  }
  
  .page-title {
    font-size: 28px;
  }
  
  .filter-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    min-width: 100%;
  }
  
  .filter-controls {
    flex-direction: column;
    width: 100%;
  }
  
  .filter-select {
    width: 100%;
  }
  
  .stats-section {
    grid-template-columns: 1fr;
  }
  
  .user-table-wrapper {
    border-radius: 15px;
  }
  
  .user-table th,
  .user-table td {
    padding: 12px 8px;
    font-size: 13px;
  }
  
  .user-cell {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .user-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .btn-action {
    width: 100%;
    justify-content: center;
  }
  
  .pagination {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .pagination-controls {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 24px;
    flex-direction: column;
    gap: 10px;
  }
  
  .refresh-btn {
    width: 100%;
    justify-content: center;
  }
  
  .message-alert {
    left: 10px;
    right: 10px;
    max-width: none;
  }
}
</style>
