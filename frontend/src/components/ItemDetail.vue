<template>
  <div class="item-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
      </div>
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <h3>{{ error }}</h3>
      <div class="error-actions">
        <button class="btn btn-retry" @click="fetchItemDetail">
          <i class="fas fa-redo"></i>
          重试
        </button>
        <button class="btn btn-back" @click="goBack">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
      </div>
    </div>

    <!-- 详情内容 -->
    <main class="detail-content" v-else-if="itemDetail">
      <!-- 顶部信息区 -->
      <div class="item-header">
        <div class="cover-section">
          <img
            :src="getFullImageUrl(itemDetail.basic?.cover) || 'https://via.placeholder.com/280x400/ff6b9d/ffffff?text=暂无封面'"
            :alt="itemDetail.basic?.title"
            class="detail-cover"
          />
        </div>

        <div class="info-section">
          <div class="title-section">
            <h1 class="detail-title">{{ itemDetail.basic?.title }}</h1>
            <span :class="['item-badge', { 'anime-badge': isAnime }]">
              {{ isAnime ? '番剧' : '条目' }}
            </span>
          </div>

          <div class="creator-info" v-if="itemDetail.meta?.createdBy">
            <div class="creator-avatar">
              <i class="fas fa-user"></i>
            </div>
            <div class="creator-text">
              <span class="creator-label">创建者</span>
              <span class="creator-name">{{ itemDetail.meta.createdBy }}</span>
            </div>
          </div>

            <div class="meta-info">
            <div class="meta-item" v-if="itemDetail.meta?.createdAt">
              <i class="fas fa-calendar-alt"></i>
              <span>创建时间: {{ formatTime(itemDetail.meta.createdAt) }}</span>
            </div>
            <div class="meta-item" v-if="itemDetail.meta?.updatedAt && itemDetail.meta?.updatedAt !== itemDetail.meta?.createdAt">
              <i class="fas fa-edit"></i>
              <span>更新时间: {{ formatTime(itemDetail.meta.updatedAt) }}</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-fire"></i>
              <span>人气: {{ formatNumber(itemDetail.basic?.popularity || 0) }}</span>
            </div>
          </div>

            <!-- 操作按钮 -->
            <div class="actions">
              <!-- 编辑按钮(仅创建者和管理员可见) -->
              <button
                v-if="canEdit"
                class="action-btn edit"
                @click="openEditModal"
                :disabled="editing"
              >
                <i class="fas fa-edit" v-if="!editing"></i>
                <i class="fas fa-spinner fa-spin" v-else></i>
                {{ editing ? '编辑中...' : '编辑' }}
              </button>
              <!-- 删除按钮(仅创建者可见) -->
              <button
                v-if="canDelete"
                class="action-btn delete"
                @click="confirmDelete"
                :disabled="deleting"
              >
                <i class="fas fa-trash" v-if="!deleting"></i>
                <i class="fas fa-spinner fa-spin" v-else></i>
                {{ deleting ? '删除中...' : '删除' }}
              </button>
            </div>
        </div>
      </div>

      <!-- 详情标签页 -->
      <div class="detail-tabs">
        <div class="tab-nav">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="handleTabChange(tab.id)"
          >
            <i :class="tab.icon"></i>
            {{ tab.label }}
          </button>
        </div>

        <div class="tab-content">
          <!-- 详情标签页 -->
          <div v-if="activeTab === 'details'" class="tab-panel details-panel">
            <h3>条目详情</h3>

            <div class="detail-grid">
              <div class="detail-card">
                <div class="detail-card-header">
                  <i class="fas fa-info-circle"></i>
                  <span>基本信息</span>
                </div>
                <div class="detail-card-body">
                  <div class="detail-item">
                    <span class="label">标题:</span>
                    <span class="value">{{ itemDetail.basic?.title || '未知' }}</span>
                  </div>
                  <div class="detail-item" v-if="itemDetail.basic?.titleJapanese">
                    <span class="label">中文标题:</span>
                    <span class="value">{{ itemDetail.basic.titleJapanese }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">类型:</span>
                    <span class="value item-type">用户创建条目</span>
                  </div>
                </div>
              </div>

              <div class="detail-card">
                <div class="detail-card-header">
                  <i class="fas fa-file-text"></i>
                  <span>条目介绍</span>
                </div>
                <div class="detail-card-body">
                  <p class="description-text">
                    {{ itemDetail.basic?.summary || '暂无介绍' }}
                  </p>
                </div>
              </div>

              <div class="detail-card">
                <div class="detail-card-header">
                  <i class="fas fa-chart-line"></i>
                  <span>统计信息</span>
                </div>
                <div class="detail-card-body">
                  <div class="detail-item">
                    <span class="label">评分:</span>
                    <span class="value">{{ formatRating(itemDetail.basic?.rating) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">人气:</span>
                    <span class="value">{{ formatNumber(itemDetail.basic?.popularity || 0) }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="label">评论数:</span>
                    <span class="value">{{ formatNumber(itemDetail.comments?.list?.length || 0) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 评论标签页 -->
          <div v-if="activeTab === 'comments'" class="tab-panel comments-panel">
            <h3>用户评论</h3>

            <!-- 加载状态 -->
            <div v-if="commentsLoading" class="loading-comments">
              <i class="fas fa-spinner fa-spin"></i>
              <span>加载评论中...</span>
            </div>

            <!-- 错误状态 -->
            <div v-else-if="commentsError" class="error-comments">
              <i class="fas fa-exclamation-triangle"></i>
              <span>{{ commentsError }}</span>
              <button @click="fetchComments" class="retry-btn">重试</button>
            </div>

            <!-- 正常状态 -->
            <div v-else>
              <!-- 评论表单组件 -->
              <ReviewForm
                :animeId="itemId"
                :commentType="'ITEM'"
                @review-submitted="handleReviewSubmitted"
                @review-updated="handleReviewUpdated"
              />

              <!-- 评论列表组件 -->
              <ReviewList
                :reviews="comments"
                @reply-submitted="handleReplySubmitted"
                @review-liked="handleReviewLiked"
              />

              <!-- 空状态提示 -->
              <div v-if="comments.length === 0" class="no-comments">
                <i class="fas fa-comments"></i>
                <p>暂无评论，快来发表第一个评论吧！</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 编辑条目模态框 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑条目</h3>
          <button class="modal-close" @click="closeEditModal">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="handleEditSubmit" class="edit-form">
            <!-- 标题输入 -->
            <div class="form-group">
              <label class="form-label required">
                <i class="fas fa-heading"></i>
                条目标题
              </label>
              <input
                v-model="editForm.title"
                type="text"
                class="form-input"
                placeholder="请输入条目标题"
                maxlength="200"
                @blur="validateEditTitle"
              />
              <span v-if="editErrors.title" class="error-text">{{ editErrors.title }}</span>
            </div>

            <!-- 描述输入 -->
            <div class="form-group">
              <label class="form-label">
                <i class="fas fa-file-text"></i>
                条目描述
              </label>
              <textarea
                v-model="editForm.description"
                class="form-textarea"
                placeholder="请输入条目描述"
                rows="4"
                maxlength="1000"
                @blur="validateEditDescription"
              ></textarea>
              <span v-if="editErrors.description" class="error-text">{{ editErrors.description }}</span>
            </div>

            <!-- 封面图片上传 -->
            <div class="form-group">
              <label class="form-label">
                <i class="fas fa-image"></i>
                封面图片
              </label>

              <!-- 文件上传区域 -->
              <div class="file-upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
                <div v-if="!editForm.coverFile && !editForm.cover" class="upload-placeholder">
                  <i class="fas fa-cloud-upload-alt"></i>
                  <p>点击或拖拽上传图片</p>
                  <p class="upload-hint">支持 JPG、PNG、GIF 格式，最大 5MB</p>
                </div>

                <div v-else-if="editForm.coverFile" class="file-preview">
                  <img :src="getFilePreview(editForm.coverFile)" alt="预览" class="preview-image" />
                  <div class="file-info">
                    <p class="file-name">{{ editForm.coverFile.name }}</p>
                    <p class="file-size">{{ formatFileSize(editForm.coverFile.size) }}</p>
                    <button type="button" class="remove-file-btn" @click.stop="removeCoverFile">
                      <i class="fas fa-times"></i>
                      移除
                    </button>
                  </div>
                </div>

                <div v-else-if="editForm.cover" class="current-cover">
                  <img :src="getFullImageUrl(editForm.cover)" alt="当前封面" class="preview-image" />
                  <div class="file-info">
                    <p class="current-label">当前封面</p>
                    <p class="file-url">{{ editForm.cover }}</p>
                    <button type="button" class="remove-file-btn" @click.stop="removeCoverUrl">
                      <i class="fas fa-times"></i>
                      移除
                    </button>
                  </div>
                </div>

                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  class="file-input"
                  @change="handleFileSelect"
                  style="display: none;"
                />
              </div>

              </div>

            <!-- 表单操作按钮 -->
            <div class="form-actions">
              <button
                type="button"
                class="btn btn-cancel"
                @click="closeEditModal"
                :disabled="editing"
              >
                取消
              </button>
              <button
                type="submit"
                class="btn btn-submit"
                :disabled="editing"
              >
                <i class="fas fa-check" v-if="!editing"></i>
                <i class="fas fa-spinner fa-spin" v-else></i>
                {{ editing ? '保存中...' : '保存修改' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItemDetail, deleteItem, getFullImageUrl, updateItem } from '@/services/itemService.js'
import { getComments } from '@/services/commentService.js'
import ReviewForm from './ReviewForm.vue'
import ReviewList from './ReviewList.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const error = ref('')
const itemDetail = ref(null)
const activeTab = ref('details')
const deleting = ref(false)
const editing = ref(false)

// 编辑相关数据
const showEditModal = ref(false)
const fileInput = ref(null)
const editForm = ref({
  title: '',
  description: '',
  coverFile: null
})
const editErrors = ref({
  title: '',
  description: ''
})

// 评论相关数据
const comments = ref([])
const commentsLoading = ref(false)
const commentsError = ref('')

// 标签页配置
const tabs = ref([
  { id: 'details', label: '详情', icon: 'fas fa-info-circle' },
  { id: 'comments', label: '评论', icon: 'fas fa-comments' }
])

// 计算属性
const itemId = computed(() => route.params.id)

const isAnime = computed(() => {
  // 根据is_admin字段判断是否为番剧
  // 注意：is_admin字段在meta中，不在basic中
  return itemDetail.value?.meta?.isAdmin === true
})

const canDelete = computed(() => {
  // 检查是否为条目创建者
  // 从localStorage中获取当前用户名
  const currentUsername = localStorage.getItem('username') || ''
  const creatorUsername = itemDetail.value?.meta?.createdBy
  
  // 检查是否是管理员
  const token = localStorage.getItem('access_token')
  let isAdmin = false
  
  if (token) {
    try {
      // JWT token的payload部分
      const payload = JSON.parse(atob(token.split('.')[1]))
      
      // 检查是否是管理员
      if (payload.is_staff !== undefined) {
        isAdmin = payload.is_staff === true || payload.is_staff === 'true'
      } else if (payload.is_superuser !== undefined) {
        isAdmin = payload.is_superuser === true || payload.is_superuser === 'true'
      } else if (payload.is_admin !== undefined) {
        isAdmin = payload.is_admin === true || payload.is_admin === 'true'
      } else if (payload.role !== undefined) {
        // 检查角色字段
        isAdmin = payload.role === 'admin' || payload.role === 'administrator' || payload.role === 'staff'
      }
    } catch (e) {
      // 忽略解析错误
    }
  }
  
  // 如果是管理员，可以删除任何条目
  if (isAdmin) {
    return true
  }
  
  // 如果是创建者，可以删除
  return currentUsername && creatorUsername && currentUsername === creatorUsername
})

const canEdit = computed(() => {
  // 所有用户都可以看到编辑按钮
  // 实际权限检查在提交时进行
  return true
})

// 获取当前用户ID
const getCurrentUserId = () => {
  // 从localStorage或其他地方获取当前用户ID
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  return userInfo.id || null
}

// 获取条目详情
const fetchItemDetail = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await getItemDetail(itemId.value)

    if (response?.code === 0 && response.data) {
      itemDetail.value = response.data
    } else {
      throw new Error(response?.message || '条目不存在')
    }

  } catch (err) {
    error.value = err.message || '加载失败，请稍后重试'
    console.error('加载条目详情失败:', err)
  } finally {
    loading.value = false
  }
}

// 格式化时间
const formatTime = (timeString) => {
  if (!timeString) return '未知'
  return new Date(timeString).toLocaleString('zh-CN')
}

// 格式化数字
const formatNumber = (num) => {
  if (!num || num === 0) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 格式化评分
const formatRating = (rating) => {
  if (!rating) return '暂无评分'
  return rating.toFixed(1) + ' 分'
}

 

// 复制链接到剪贴板
const copyToClipboard = () => {
  navigator.clipboard.writeText(window.location.href).then(() => {
    showToast('链接已复制到剪贴板', 'success')
  }).catch(() => {
    showToast('复制失败，请手动复制链接', 'error')
  })
}

// 确认删除
const confirmDelete = () => {
  const title = itemDetail.value?.basic?.title || '此条目'
  if (confirm(`确定要删除"${title}"吗？\n\n删除后将无法恢复。`)) {
    handleDelete()
  }
}

// 处理删除
const handleDelete = async () => {
  deleting.value = true

  try {
    const response = await deleteItem(itemId.value)

    if (response?.code === 0) {
      showToast('条目删除成功', 'success')
      // 延迟跳转到列表页
      setTimeout(() => {
        router.push('/items')
      }, 1500)
    } else {
      throw new Error(response?.message || '删除失败')
    }
  } catch (err) {
    console.error('删除条目失败:', err)
    // 检查是否是权限错误
    if (err.message === "没有权限删除此条目") {
      alert("没有权限删除此条目")
    } else {
      showToast(err.message || '删除失败，请稍后重试', 'error')
    }
  } finally {
    deleting.value = false
  }
}

// 处理评论相关事件
const handleReviewSubmitted = async (data) => {
  console.log('评论已提交:', data)
  // 重新加载评论列表
  await fetchComments()
  showToast('评论提交成功', 'success')
}

const handleReviewUpdated = async (data) => {
  console.log('评论已更新:', data)
  // 重新加载评论列表
  await fetchComments()
  showToast('评论更新成功', 'success')
}

const handleReplySubmitted = async (data) => {
  console.log('回复已提交:', data)
  // 重新加载评论列表
  await fetchComments()
  showToast('回复提交成功', 'success')
}

const handleReviewLiked = async (data) => {
  console.log('评论已点赞:', data)
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 显示提示
const showToast = (message, type = 'info') => {
  const toast = document.createElement('div')
  toast.className = `toast toast-${type}`
  toast.innerHTML = `
    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
    ${message}
  `
  document.body.appendChild(toast)

  setTimeout(() => {
    toast.classList.add('show')
  }, 100)

  setTimeout(() => {
    toast.classList.remove('show')
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, 3000)
}

// 获取评论列表
const fetchComments = async () => {
  commentsLoading.value = true
  commentsError.value = ''

  try {
    console.log('开始获取条目评论，itemId:', itemId.value, ', type:', typeof itemId.value)

    const response = await getComments('ITEM', parseInt(itemId.value), {
      page: 1,
      pageSize: 20,
      orderBy: 'time_desc'
    })

    console.log('评论API完整响应:', response)

    if (response?.code === 200 && response.data) {
      const rawComments = response.data.comments || []
      console.log('原始评论数据:', rawComments)
      console.log('评论总数:', response.data.total_comments)

      // 标准化评论数据结构，确保前端组件能正确识别字段
      comments.value = rawComments.map(comment => ({
        ...comment,
        reviewId: comment.comment_id,        // 标准化为reviewId
        likes: comment.likes_count || 0,     // 标准化为likes
        isLiked: comment.is_liked || false,  // 标准化为isLiked
        user: comment.author?.username || '匿名用户', // 标准化为user
        score: comment.score,
        content: comment.content,
        createdAt: comment.created_at,
        replyCount: comment.replies_count || 0
      }))

      console.log('标准化后的评论数据:', comments.value)
      console.log('评论列表长度:', comments.value.length)
    } else {
      console.error('评论数据响应不正确:', response)
      throw new Error(response?.message || '获取评论失败')
    }
  } catch (err) {
    console.error('获取条目评论失败:', err)
    console.error('错误详情:', err.response?.data || err.message)
    commentsError.value = err.response?.data?.message || err.message || '加载评论失败，请稍后重试'
  } finally {
    commentsLoading.value = false
  }
}

// 处理标签页切换
const handleTabChange = (tabId) => {
  activeTab.value = tabId

  // 当切换到评论标签页时自动加载评论
  if (tabId === 'comments' && comments.value.length === 0 && !commentsLoading.value) {
    fetchComments()
  }
}

// 打开编辑模态框
const openEditModal = () => {
  // 填充表单数据
  editForm.value = {
    title: itemDetail.value?.basic?.title || '',
    description: itemDetail.value?.basic?.summary || '',
    coverFile: null
  }

  // 清空错误信息
  editErrors.value = {
    title: '',
    description: ''
  }

  showEditModal.value = true
}


// 关闭编辑模态框
const closeEditModal = () => {
  if (!editing.value) {
    showEditModal.value = false
  }
}

// 触发文件输入
const triggerFileInput = () => {
  fileInput.value?.click()
}

// 处理文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    showToast('请选择图片文件', 'error')
    return
  }

  // 验证文件大小（最大5MB）
  const maxSize = 5 * 1024 * 1024 // 5MB
  if (file.size > maxSize) {
    showToast('文件大小不能超过5MB', 'error')
    return
  }

  // 设置文件并清空URL输入
  editForm.value.coverFile = file
  editForm.value.cover = ''
  editErrors.value.cover = ''
}

// 处理拖放
const handleDrop = (event) => {
  event.preventDefault()
  const file = event.dataTransfer.files[0]
  if (!file) return

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    showToast('请拖放图片文件', 'error')
    return
  }

  // 验证文件大小（最大5MB）
  const maxSize = 5 * 1024 * 1024 // 5MB
  if (file.size > maxSize) {
    showToast('文件大小不能超过5MB', 'error')
    return
  }

  // 设置文件并清空URL输入
  editForm.value.coverFile = file
  editForm.value.cover = ''
  editErrors.value.cover = ''
}

// 获取文件预览URL
const getFilePreview = (file) => {
  return URL.createObjectURL(file)
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 移除封面文件
const removeCoverFile = () => {
  editForm.value.coverFile = null
  // 释放预览URL
  if (editForm.value.coverFile) {
    URL.revokeObjectURL(getFilePreview(editForm.value.coverFile))
  }
}

// 移除封面URL
const removeCoverUrl = () => {
  editForm.value.cover = ''
}


// 验证编辑标题
const validateEditTitle = () => {
  editErrors.value.title = ''
  if (!editForm.value.title.trim()) {
    editErrors.value.title = '请输入条目标题'
    return false
  }
  if (editForm.value.title.length > 200) {
    editErrors.value.title = '标题长度不能超过200个字符'
    return false
  }
  return true
}

// 验证编辑描述
const validateEditDescription = () => {
  editErrors.value.description = ''
  if (editForm.value.description.length > 1000) {
    editErrors.value.description = '描述长度不能超过1000个字符'
    return false
  }
  return true
}


// 验证编辑表单
const validateEditForm = () => {
  const isTitleValid = validateEditTitle()
  const isDescriptionValid = validateEditDescription()
  return isTitleValid && isDescriptionValid
}

// 处理编辑提交
const handleEditSubmit = async () => {
  if (!validateEditForm()) return

  const token = localStorage.getItem("access_token")
  if (!token) {
    alert("请先登录")
    router.push("/login")
    return
  }

  try {
    editing.value = true

    // 构建更新数据
    const updateData = {
      title: editForm.value.title,
      description: editForm.value.description
    }

    // 检查是否有实际变化
    const hasTitleChange = editForm.value.title !== itemDetail.value.basic.title
    const hasDescriptionChange = editForm.value.description !== itemDetail.value.basic.summary
    const hasCoverFileChange = !!editForm.value.coverFile

    if (!hasTitleChange && !hasDescriptionChange && !hasCoverFileChange) {
      showToast("没有检测到任何修改", "info")
      closeEditModal()
      return
    }

    // 如果没有变化，移除对应字段
    if (!hasTitleChange) {
      delete updateData.title
    }
    if (!hasDescriptionChange) {
      delete updateData.description
    }

    // 处理封面图片
    if (hasCoverFileChange) {
      updateData.coverFile = editForm.value.coverFile
    }

    // 直接使用已导入的 updateItem 函数
    const response = await updateItem(itemId.value, updateData)

    if (response.code === 0) {
      showToast("条目修改成功", "success")
      closeEditModal()
      await fetchItemDetail()
    } else {
      throw new Error(response.message || "修改失败")
    }

  } catch (err) {
    console.error("修改失败:", err)
    // 检查是否是权限错误
    if (err.message === "没有权限修改此条目") {
      alert("没有权限修改此条目")
    } else {
      showToast(err.message || "修改失败，请稍后再试", "error")
    }
  } finally {
    editing.value = false
  }
}


// 生命周期
onMounted(() => {
  fetchItemDetail()
})
</script>

<style scoped>
.item-detail-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
}

/* 加载和错误状态 */
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
}

.loading-spinner i {
  font-size: 48px;
  color: #ff6b9d;
  margin-bottom: 20px;
}

.error-icon i {
  font-size: 64px;
  color: #ff4081;
  margin-bottom: 20px;
}

.error-state h3 {
  color: #333;
  margin-bottom: 30px;
  font-size: 24px;
}

.error-actions {
  display: flex;
  gap: 15px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-retry {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
}

.btn-back {
  background: rgba(255, 255, 255, 0.9);
  color: #666;
  border: 2px solid #ddd;
}

.btn:hover {
  transform: translateY(-2px);
}

/* 详情内容 */
.detail-content {
  max-width: 1200px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 25px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 顶部信息区 */
.item-header {
  display: flex;
  gap: 40px;
  padding: 40px;
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.1), rgba(162, 210, 255, 0.1));
  border-bottom: 3px solid #ffc2d9;
}

.cover-section {
  flex-shrink: 0;
}

.detail-cover {
  width: 280px;
  height: 400px;
  object-fit: cover;
  border-radius: 20px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
  border: 4px solid white;
  transition: transform 0.3s ease;
}

.detail-cover:hover {
  transform: scale(1.02);
}

.info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.title-section {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  flex-wrap: wrap;
}

.detail-title {
  color: #333;
  font-size: 32px;
  margin: 0;
  text-shadow: 2px 2px 0 #ffc2d9;
  line-height: 1.2;
  flex: 1;
}

.item-badge {
  background: linear-gradient(135deg, #a2d2ff, #bde0fe);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(162, 210, 255, 0.3);
}

.anime-badge {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4) !important;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3) !important;
}

/* 创建者信息 */
.creator-info {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  border: 2px solid #ffc2d9;
}

.creator-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.creator-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.creator-label {
  color: #666;
  font-size: 14px;
}

.creator-name {
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

/* 元信息 */
.meta-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 15px;
  border: 2px solid #a2d2ff;
  transition: all 0.3s ease;
}

.meta-item:hover {
  background: rgba(162, 210, 255, 0.2);
  transform: translateX(5px);
}

.meta-item i {
  color: #ff6b9d;
  width: 20px;
  text-align: center;
}

.meta-item span {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

/* 操作按钮 */
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.action-btn {
  padding: 14px 24px;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}


.action-btn.share {
  background: rgba(255, 255, 255, 0.9);
  color: #ff6b9d;
  border: 2px solid #ffc2d9;
}

.action-btn.delete {
  background: linear-gradient(135deg, #ff4444, #ff6666);
  color: white;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(255, 107, 157, 0.4);
}

.action-btn i.active {
  color: #ff6b9d;
}

/* 标签页样式 */
.detail-tabs {
  background: rgba(255, 255, 255, 0.98);
}

.tab-nav {
  display: flex;
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.1), rgba(162, 210, 255, 0.1));
  border-bottom: 3px solid #ffc2d9;
}

.tab-btn {
  flex: 1;
  padding: 20px;
  border: none;
  background: none;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  font-family: inherit;
  font-size: 16px;
  font-weight: 500;
  position: relative;
}

.tab-btn::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 3px;
  background: #ff6b9d;
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.tab-btn:hover {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.05);
}

.tab-btn:hover::before,
.tab-btn.active::before {
  width: 80%;
}

.tab-btn.active {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.1);
}

.tab-content {
  padding: 40px;
}

/* 详情面板 */
.tab-panel h3 {
  color: #333;
  margin-bottom: 25px;
  font-size: 24px;
  text-shadow: 1px 1px 0 #ffc2d9;
  border-bottom: 3px solid #ffc2d9;
  padding-bottom: 10px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
}

.detail-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  border: 2px solid #ffc2d9;
}

