<template>
  <div class="user-menu" @mouseenter="show = true" @mouseleave="show = false">
    <div class="avatar-box">
      <img
        :src="userAvatar"
        alt="User Avatar"
        class="avatar"
        @error="handleImageError"
      />
    </div>

    <transition name="dropdown">
      <div v-if="show" class="menu-panel">
        <div class="menu-header">
          <div class="user-info">
            <p class="username">个人中心</p>
          </div>
        </div>
        <div class="menu-items">
          <!-- 管理员入口 -->
          <div class="menu-item admin" @click="go('/admin/users')">
            <span class="menu-icon">👑</span>
            <span>用户管理</span>
          </div>

          <div class="menu-item admin" @click="go('/admin/reports')">
            <span class="menu-icon">🚩</span>
            <span>举报处理</span>
          </div>

          <div class="menu-item" @click="go('/change-password')">
            <span class="menu-icon">🔐</span>
            <span>修改密码</span>
          </div>
          <div class="menu-item" @click.stop="go('/change-contact')">
            <span class="menu-icon">📧</span>
            <span>修改邮箱</span>
          </div>

          <div class="menu-divider"></div>
          <div class="menu-item" @click="logoutAll" title="登出所有设备">
            <span class="menu-icon">🚫</span>
            <span>登出所有设备</span>
          </div>
          <div class="menu-item logout" @click="logout">
            <span class="menu-icon">🚪</span>
            <span>退出登录</span>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios' 

/* ---------- 基础配置 ---------- */
const router = useRouter()
const show = ref(false)
const userAvatar = ref('/default-avatar.png')

// 检查是否为管理员
const isAdmin = computed(() => {
  // 这里可以根据实际需求实现更复杂的权限检查
  // 例如从JWT token中解析用户角色
  const token = localStorage.getItem('access_token')
  if (!token) return false
  
  // 简单实现：假设有token且访问管理页面就是管理员
  // 实际项目中应该从后端获取用户角色信息
  // 这里可以添加更复杂的逻辑，比如检查token中的角色字段
  return true
})

// 创建API客户端
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000
})
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/* ---------- 获取用户信息 ---------- */
async function fetchUserProfile() {
  try {
    const { data } = await apiClient.get('/user/profile')
    if (data.code === 0) return data.data
  } catch (e) {
    console.error('获取用户信息失败：', e)
  }
  return null
}

/* ---------- 初始化头像 ---------- */
async function ensureAvatarLoaded() {
  let avatar = localStorage.getItem('user_avatar')
  if (!avatar) {
    const profile = await fetchUserProfile()
    if (profile?.avatar) {
      avatar = profile.avatar
      localStorage.setItem('user_avatar', avatar)
    }
  }
  if (avatar) userAvatar.value = avatar
}

/* ---------- 错误处理：缓存优先 + 锁 ---------- */
function handleImageError() {
  if (isUpdatingAvatar.value) return          // 🔒 更新期间不处理
  const cached = localStorage.getItem('user_avatar')
  if (cached) {
    userAvatar.value = cached
    return
  }
  setTimeout(async () => {
    const profile = await fetchUserProfile()
    if (profile?.avatar) {
      userAvatar.value = profile.avatar
      localStorage.setItem('user_avatar', profile.avatar)
    } else {
      userAvatar.value = '/default-avatar.png'
    }
  }, 1000)
}

/* ---------- 头像更新事件（由 PersonalSpace 派发） ---------- */
function handleAvatarUpdate(e) {
  const newAvatar = e.detail?.avatar || e.detail?.newAvatar
  if (!newAvatar) return
  isUpdatingAvatar.value = true              // 🔒 加锁
  const img = new Image()
  img.onload = () => {
    userAvatar.value = `${newAvatar}?t=${Date.now()}`
    localStorage.setItem('user_avatar', newAvatar)
    isUpdatingAvatar.value = false           // 🔓 解锁
  }
  img.onerror = () => {
    console.warn('新头像预加载失败，放弃切换')
    isUpdatingAvatar.value = false           // 🔓 解锁
  }
  img.src = newAvatar
}

/* ---------- 登录事件 ---------- */
async function handleUserLogin() {
  const profile = await fetchUserProfile()
  if (profile?.avatar) {
    userAvatar.value = `${profile.avatar}?t=${Date.now()}`
    localStorage.setItem('user_avatar', profile.avatar)
  }
}

