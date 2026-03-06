import axios from 'axios'

// 用户认证与信息相关接口
const API_BASE = ''

/* ===== 工具：带自动刷新的 fetch ===== */
async function fetchWithAuth(url, options = {}, retry = true) {
  const accessToken = localStorage.getItem('access_token')
  options.headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
  const resp = await fetch(url, options)

  // 401 且允许重试 → 刷新一次 token
  if (resp.status === 401 && retry) {
    const refreshed = await refreshAccessToken()
    if (refreshed) return fetchWithAuth(url, options, false)
  }
  return resp
}
export { fetchWithAuth }

/* 刷新 access_token */
async function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) return false
  try {
    const res = await fetch('/api/token/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    })
    if (!res.ok) throw new Error()
    const { access } = await res.json()
    localStorage.setItem('access_token', access)
    return true
  } catch {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return false
  }
}

/* ===== 登录/登出 ===== */
export async function login(username, password) {
  const res = await fetch('/api/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || '登录失败')
  return data /* {access, refresh} */
}

export async function logout(refreshToken) {
  await fetch('/api/logout/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  })
  // 不论成功失败都清本地
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_avatar')
  window.dispatchEvent(new CustomEvent('user-logged-out'))
}

export async function logoutAll() {
  await fetchWithAuth('/api/logout-all/', { method: 'POST' })
    .catch(() => {}) // 静默处理
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_avatar')
  window.dispatchEvent(new CustomEvent('user-logged-out'))
}

/* ===== 用户信息 ===== */
export async function fetchUserProfile() {
  const res = await fetchWithAuth('/api/user/profile')
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '获取用户信息失败')
  return json.data /* 你的统一返回格式 */
}

export async function updateUserProfile({ username, signature, intro }) {
  const res = await fetchWithAuth('/api/user/profile/edit', {
    method: 'POST',
    body: JSON.stringify({ username, signature, intro })
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '更新失败')
  return json
}

export async function uploadAvatar(file) {
  const fd = new FormData()
  fd.append('avatar', file)
  const res = await fetchWithAuth('/api/user/avatar', {
    method: 'POST',
    body: fd // 不带 Content-Type，让浏览器自动生成
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '上传失败')
  return json
}

/* ===== 密码/邮箱 ===== */
export async function changePassword(oldPwd, newPwd) {
  const params = new URLSearchParams()
  params.append('old_password', oldPwd)
  params.append('new_password', newPwd)
  const res = await fetchWithAuth('/api/account/password_change/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.error || json.detail || '修改失败')
  return json
}

export async function requestChangeEmail(newEmail, password) {
  const res = await fetchWithAuth('/api/account/contact/change/request/', {
    method: 'POST',
    body: JSON.stringify({ contact_type: 'email', value: newEmail, current_password: password })
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '发送验证码失败')
  return json
}

export async function confirmChangeEmail(newEmail, code, password) {
  const res = await fetchWithAuth('/api/account/contact/change/confirm/', {
    method: 'POST',
    body: JSON.stringify({ contact_type: 'email', value: newEmail, code, current_password: password })
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '修改失败')
  return json
}

/* ===== 隐私设置 ===== */
export async function fetchPrivacySettings() {
  const res = await fetchWithAuth('/api/users/privacy')
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '获取失败')
  return json.data
}

export async function savePrivacySettings(payload) {
  const res = await fetchWithAuth('/api/users/privacy', {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
  const json = await res.json()
  if (!res.ok) throw new Error(json.message || '保存失败')
  return json
}