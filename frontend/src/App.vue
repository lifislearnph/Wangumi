<template>
  <div class="anime-website">
    <header class="header">
      <nav class="nav-container">
        <div class="logo" @click="goHome">Wangumi</div>
        
        <ul class="nav-links">
          <li v-for="item in navItems" :key="item.id">
            <RouterLink 
              :to="item.to"
              :class="{ active: activeNav === item.id }">
              {{ item.text }}
            </RouterLink>
          </li>
        </ul>

        <!-- 检索输入框 -->
        <div class="search-container" ref="searchContainer">
          <div class="search-box" :class="{ 'search-focused': isSearchFocused }">
            <input
              type="text"
              v-model="searchKeyword"
              @focus="handleSearchFocus"
              @blur="handleSearchBlur"
              @keyup.enter="handleSearch"
              placeholder="搜索..."
              class="search-input"
            />
            <button @click="handleSearch" class="search-btn">
              <i class="search-icon">🔍</i>
            </button>
          </div>
          <!-- 历史搜索下拉列表 -->
          <div v-if="showSearchHistory && searchHistory.length > 0" class="search-history">
            <div class="search-history-header">
              <span>搜索历史</span>
              <button @click="clearSearchHistory" class="clear-history-btn">清空</button>
            </div>
            <ul class="history-list">
              <li
                v-for="(item, index) in searchHistory"
                :key="index"
                @click="selectHistoryItem(item)"
                class="history-item"
              >
                <span class="history-icon">🕐</span>
                <span class="history-text">{{ item }}</span>
                <button
                  @click.stop="removeHistoryItem(index)"
                  class="remove-history-btn"
                >
                  ×
                </button>
              </li>
            </ul>
          </div>
        </div>

        <div class="user-actions">
          <!-- 未登录 -->
          <template v-if="!isLoggedIn">
            <button class="login-btn" @click="handleLogin">注册/登录</button>
          </template>

          <!-- 已登录：显示独立的 UserMenu 组件 -->
          <template v-else>
            <UserMenu @click="gotopersonalspace"/>
            </template>
        </div>
      </nav>
    </header>
    
    <main class="main-content">
      <RouterView/>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserMenu from "@/components/UserMenu.vue"

// 路由相关
const route = useRoute()
const router = useRouter()

// 导航项
const navItems = [
  { id: 'anime-list', text: '番剧', to: '/animelist' },
  { id: 'recommend', text: '推荐', to: '/recommend' },
  //{ id: 'personal-space', text: '个人空间', to: '/personal/own' },
  { id: 'items', text: '条目', to: '/items' }
]

// 响应式数据
const isLoggedIn = ref(false)
const searchKeyword = ref('')
const isSearchFocused = ref(false)
const showSearchHistory = ref(false)
const searchHistory = ref([])
const searchHistoryMaxItems = 10 // 最多保存10条历史记录

// 计算属性
const activeNav = computed(() => {
  // 根据当前路由自动设置激活状态
  const routeMap = {
    '/animelist': 'anime-list',
    '/recommend': 'recommend',
    '/personal/own': 'personal-space',
    '/items': 'items'
  }
  return routeMap[route.path] || 'anime-list'
})

// 方法
const goHome = () => {
  router.push('/animelist')
  console.log('返回首页')
}

const handleLogin = (event) => {
  router.push('/login')
  console.log('跳转到登录页面')
}

const gotopersonalspace = () => {
  router.push('/personal/own')
  console.log('跳转个人空间')
}

// 搜索相关方法
const handleSearchFocus = () => {
  isSearchFocused.value = true
  showSearchHistory.value = true
}

const handleSearchBlur = () => {
  // 延迟隐藏，以便点击历史记录项时能触发
  setTimeout(() => {
    isSearchFocused.value = false
    showSearchHistory.value = false
  }, 200)
}

const handleSearch = () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    return
  }
  
  // 保存搜索历史
  addToSearchHistory(keyword)
  
  // 跳转到搜索结果页面（路由稍后配置）
  router.push({
    path: '/search',
    query: { keyword: keyword }
  })
  
  // 清空输入框并隐藏历史记录
  searchKeyword.value = ''
  showSearchHistory.value = false
  isSearchFocused.value = false
}

const addToSearchHistory = (keyword) => {
  // 移除重复项
  searchHistory.value = searchHistory.value.filter(item => item !== keyword)
  // 添加到开头
  searchHistory.value.unshift(keyword)
  // 限制数量
  if (searchHistory.value.length > searchHistoryMaxItems) {
    searchHistory.value = searchHistory.value.slice(0, searchHistoryMaxItems)
  }
  // 保存到 localStorage
  saveSearchHistory()
}

const selectHistoryItem = (keyword) => {
  searchKeyword.value = keyword
  handleSearch()
}

const removeHistoryItem = (index) => {
  searchHistory.value.splice(index, 1)
  saveSearchHistory()
}

const clearSearchHistory = () => {
  searchHistory.value = []
  saveSearchHistory()
}