.detail-card-header {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.detail-card-body {
  padding: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  color: #666;
  font-weight: 500;
}

.detail-item .value {
  color: #333;
  font-weight: 600;
}

.item-type {
  color: #ff6b9d !important;
}

.description-text {
  line-height: 1.6;
  color: #666;
  margin: 0;
  font-size: 15px;
}

/* Toast提示 */
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 16px 24px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 500;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
  opacity: 0;
  transform: translateX(100px);
  transition: all 0.3s ease;
  z-index: 9999;
}

.toast.show {
  opacity: 1;
  transform: translateX(0);
}

.toast-success {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

.toast-error {
  background: linear-gradient(135deg, #f44336, #ef5350);
  color: white;
}

.toast-info {
  background: linear-gradient(135deg, #2196f3, #42a5f5);
  color: white;
}

/* 评论加载和错误状态 */
.loading-comments, .error-comments {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  text-align: center;
  color: #666;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 15px;
  border: 2px dashed #ffc2d9;
  margin: 20px 0;
}

.loading-comments i {
  color: #ff6b9d;
  font-size: 20px;
}

.error-comments {
  flex-direction: column;
  color: #ff4081;
}

.error-comments i {
  font-size: 24px;
  margin-bottom: 8px;
}

.retry-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 12px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.3);
}

/* 编辑按钮样式 */
.action-btn.edit {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

/* 编辑模态框样式 */
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
  z-index: 10000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 25px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 3px solid #ffc2d9;
  background: linear-gradient(135deg, rgba(255, 107, 157, 0.1), rgba(162, 210, 255, 0.1));
}

.modal-header h3 {
  color: #333;
  margin: 0;
  font-size: 24px;
  text-shadow: 1px 1px 0 #ffc2d9;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(255, 107, 157, 0.1);
  color: #ff6b9d;
  transform: rotate(90deg);
}

.modal-body {
  padding: 30px;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-label {
  color: #333;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-label.required::after {
  content: '*';
  color: #ff6b9d;
  margin-left: 4px;
}

.form-label i {
  color: #ff6b9d;
}

.form-input, .form-textarea {
  padding: 15px 20px;
  border: 2px solid #ffc2d9;
  border-radius: 15px;
  font-family: inherit;
  font-size: 16px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 4px rgba(255, 107, 157, 0.1);
}

.form-input::placeholder, .form-textarea::placeholder {
  color: #bbb;
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.form-hint {
  color: #999;
  font-size: 14px;
  margin-top: 5px;
}

.error-text {
  color: #ff4081;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  animation: shake 0.3s ease;
}

.error-text::before {
  content: '⚠';
  font-size: 16px;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  gap: 20px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 2px solid #ffc2d9;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.9);
  color: #666;
  border: 2px solid #ddd;
}

.btn-cancel:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #bbb;
  transform: translateY(-2px);
}

.btn-submit {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  color: white;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: 0 6px 18px rgba(76, 175, 80, 0.4);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

/* 文件上传样式 */
.file-upload-area {
  border: 2px dashed #ffc2d9;
  border-radius: 15px;
  padding: 30px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
  margin-bottom: 15px;
}

.file-upload-area:hover {
  border-color: #ff6b9d;
  background: rgba(255, 107, 157, 0.05);
}

.upload-placeholder {
  color: #999;
}

.upload-placeholder i {
  font-size: 48px;
  color: #ffc2d9;
  margin-bottom: 15px;
}

.upload-placeholder p {
  margin: 8px 0;
  font-size: 16px;
}

.upload-hint {
  font-size: 14px !important;
  color: #bbb;
}

.file-preview,
.current-cover {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 15px;
  border: 2px solid #a2d2ff;
}

.preview-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 10px;
  border: 2px solid #ffc2d9;
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.file-name,
.file-url {
  color: #333;
  font-weight: 500;
  word-break: break-all;
  font-size: 14px;
}

.file-size {
  color: #666;
  font-size: 13px;
}

.current-label {
  color: #ff6b9d;
  font-weight: 600;
  font-size: 14px;
}

.remove-file-btn {
  align-self: flex-start;
  padding: 6px 12px;
  background: rgba(255, 107, 157, 0.1);
  color: #ff6b9d;
  border: 1px solid #ffc2d9;
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.3s ease;
}

.remove-file-btn:hover {
  background: rgba(255, 107, 157, 0.2);
  transform: translateY(-1px);
}


/* 响应式设计 */
@media (max-width: 768px) {
  .item-detail-page {
    padding: 10px;
  }

  .item-header {
    flex-direction: column;
    padding: 20px;
    text-align: center;
  }

  .detail-cover {
    width: 200px;
    height: 280px;
    margin: 0 auto;
  }

  .detail-title {
    font-size: 24px;
    text-align: center;
  }

  .actions {
    justify-content: center;
  }

  .tab-nav {
    flex-wrap: wrap;
  }

  .tab-btn {
    flex: 1 0 50%;
    padding: 15px 10px;
    font-size: 14px;
  }

  .tab-content {
    padding: 20px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    margin: 10px;
    max-height: 85vh;
  }

  .modal-header {
    padding: 15px 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
