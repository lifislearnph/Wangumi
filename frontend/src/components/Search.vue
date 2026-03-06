<template>
  <div class="search-page">
    <!-- 分类标签导航栏 -->
    <div class="tab-container">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-btn', { active: activeTab === tab.value }]"
        @click="switchTab(tab.value)"
      >
        {{ tab.label }}
        <span v-if="tab.count !== undefined" class="tab-count">({{ tab.count }})</span>
      </button>
    </div>

    <!-- 排序选项 -->
    <div class="sort-section">
      <h3 class="sort-title">
        <i class="fas fa-sort"></i>
        排序方式
      </h3>
      <div class="sort-buttons">
        <button
          v-for="sort in sortOptions"
          :key="sort.value"
          :class="['sort-btn', { active: currentSort === sort.value }]"
          @click="changeSort(sort.value)"
        >
          {{ sort.label }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-section">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <p>正在搜索...</p>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-else-if="!loading && hasResult" class="content-section">
      <!-- 全部结果 -->
      <div v-if="activeTab === 'all'" class="all-results">
        <!-- 番剧结果 -->
        <div v-if="searchResults.anime.length > 0" class="result-section">
          <h3 class="section-title">
            <i class="fas fa-tv"></i>
            番剧 ({{ searchResults.anime.length }})
          </h3>
          <div class="anime-grid">
            <div
              v-for="anime in searchResults.anime"
              :key="anime.id"
              class="anime-card"
              @click="goToAnimeDetail(anime.id)"
            >
              <div class="card-image-container">
                <img :src="anime.cover_url" :alt="anime.title" class="anime-cover" />
              </div>
              <div class="card-content">
                <h3 class="anime-title">{{ anime.title }}</h3>
                <button class="detail-btn" @click.stop="goToAnimeDetail(anime.id)">
                  查看详情
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 条目结果 -->
        <div v-if="searchResults.item.length > 0" class="result-section">
          <h3 class="section-title">
            <i class="fas fa-th-large"></i>
            条目 ({{ searchResults.item.length }})
          </h3>
          <div class="entry-grid">
            <div
              v-for="item in searchResults.item"
              :key="item.id"
              class="entry-card"
              @click="goToItemDetail(item.id)"
            >
              <div class="card-image-container">
                <img :src="item.cover_url" :alt="item.title" class="entry-cover" />
              </div>
              <div class="card-content">
                <h4 class="entry-title">{{ item.title }}</h4>
                <button class="detail-btn" @click.stop="goToItemDetail(item.id)">
                  查看详情
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 角色结果 -->
        <div v-if="searchResults.person.length > 0" class="result-section">
          <h3 class="section-title">
            <i class="fas fa-user-tie"></i>
            角色 ({{ searchResults.person.length }})
          </h3>
          <div class="user-grid">
            <div
              v-for="team in searchResults.person"
              :key="team.id"
              class="user-card"
            >
              <div class="user-avatar-container">
                <img
                  :src="team.pers_image_url || team.image_url || team.cover_url || '/path/to/default-avatar.png'"
                  :alt="team.name || team.title || '角色'"
                  class="user-avatar"
                />
              </div>
              <h4 class="username">{{ team.name || team.title }}</h4>
            </div>
          </div>
        </div>

        <!-- 用户结果 -->
        <div v-if="searchResults.user.length > 0" class="result-section">
          <h3 class="section-title">
            <i class="fas fa-users"></i>
            用户 ({{ searchResults.user.length }})
          </h3>
          <div class="user-grid">
            <div
              v-for="user in searchResults.user"
              :key="user.id"
              class="user-card"
              @click="goToUserProfile(user.id)"
            >
              <div class="user-avatar-container">
                <img 
                  :src="user.avatar_url ? `/media/${user.avatar_url}` : '/media/default-avatar.png'"
                  :alt="user.name"
                  class="user-avatar"
                />
              </div>
              <h4 class="username">{{ user.name }}</h4>
              <button class="profile-btn" @click.stop="goToUserProfile(user.id)">
                访问主页
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 番剧标签页 -->
      <div v-else-if="activeTab === 'anime'" class="tab-content">
        <div v-if="searchResults.anime.length > 0" class="anime-grid">
          <div
            v-for="anime in searchResults.anime"
            :key="anime.id"
            class="anime-card"
            @click="goToAnimeDetail(anime.id)"
          >
            <div class="card-image-container">
              <img :src="anime.cover_url" :alt="anime.title" class="anime-cover" />
            </div>
            <div class="card-content">
              <h3 class="anime-title">{{ anime.title }}</h3>
              <button class="detail-btn" @click.stop="goToAnimeDetail(anime.id)">
                查看详情
              </button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无番剧结果</p>
        </div>
      </div>

      <!-- 条目标签页 -->
      <div v-else-if="activeTab === 'item'" class="tab-content">
        <div v-if="searchResults.item.length > 0" class="entry-grid">
          <div
            v-for="item in searchResults.item"
            :key="item.id"
            class="entry-card"
            @click="goToItemDetail(item.id)"
          >
            <div class="card-image-container">
              <img :src="item.cover_url" :alt="item.title" class="entry-cover" />
            </div>
            <div class="card-content">
              <h4 class="entry-title">{{ item.title }}</h4>
              <button class="detail-btn" @click.stop="goToItemDetail(item.id)">
                查看详情
              </button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无条目结果</p>
        </div>
      </div>

      <!-- 角色标签页 -->
      <div v-else-if="activeTab === 'person'" class="tab-content">
        <div v-if="searchResults.person.length > 0" class="user-grid">
          <div
            v-for="team in searchResults.person"
            :key="team.id"
            class="user-card"
          >
            <div class="user-avatar-container">
              <img
                :src="team.pers_image_url || team.image_url || team.cover_url || '/path/to/default-avatar.png'"
                :alt="team.name || team.title || '角色'"
                class="user-avatar"
              />
            </div>
            <h4 class="username">{{ team.name || team.title }}</h4>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无角色结果</p>
        </div>
      </div>

      <!-- 用户标签页 -->
      <div v-else-if="activeTab === 'user'" class="tab-content">
        <div v-if="searchResults.user.length > 0" class="user-grid">
          <div
            v-for="user in searchResults.user"
            :key="user.id"
            class="user-card"
            @click="goToUserProfile(user.id)"
          >
            <div class="user-avatar-container">
              <img 
                  :src="user.avatar_url ? `/media/${user.avatar_url}` : '/media/default-avatar.png'"
                  :alt="user.name"
                  class="user-avatar"
                />
            </div>
            <h4 class="username">{{ user.name }}</h4>
            <button class="profile-btn" @click.stop="goToUserProfile(user.id)">
              访问主页
            </button>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无用户结果</p>
        </div>
      </div>

      <!-- 分页控件 -->
      <div v-if="activeTab !== 'all' && pagination.totalPages > 0" class="pagination">
        <div class="pagination-info">
          显示第 {{ (pagination.page - 1) * pagination. limit + 1 }} - 
          {{ Math.min(pagination.page * pagination.limit, pagination.totalResults) }}条，
          共 {{ pagination.totalResults }} 条结果
        </div>
        <button
          :disabled="pagination.page <= 1"
          @click="changePage(pagination.page - 1)"
          class="page-btn"
        >
          <i class="fas fa-chevron-left"></i>
          上一页
        </button>
        <span class="page-info">{{ pagination.page }} / {{ pagination.totalPages }}</span>
        <button
          :disabled="pagination.page >= pagination.totalPages"
          @click="changePage(pagination.page + 1)"
          class="page-btn"
        >
          下一页
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- 无结果状态 -->
    <div v-else-if="!loading && !hasResult" class="empty-state">
      <i class="fas fa-search"></i>
      <h3>未找到相关结果</h3>
      <p>请尝试使用其他关键词搜索</p>
    </div>

    <!-- 错误状态 -->
    <div v-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i>
      <h3>搜索失败</h3>
      <p>{{ error }}</p>
      <button @click="performSearch" class="retry-btn">重试</button>
    </div>
  </div>
</template>

<script setup>
import { ref,reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { search } from '@/services/searchService.js'

import axios from 'axios'

// ===== 接口客户端与工具 =====

const apiClient = axios.create({
  // 默认使用相对路径 /api，开发环境由 Vite 代理到 8000，生产环境由 Nginx 反向代理
  baseURL: import.meta.env?.VITE_API_BASE_URL || '/api',
  timeout: 10000
})
//api.interceptors.request.use
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token')
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)
// 路由相关
const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const error = ref('')
const activeTab = ref('all')
const currentSort = ref('relevance')
const searchKeyword = ref('')
const lastsearchKeyword = ref('')

const logininId = ref(null)

const pagination = reactive({
  page: 1,
  limit: 20,
  totalResults: 0,
  totalPages: 1
})
const searchResults = ref({
  anime: [],
  item: [],
  person: [],      // 角色
  user: []         // 用户
})

const hasResult = ref(false)

// 排序选项
const sortOptions = [
  { value: 'relevance', label: '按相关度' },
  { value: 'popularity', label: '按热度' },
  { value: 'time', label: '按时间' }
]

// 使用 ref 而不是 computed
const tabs = ref([])

// 在搜索结果更新时手动更新 tabs
const updateTabs = () => {
  const allCount = searchResults.value.anime.length + 
                   searchResults.value.item.length + 
                   searchResults.value.person.length +
                   searchResults.value.user.length
  
  tabs.value = [
    { value: 'all', label: '全部结果', count: allCount },
    { value: 'anime', label: '番剧', count: searchResults.value.anime.length },
    { value: 'item', label: '条目', count: searchResults.value.item.length },
    { value: 'person', label: '角色', count: searchResults.value.person.length },
    { value: 'user', label: '用户', count: searchResults.value.user.length }
  ]
}

// 方法
const performSearch = async () => {
  if (!searchKeyword.value.trim()) {
    return
  }
  loading.value = true
  error.value = ''
  hasResult.value = false
  try {
    const params = {
      query: searchKeyword.value.trim(),
      page: pagination.page,
      limit: pagination.limit,
      sort: currentSort.value
    }
    // 添加type参数,默认全部
    if (activeTab.value !== 'all') {
      params.type = activeTab.value
    }
   
    const response = await search(params)
    if (response && response.has_result) {
      const results = response.results || []
      searchResults.value = {
        anime: results.filter(item => item.type === 'anime'),
        item: results.filter(item => item.type === 'item'),
        person: results.filter(item => item.type === 'person'),
        user: results.filter(item => item.type === 'user')
      }
      pagination.totalResults = response.total || 0
      pagination.totalPages=Math.ceil(pagination.totalResults / pagination.limit)
      hasResult.value = true

      if (searchKeyword.value !== lastsearchKeyword.value) {
        updateTabs()
        lastsearchKeyword.value = searchKeyword.value
      }
    } else {
      searchResults.value = {
        anime: [],
        item: [],
        person: [],
        user: []
      }
      updateTabs()
      lastsearchKeyword.value = searchKeyword.value
      hasResult.value = false
    }
  } catch (err) {
    error.value = err.message || '搜索失败，请稍后重试'
    hasResult.value = false
    console.error('搜索错误:', err)
  } finally {
    loading.value = false
  }
}

const switchTab = (tab) => {
  activeTab.value = tab
  pagination.page = 1
  performSearch()
}

const changeSort = (sort) => {
  currentSort.value = sort
  pagination.page = 1
  performSearch()
}

const changePage = (page) => {
  console.log(pagination.totalPages)
  if (page >= 1 && page <= pagination.totalPages) {
    pagination.page = page
    console.log("changePage", page)
    performSearch()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const goToAnimeDetail = (id) => {
  router.push(`/anime/${id}`)
}

const goToItemDetail = (id) => {
  router.push(`/item/${id}`)
}

const goToUserProfile = (id) => {
  console.log("当前登录用户ID: 跳转到", logininId.value)
  if (id === logininId.value)
    router.push(`/personal/own`)
  else
    router.push(`/personal/others/${id}`)
}

// 生命周期
onMounted(async () => {
  const keyword = route.query.keyword
  if (keyword) {
    searchKeyword.value = keyword
    performSearch()
  }
  try {
    const response = await apiClient.get('/user/profile')
    const result = response.data || {}
    if (result.code === 0 && result.data && result.data.id) {
      logininId.value = result.data.id
      console.log("当前登录用户ID:", logininId.value)
    } else {
      console.log("获取用户信息失败:", result.message)
      logininId.value = null
    }
  } catch (error) {
    console.error("获取用户信息异常:", error)
    logininId.value = null
  }
})
/*
onMounted(() => {
  
  // 从路由参数获取搜索关键词
  const keyword = route.query.keyword
  if (keyword) {
    searchKeyword.value = keyword
    performSearch()
  }
})
*/
// 监听路由变化（当用户通过导航栏搜索时）
watch(
  () => route.query.keyword,
  (newKeyword) => {
    if (newKeyword && newKeyword !== searchKeyword.value) {
      searchKeyword.value = newKeyword
      pagination.page = 1
      performSearch()
    }
  }
)
</script>

<style scoped>
.search-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  padding: 20px;
}


/* 标签页容器 */
.tab-container {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 25px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  color: #666;
  border-radius: 25px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  font-family: inherit;
}

.tab-btn:hover {
  background: rgba(255, 107, 157, 0.1);
  transform: translateY(-2px);
}

.tab-btn.active {
  background: linear-gradient(135deg, #f4b0d8 0%, #e3919f 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
}

.tab-count {
  margin-left: 5px;
  font-size: 14px;
  opacity: 0.9;
}

/* 排序区域 */
.sort-section {
  background: rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  padding: 15px 20px;
  margin-bottom: 30px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border: 2px solid #ffc2d9;
}

.sort-title {
  color: #ff6b9d;
  margin: 0 0 15px 0;
  font-size: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.sort-btn {
  background: rgba(255, 107, 157, 0.1);
  border: 2px solid #ffc2d9;
  color: #ff6b9d;
  padding: 10px 20px;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  font-size: 14px;
}

.sort-btn:hover {
  background: rgba(255, 107, 157, 0.2);
  transform: translateY(-2px);
}

.sort-btn.active {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border-color: #ff6b9d;
}

/* 内容区域 */
.content-section {
  max-width: 1200px;
  margin: 0 auto;
}

.result-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 1.5em;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e9ecef;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title i {
  color: #ff6b9d;
}

/* 网格布局 */
.anime-grid,
.entry-grid,
.user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 25px;
  margin-bottom: 30px;
}

/* 卡片样式 */
.anime-card,
.entry-card,
.user-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.anime-card:hover,
.entry-card:hover,
.user-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 15px 35px rgba(255, 107, 157, 0.2);
  border-color: #ffc2d9;
}

.card-image-container {
  position: relative;
  width: 100%;
  height: 280px;
  overflow: hidden;
}

.anime-cover,
.entry-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.anime-card:hover .anime-cover,
.entry-card:hover .entry-cover {
  transform: scale(1.05);
}

.star-icon {
  color: #ffd166;
  font-size: 12px;
  text-shadow: 0 0 4px rgba(255, 209, 102, 0.6);
}

.card-content {
  padding: 15px;
  text-align: center;
}

.anime-title,
.entry-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2c3e50;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 2.8em;
}

.detail-btn,
.profile-btn {
  width: 100%;
  padding: 10px;
  border: none;
  background: linear-gradient(135deg, #f4b0d8 0%, #e3919f 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  font-family: inherit;
}

.detail-btn:hover,
.profile-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
}

/* 用户卡片特殊样式 */
.user-card {
  text-align: center;
  padding: 20px;
}

.user-avatar-container {
  width: 80px;
  height: 80px;
  margin: 0 auto 15px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #f0f0f0;
}

.user-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.username {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 40px;
  padding: 25px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.page-btn {
  background: rgba(255, 255, 255, 0.8);
  border: 2px solid #ffc2d9;
  color: #ff6b9d;
  padding: 10px 16px;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: inherit;
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 107, 157, 0.1);
  transform: translateY(-2px);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.page-info {
  font-weight: 500;
  color: #495057;
  font-size: 16px;
}

/* 加载状态 */
.loading-section {
  text-align: center;
  padding: 60px 20px;
}

.loading-spinner {
  color: #ff6b9d;
  font-size: 24px;
}

.loading-spinner p {
  margin-top: 15px;
  font-size: 16px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: #666;
}

.empty-state i {
  font-size: 64px;
  color: #ffc2d9;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: #ff6b9d;
  margin-bottom: 10px;
}

/* 错误状态 */
.error-state {
  text-align: center;
  padding: 60px 20px;
  color: #c62828;
}

.error-state i {
  font-size: 64px;
  margin-bottom: 20px;
}

.retry-btn {
  margin-top: 20px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  transition: all 0.3s ease;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-page {
    padding: 15px;
  }

  .page-title {
    font-size: 24px;
  }

  .tab-container {
    gap: 8px;
  }

  .tab-btn {
    padding: 10px 16px;
    font-size: 14px;
  }

  .anime-grid,
  .entry-grid,
  .user-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }

  .sort-buttons {
    justify-content: center;
  }

  .pagination {
    flex-direction: column;
    gap: 10px;
  }
}
</style>