/* ---------- 路由跳转 & 退出 ---------- */
function go(path) {
  console.log('跳转到:', path)
  show.value = false
  setTimeout(() => {
    router.push(path)
  })
}
function logoutLocalOnly() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_avatar')
  window.dispatchEvent(new CustomEvent('user-logged-out'))
  router.push('/login')
}
 
async function logout() {
  try {
    // 获取refresh token
    const refreshToken = localStorage.getItem('refresh_token')

    if (refreshToken) {
      // 调用登出API，将refresh token加入黑名单
      const response = await fetch('/api/logout/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      })

      // 如果API调用失败，但不影响本地清理
      if (!response.ok) {
        console.warn('登出API调用失败，但仍会清除本地存储')
      }
    }

    // 清除本地 token 和头像缓存
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_avatar')

    // 触发登出事件，通知App.vue更新状态
    window.dispatchEvent(new CustomEvent('user-logged-out'))

    // 登出成功后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 500)
  } catch (error) {
    console.error('登出过程中发生错误:', error)

    // 即使API调用失败，也要清除本地存储并跳转
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_avatar')

    window.dispatchEvent(new CustomEvent('user-logged-out'))
    setTimeout(() => {
      router.push('/login')
    }, 500)
  }
}

async function logoutAll() {
  try {
    // 调用登出所有设备API
    const response = await fetch('/api/logout-all/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    if (!response.ok) {
      console.warn('登出所有设备API调用失败，但仍会清除本地存储')
    }

    // 清除本地 token 和头像缓存
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_avatar')

    // 触发登出事件，通知App.vue更新状态
    window.dispatchEvent(new CustomEvent('user-logged-out'))

    // 登出成功后跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 500)
  } catch (error) {
    console.error('登出所有设备过程中发生错误:', error)

    // 即使API调用失败，也要清除本地存储并跳转
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_avatar')

    window.dispatchEvent(new CustomEvent('user-logged-out'))
    setTimeout(() => {
      router.push('/login')
    }, 500)
  }
}

onMounted(async () => {
  await ensureAvatarLoaded();
  window.addEventListener('avatar-updated', handleAvatarUpdate);

  // 监听登录事件，更新头像
  window.addEventListener('user-logged-in', async () => {
    console.log('检测到用户登录，更新头像');
    const avatar = await fetchUserProfile();
    if (avatar) {
      userAvatar.value = `${avatar}?t=${Date.now()}`;
    }
  });
});

onUnmounted(() => {
  window.removeEventListener('avatar-updated', handleAvatarUpdate)
  window.removeEventListener('user-logged-in', handleUserLogin)
})
</script>

<style scoped>
 
.user-menu {
  position: relative;
  display: inline-block;
  cursor: pointer;
}

.avatar-box {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  background: #f0f0f0;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.menu-panel {
  position: absolute;
  top: 52px;
  right: 50%;
  transform: translateX(50%);
  width: 240px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 1000;
  border: 1px solid rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
}

.menu-header {
  padding: 16px;
  background: linear-gradient(135deg, #f4b0d8 0%, #e3919f 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.user-info {
  text-align: center;
  color: white;
}

.username {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.user-email {
  font-size: 12px;
  opacity: 0.9;
  margin: 0;
}

.menu-items {
  padding: 8px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  color: #333;
  transition: all 0.3s ease;
  cursor: pointer;
}

.menu-item:hover {
  background: linear-gradient(90deg, rgba(244, 176, 216, 0.1) 0%, rgba(227, 145, 159, 0.1) 100%);
  transform: translateX(4px);
}

.menu-icon {
  width: 20px;
  margin-right: 12px;
  font-size: 16px;
  text-align: center;
}

.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(0, 0, 0, 0.1) 50%, transparent 100%);
  margin: 8px 16px;
}

.logout {
  color: #e74c3c;
}

.logout:hover {
  background: linear-gradient(90deg, rgba(231, 76, 60, 0.1) 0%, rgba(192, 57, 43, 0.1) 100%);
}

.admin {
  font-weight: 600;
  color: #ff6b9d;
}

.admin .menu-icon {
  font-size: 18px;
}

.admin:hover {
  background: linear-gradient(90deg, rgba(255, 107, 157, 0.15) 0%, rgba(255, 142, 180, 0.15) 100%);
}

/* 动画效果 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s ease;
  transform-origin: top center;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px) scale(0.95);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px) scale(0.95);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .menu-panel {
    width: 200px;
    right: 0;
    transform: none;
  }
  
  .dropdown-enter-from,
  .dropdown-leave-to {
    transform: translateY(-10px) scale(0.95);
  }
}
</style>