const loadSearchHistory = () => {
  try {
    const history = localStorage.getItem('searchHistory')
    if (history) {
      searchHistory.value = JSON.parse(history)
    }
  } catch (error) {
    console.error('加载搜索历史失败:', error)
    searchHistory.value = []
  }
}

const saveSearchHistory = () => {
  try {
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory.value))
  } catch (error) {
    console.error('保存搜索历史失败:', error)
  }
}

// 事件监听器函数
const handleUserLoggedIn = () => {
  isLoggedIn.value = true
  console.log('用户已登录，更新状态')
}

const handleUserLoggedOut = () => {
  isLoggedIn.value = false
  console.log('用户已登出，更新状态')
}

// 生命周期钩子
onMounted(() => {
  // 初始化检查
  isLoggedIn.value = !!localStorage.getItem('access_token')
  
  // 加载搜索历史
  loadSearchHistory()

  // 监听登录事件
  window.addEventListener('user-logged-in', handleUserLoggedIn)

  // 监听登出事件
  window.addEventListener('user-logged-out', handleUserLoggedOut)
})

onBeforeUnmount(() => {
  window.removeEventListener('user-logged-in', handleUserLoggedIn)
  window.removeEventListener('user-logged-out', handleUserLoggedOut)
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.anime-website {
  font-family: 'Mochiy Pop One', 'Arial Rounded MT Bold', sans-serif;
  background: linear-gradient(135deg, #ffcfe6, #c2e9fb);
  min-height: 100vh;
  color: #333;
}

.header {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 15px 30px;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 3px solid #ff6b9d;
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 28px;
  font-weight: bold;
  color: #ff6b9d;
  text-shadow: 2px 2px 0 #ffc2d9;
  transition: all 0.3s ease;
  cursor: pointer;
}

.logo:hover {
  transform: scale(1.05);
  text-shadow: 3px 3px 0 #ffc2d9, 5px 5px 5px rgba(0, 0, 0, 0.1);
}

.logo i {
  margin-right: 10px;
  font-size: 32px;
}

.nav-links {
  display: flex;
  list-style: none;
  gap: 30px;
}

.nav-links li {
  position: relative;
}

.nav-links a {
  text-decoration: none;
  color: #5a5a5a;
  font-size: 18px;
  padding: 8px 15px;
  border-radius: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  display: block;
}

.nav-links a:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  transition: all 0.5s ease;
}

.nav-links a:hover:before {
  left: 100%;
}

.nav-links a:hover {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.1);
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(255, 107, 157, 0.3);
}

.nav-links a.active {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.15);
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
  margin-right: 20px;
}

.search-box {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(255, 107, 157, 0.3);
  border-radius: 25px;
  padding: 8px 15px;
  transition: all 0.3s ease;
  min-width: 250px;
}

.search-box.search-focused {
  border-color: #ff6b9d;
  box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1);
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 16px;
  color: #333;
  font-family: inherit;
  padding: 0 10px;
}

.search-input::placeholder {
  color: #999;
}

.search-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

.search-btn:hover {
  transform: scale(1.1);
}

.search-icon {
  font-size: 18px;
  line-height: 1;
}

.search-history {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 5px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  animation: slideDown 0.2s ease;
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

.search-history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
  font-size: 14px;
  color: #666;
}

.clear-history-btn {
  background: none;
  border: none;
  color: #ff6b9d;
  cursor: pointer;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.clear-history-btn:hover {
  background: rgba(255, 107, 157, 0.1);
}

.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  cursor: pointer;
  transition: background 0.2s ease;
  border-bottom: 1px solid #f5f5f5;
}

.history-item:hover {
  background: rgba(255, 107, 157, 0.05);
}

.history-item:last-child {
  border-bottom: none;
}

.history-icon {
  margin-right: 10px;
  font-size: 14px;
}

.history-text {
  flex: 1;
  font-size: 14px;
  color: #333;
}

.remove-history-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  padding: 0 5px;
  transition: color 0.2s ease;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.remove-history-btn:hover {
  color: #ff6b9d;
  background: rgba(255, 107, 157, 0.1);
}

.user-actions {
  display: flex;
  align-items: center;
}

.login-btn {
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 25px;
  font-family: inherit;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(255, 107, 157, 0.4);
}

.login-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(255, 107, 157, 0.6);
}

.login-btn:active {
  transform: translateY(0);
}

.main-content {
  max-width: 1500px;
  margin: 0 auto;
  padding: 0px 0px;
}

.login-container{
  background-color: #ffffff;  /* 白色背景 */
  width: 500px;               /* 调整宽度 */
  padding: 40px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.register-container {
  background-color: #ffffff;  /* 白色背景 */
  width: 500px;               /* 调整宽度 */
  padding: 40px 32px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .nav-links {
    gap: 15px;
  }
  
  .logo {
    font-size: 24px;
  }
  
  .search-container {
    margin-right: 0;
    width: 100%;
    max-width: 100%;
  }
  
  .search-box {
    min-width: 100%;
    width: 100%;
  }
}
</style>
