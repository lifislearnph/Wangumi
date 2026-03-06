import axios from 'axios'

// 推荐内容相关接口
const API_BASE = ''

function getHeaders() {
  const token = localStorage.getItem('access_token')
  const h = { 'Content-Type': 'application/json' }
  if (token) h.Authorization = `Bearer ${token}`
  return h
}

/* ===== 番剧推荐 ===== */
export async function fetchAnimeRecommend({ page = 1, limit = 12, source = 'None' } = {}) {
  const url = `/api/recommend_anime/?page=${page}&limit=${limit}&source=${source}`
  const res = await fetch(url, { headers: getHeaders() })
  const json = await res.json()
  if (!res.ok) throw new Error(json.detail || '获取失败')
  return {
    list: json.results || [],
    total: json.count || 0,
    pages: Math.ceil((json.count || 0) / limit)
  }
}

/* ===== 社交推荐 ===== */
export async function fetchSocialRecommend({ page = 1, limit = 12 } = {}) {
  const [entryRes, userRes] = await Promise.all([
    fetch(`/api/recommend_items/?page=${page}&limit=${limit}`, { headers: getHeaders() }),
    fetch(`/api/recommend_users/?page=${page}&limit=${limit}`, { headers: getHeaders() })
  ])
  const entryJson = await entryRes.json()
  const userJson = await userRes.json()

  if (!entryRes.ok || !userRes.ok) throw new Error('获取社交推荐失败')

  return {
    entryList: entryJson.data?.results || [],
    userList: userJson.results || [],
    entryTotal: entryJson.data?.count || 0,
    userTotal: userJson.count || 0
  }
}

/* ===== 用户主页数据聚合 ===== */
export async function fetchUserHomePage(userId) {
  const headers = getHeaders()
  const [followingRes, followerRes, animeRes] = await Promise.all([
    fetch(`/api/personal_homepage_following_list/${userId}?page=1&limit=20`, { headers }),
    fetch(`/api/personal_homepage_follower_list/${userId}?page=1&limit=20`, { headers }),
    fetch(`/api/personal_homepage_anime_list/${userId}?page=1&limit=20`, { headers })
  ])
  const [following, follower, anime] = await Promise.all([
    followingRes.json(),
    followerRes.json(),
    animeRes.json()
  ])
  if (!followingRes.ok || !followerRes.ok || !animeRes.ok) throw new Error('获取用户主页失败')
  return {
    following: following.results || [],
    followers: follower.results || [],
    animeList: anime.results || []
  }
}