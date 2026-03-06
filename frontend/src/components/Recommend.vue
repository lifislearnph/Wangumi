<template>
  <div class="recommendation-page">
    <div class="page-header"> 
      <div class="tab-container">
        <button 
          :class="['tab-btn', { active: activeTab === 'anime' }]"
          @click="switchTab('anime')"
        >
          番剧推荐
        </button>
        <button 
          :class="['tab-btn', { active: activeTab === 'social' }]"
          @click="switchTab('social')"
        >
          社交推荐
        </button>
      </div>
    </div>

    <!-- 番剧推荐区 -->
<div v-show="activeTab === 'anime'" class="content-section">
  <div v-if="enhancedAnimeRecs.length" class="editorial-sections">
    <section class="section-block">
      <div class="section-head">
        <div>
          <h3>✨ 编辑精选</h3>
        </div>
        <div class="section-actions">
          <span class="chip">共 {{ enhancedAnimeRecs.length }} 部</span>
        </div>
      </div>
      <div
        class="horizontal-scroll"
        ref="heroScrollRef"
        @scroll.passive="updateActiveHero"
        tabindex="0"
        @keydown.prevent="onHeroKeydown"
      >
        <div 
          v-for="(anime, idx) in heroDeck" :key="anime.__key || anime.id" 
          :class="['hero-card', { 'is-active': isHeroCardActive(idx) }]"
          @click="goToAnimeDetail(anime.id)"
        >
          <div class="hero-frame">
            <img :src="anime.cover" :alt="anime.title" class="hero-cover" loading="lazy">
            <div class="hero-overlay"></div>
            <div class="hero-info">
              <div class="hero-tags">
                <span class="tag primary-tag">{{ anime.reason || '推荐' }}</span>
                <span class="tag rating-tag" v-if="anime.rating">评分 {{ anime.rating.toFixed(1) }}</span>
              </div>
              <h4 class="hero-title">{{ anime.title }}</h4>
              <p class="hero-summary">{{ anime.summary || '暂无简介' }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head">
        <div>
          <h3>🔥 今日最热</h3>
        </div>
      </div>
      <div class="podium-grid">
        <div 
          v-for="(anime, idx) in topHotThree" 
          :key="anime.id" 
          class="podium-card"
          :data-rank="idx + 1"
          @click="goToAnimeDetail(anime.id)"
        >
          <div class="podium-medal" :class="'medal-' + (idx + 1)">
            {{ idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉' }}
          </div>
          <div class="podium-cover">
            <img :src="anime.cover" :alt="anime.title" loading="lazy">
          </div>
          <div class="podium-info">
            <div class="podium-rank">TOP {{ idx + 1 }}</div>
            <h4>{{ anime.title }}</h4>
            <div class="meta">
              <span v-if="anime.rating"><i class="fas fa-star"></i> {{ anime.rating.toFixed(1) }}</span>
              <span v-if="anime.popularity"><i class="fas fa-fire"></i> {{ anime.popularity }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head">
        <div>
          <h3>🕒 本季新番</h3>
        </div>
      </div>
      <div class="seasonal-grid">
        <div 
          v-for="anime in seasonalList" 
          :key="anime.id" 
          class="seasonal-card"
          @click="goToAnimeDetail(anime.id)"
        >
          <div class="seasonal-cover">
            <img :src="anime.cover" :alt="anime.title" loading="lazy">
            <div class="seasonal-chip" v-if="displayDate(anime)">开播 {{ displayDate(anime) }}</div>
          </div>
          <div class="seasonal-info">
            <h4>{{ anime.title }}</h4>
            <p class="seasonal-summary">{{ anime.summary || '暂无简介' }}</p>
            <div class="progress-row" v-if="anime.total_episodes">
              <div class="progress-bar">
                <div class="progress-inner" :style="{ width: episodeProgress(anime) + '%' }"></div>
              </div>
              <span class="progress-text">共 {{ anime.total_episodes }} 集</span>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>

  <div v-if="animeRecommendations.length > 0" class="anime-grid">
    <div v-for="anime in visibleAnimeList" :key="anime.id" class="anime-card">
      <div class="card-image-container">
        <img :src="anime.cover || anime.cover_url" alt="anime cover" class="anime-cover" loading="lazy">
        <div class="rating-badge" v-if="anime.rating">
          <i class="fas fa-star star-icon"></i>
          {{ anime.rating }}
        </div>
      </div>
      <div class="card-content">
        <h3 class="anime-title">{{ anime.title }}</h3>
        <div class="recommendation-tags">
          <span v-if="anime.reason === '好友在追'" class="tag friend-tag">好友在追</span>
          <span v-if="anime.reason === '兴趣相似'" class="tag interest-tag">兴趣推荐</span>
          <span v-if="anime.reason === '热门'" class="tag hot-tag">热门</span>
        </div>
        <button class="detail-btn" @click="goToAnimeDetail(anime.id)">查看详情</button>
      </div>
    </div>
  </div>
  <div v-if="animeTotal > 0" class="pagination-section">
    <div class="pagination-info">
      显示第 {{ (animePage - 1) * animePageSize + 1 }} - 
      {{ Math.min(animePage * animePageSize, animeTotal) }} 条，
      共 {{ animeTotal }} 条推荐
    </div>
    <div class="pagination-controls">
      <button 
        :disabled="animePage <= 1"
        @click="changeAnimePage(animePage - 1)"
        class="page-btn">
        <i class="fas fa-chevron-left"></i>
        上一页
      </button>
      
      <button 
        v-for="page in visiblePages" 
        :key="page"
        :class="['page-btn', 'number', { active: page === animePage }]"
        @click="changeAnimePage(page)">
        {{ page }}
      </button>
      
      <button 
        :disabled="animePage >= animeTotalPages"
        @click="changeAnimePage(animePage + 1)"
        class="page-btn">
        下一页
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>
  </div>
</div>

    <!-- 社交推荐区 -->
    <div v-show="activeTab === 'social'" class="content-section">
      <!-- 条目推荐 -->
      <div v-if="entryRecommendations.length > 0" class="social-section">
        <h3 class="section-title">讨论条目推荐</h3>
        <div class="entry-grid">
          <div v-for="entry in entryRecommendations" :key="entry.id" class="entry-card">
            <div class="card-image-container">
              <img :src="entry.cover_image" alt="entry cover" class="entry-cover">
              <div class="popularity-badge">热度: {{ entry.popularity }}</div>
            </div>
            <div class="card-content"> 
              <h4 class="entry-title">{{ entry.title }}</h4>
              <button class="detail-btn" @click="goToEntryDetail(entry.id)">查看详情</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 同好推荐 -->
      <div v-if="userRecommendations.length > 0" class="social-section">
        <h3 class="section-title">同好推荐</h3>
        <div class="user-grid">
          <div v-for="user in userRecommendations" :key="user.id" class="user-card">
            <div class="user-avatar-container">
              <img :src="user.avatar || '/path/to/default-avatar.png'" alt="user avatar" class="user-avatar">
            </div>
            <h4 class="username">{{ user.username }}</h4>
            <p class="mutual-count" v-if="user.mutual_watch_count">
              共同追番: {{ user.mutual_watch_count }}部
            </p>
            <button class="profile-btn" @click="goToUserProfile(user.id)">访问主页</button>
          </div>
        </div>
      </div>

      <div v-if="entryRecommendations.length === 0 && userRecommendations.length === 0" class="empty-state">
        <p>社交推荐需登录后使用</p>
      </div>
      
      <!-- 分页控件 -->
      <div v-if="socialTotalPages > 1" class="pagination">
        <button 
          :disabled="socialPage <= 1" 
          @click="changeSocialPage(socialPage - 1)"
          class="page-btn"
        >
          上一页
        </button>
        <span class="page-info">{{ socialPage }} / {{ socialTotalPages }}</span>
        <button 
          :disabled="socialPage >= socialTotalPages" 
          @click="changeSocialPage(socialPage + 1)"
          class="page-btn"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 用户信息弹窗 -->
    <div v-if="showUserProfileModal" class="modal-overlay" @click.self="closeUserProfile">
      <div class="modal-content">
        <div class="modal-header">
          <h3>用户主页</h3>
          <button class="close-btn" @click="closeUserProfile">×</button>
        </div>
        
        <div class="modal-body">
          <div class="profile-section">
            <h4>关注列表</h4>
            <div v-if="selectedUserProfile.following.length > 0" class="user-list">
              <div v-for="user in selectedUserProfile.following" :key="user.id" class="user-item">
                <img :src="user.avatar || '/path/to/default-avatar.png'" class="small-avatar">
                <span>{{ user.username }}</span>
              </div>
            </div>
            <p v-else class="empty-message">暂无关注</p>
          </div>
          
          <div class="profile-section">
            <h4>粉丝列表</h4>
            <div v-if="selectedUserProfile.followers.length > 0" class="user-list">
              <div v-for="user in selectedUserProfile.followers" :key="user.id" class="user-item">
                <img :src="user.avatar || '/path/to/default-avatar.png'" class="small-avatar">
                <span>{{ user.username }}</span>
              </div>
            </div>
            <p v-else class="empty-message">暂无粉丝</p>
          </div>
          
          <div class="profile-section">
            <h4>番剧列表</h4>
            <div v-if="selectedUserProfile.animeList.length > 0" class="anime-list">
              <div v-for="anime in selectedUserProfile.animeList" :key="anime.id" class="anime-item">
                <img :src="anime.cover" class="small-cover">
                <span>{{ anime.title }}</span>
              </div>
            </div>
            <p v-else class="empty-message">暂无番剧</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/* ===== 统一 API ===== */
import {
  fetchAnimeRecommend,
  fetchSocialRecommend,
  fetchUserHomePage
} from '@/services/recommendService.js'
import { getAnimeList } from '@/services/animeService.js'

import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ===== 状态 ===== */
const activeTab = ref('anime') // 'anime' | 'social'

// 切换标签
function switchTab(tab) {
  activeTab.value = tab
  // 切换标签后重新加载当前页数据
  loadRecommendations()
}

/* 番剧推荐 */
const animeRecommendations = ref([])
const realAnimeLength = ref(0)
const animePage = ref(1)
const animeTotalPages = ref(1)
const animePageSize = 10
const baseAnimeList = computed(() => {
  const total = realAnimeLength.value || animeRecommendations.value.length
  return animeRecommendations.value.slice(0, total)
})
const animeTotal = computed(() => baseAnimeList.value.length)
const seasonalList = ref([])
const visibleAnimeList = computed(() => {
  const start = (animePage.value - 1) * animePageSize
  const end = start + animePageSize
  return baseAnimeList.value.slice(start, end)
})
const visiblePages = computed(() => {
  const current = animePage.value
  const total = animeTotalPages.value
  if (total <= 0) return []
  const range = 2
  let start = Math.max(1, current - range)
  let end = Math.min(total, current + range)
  if (end - start < 4) {
    if (current <= 3) {
      end = Math.min(5, total)
    } else {
      start = Math.max(1, total - 4)
    }
  }
  const pages = []
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})
const heroScrollRef = ref(null)
const activeHeroIndex = ref(0)
const heroVirtualIndex = ref(0)
const isHeroAutoScrolling = ref(false)
const markHeroAuto = (duration = 600) => {
  isHeroAutoScrolling.value = true
  setTimeout(() => {
    isHeroAutoScrolling.value = false
  }, duration)
}
const enhancedAnimeRecs = computed(() =>
  (baseAnimeList.value || [])
    .map(item => ({
      ...item,
      cover: item.cover || item.cover_url || item.cover_image || ''
    }))
    .filter(item => item.id)
)
const editorPicks = computed(() =>
  [...enhancedAnimeRecs.value]
    .sort((a, b) => (b.rating || 0) - (a.rating || 0) || (b.popularity || 0) - (a.popularity || 0))
    .slice(0, 12)
)
const HERO_CLONE_COUNT = 2
const heroCloneSize = computed(() => Math.min(HERO_CLONE_COUNT, editorPicks.value.length))
const disableSnapTemporarily = (container, duration = 80) => {
  if (!container) return
  const prev = container.style.scrollSnapType
  container.style.scrollSnapType = 'none'
  setTimeout(() => {
    container.style.scrollSnapType = prev || ''
  }, duration)
}
const heroDeck = computed(() => {
  const base = editorPicks.value
  const cloneSize = heroCloneSize.value
  const baseWithKey = base.map((item, idx) => ({
    ...item,
    __key: `base-${item.id}-${idx}`,
    __realIndex: idx
  }))
  const prefix = baseWithKey.slice(-cloneSize).map((item, i) => ({
    ...item,
    __key: `pre-${item.id}-${i}-${item.__realIndex}`,
    __clone: 'pre'
  }))
  const suffix = baseWithKey.slice(0, cloneSize).map((item, i) => ({
    ...item,
    __key: `post-${item.id}-${i}-${item.__realIndex}`,
    __clone: 'post'
  }))
  return [...prefix, ...baseWithKey, ...suffix]
})
const hotRanking = computed(() =>
  [...enhancedAnimeRecs.value]
    .sort((a, b) => (b.popularity || 0) - (a.popularity || 0))
    .slice(0, 12)
)
const topHotThree = computed(() => hotRanking.value.slice(0, 3))

/* 社交推荐 */
const entryRecommendations = ref([])
const userRecommendations = ref([])
const socialPage = ref(1)
const socialTotalPages = ref(1)

/* 用户弹窗 */
const showUserProfileModal = ref(false)
const selectedUserProfile = ref({
  following: [],
  followers: [],
  animeList: []
})
const heroAutoplayTimer = ref(null)

/* ===== 方法 ===== */
function getHeaders() {
  const token = localStorage.getItem('access_token')
  const h = { 'Content-Type': 'application/json' }
  if (token) h.Authorization = `Bearer ${token}`
  return h
}

async function loadRecommendations() {
  try {
    stopHeroAutoplay()
    if (activeTab.value === 'anime') {
      const { list, total, pages } = await fetchAnimeRecommend({
        page: animePage.value,
        limit: 100,
        source: 'None'
      })
      realAnimeLength.value = list.length
      animeRecommendations.value = list
      const totalLocal = realAnimeLength.value
      animeTotalPages.value = Math.max(1, Math.ceil(totalLocal / animePageSize))
      await loadSeasonalLatest()
      await nextTick()
      const startIdx = heroCloneSize.value || 0
      heroVirtualIndex.value = startIdx
      scrollToHero(startIdx, 'auto')
      activeHeroIndex.value = 0
      startHeroAutoplay()
    } else {
      const { entryList, userList, entryTotal, userTotal } = await fetchSocialRecommend({
        page: socialPage.value,
        limit: 12
      })
      entryRecommendations.value = entryList
      userRecommendations.value = userList
      const maxCount = Math.max(entryTotal, userTotal)
      socialTotalPages.value = Math.ceil(maxCount / 12)
    }
  } catch (e) {
    console.error('加载推荐失败:', e)
  }
}

function episodeProgress(anime) {
  const total = Number(anime.total_episodes || anime.totalEpisodes) || 0
  const released = Number(anime.episodes_released || anime.episodesReleased) || 0
  if (!total) return 0
  const ratio = (released || total / 2) / total
  return Math.min(100, Math.max(0, ratio * 100))
}

function updateActiveHero() {
  if (isHeroAutoScrolling.value) return
  const container = heroScrollRef.value
  if (!container) return
  const cards = container.querySelectorAll('.hero-card')
  if (!cards.length) return
  const { left, width } = container.getBoundingClientRect()
  const centerX = left + width / 2
  let min = Infinity
  let idx = 0
  cards.forEach((card, i) => {
    const rect = card.getBoundingClientRect()
    const cardCenter = rect.left + rect.width / 2
    const dist = Math.abs(cardCenter - centerX)
    if (dist < min) {
      min = dist
      idx = i
    }
  })
  const totalReal = editorPicks.value.length || 1
  const deck = heroDeck.value
  heroVirtualIndex.value = idx
  const realIdx = deck[idx]?.__realIndex
  activeHeroIndex.value = totalReal ? (realIdx ?? (idx % totalReal)) : idx
}

function scrollToHero(targetIndex, behavior = 'smooth') {
  const container = heroScrollRef.value
  if (!container) return
  const cards = container.querySelectorAll('.hero-card')
  if (!cards.length) return
  const total = cards.length
  const idx = Math.min(Math.max(0, targetIndex), total - 1)
  const card = cards[idx]
  const containerRect = container.getBoundingClientRect()
  const cardRect = card.getBoundingClientRect()
  const cardCenter = (cardRect.left - containerRect.left) + container.scrollLeft + cardRect.width / 2
  const targetLeft = cardCenter - container.clientWidth / 2
  const autoDuration = behavior === 'smooth' ? HERO_SCROLL_DURATION : 120
  markHeroAuto(autoDuration)
  container.scrollTo({ left: targetLeft, behavior })
  heroVirtualIndex.value = idx
  const realIdx = heroDeck.value[idx]?.__realIndex
  const realLen = editorPicks.value.length || 1
  activeHeroIndex.value = realLen ? (realIdx ?? (idx % realLen)) : idx
}

function isHeroCardActive(idx) {
  const deck = heroDeck.value || []
  const item = deck[idx]
  if (!item || item.__clone) return false
  const realIdx = item.__realIndex ?? idx
  return realIdx === activeHeroIndex.value
}


function snapHeroToIndex(targetIdx, fromIdx) {
  const container = heroScrollRef.value
  const cards = container?.querySelectorAll('.hero-card') || []
  if (!container || !cards.length) return
  const safeFrom = Math.min(Math.max(0, fromIdx), cards.length - 1)
  const safeTo = Math.min(Math.max(0, targetIdx), cards.length - 1)
  disableSnapTemporarily(container)
  const delta = cards[safeFrom].offsetLeft - cards[safeTo].offsetLeft
  const targetLeft = container.scrollLeft - delta
  markHeroAuto(150)
  container.scrollTo({ left: targetLeft, behavior: 'auto' })
}

function snapHeroToRealStartFromClone(fromIdx) {
  const totalReal = editorPicks.value.length
  const cloneSize = heroCloneSize.value
  if (!totalReal) return
  const targetIdx = cloneSize // first real card position in deck
  snapHeroToIndex(targetIdx, fromIdx)
  heroVirtualIndex.value = targetIdx
  activeHeroIndex.value = 0
  // 额外校准一次确保首张居中
  scrollToHero(targetIdx, 'auto')
}

const HERO_SCROLL_DURATION = 600
const HERO_RESET_DELAY = 0
const HERO_AUTOPLAY_INTERVAL = 1500
function startHeroAutoplay() {
  stopHeroAutoplay()
  if (activeTab.value !== 'anime') return
  const totalReal = editorPicks.value.length
  const totalDeck = heroDeck.value.length
  if (!totalReal || totalDeck <= 1) return
  const cloneSize = heroCloneSize.value
  heroAutoplayTimer.value = setInterval(() => {
    if (activeTab.value !== 'anime' || !heroScrollRef.value) {
      stopHeroAutoplay()
      return
    }
    const baseStart = cloneSize
    const baseEnd = baseStart + totalReal - 1
    const currentDeckIdx = heroVirtualIndex.value || baseStart
    const nextDeckIdx = currentDeckIdx + 1
    if (nextDeckIdx > baseEnd) {
      const fromIdx = Math.min(nextDeckIdx, totalDeck - 1)
      markHeroAuto(HERO_RESET_DELAY + HERO_SCROLL_DURATION)
      scrollToHero(fromIdx, 'smooth')
      setTimeout(() => {
        snapHeroToRealStartFromClone(fromIdx)
      }, HERO_RESET_DELAY)
    } else {
      scrollToHero(nextDeckIdx, 'smooth')
    }
  }, HERO_AUTOPLAY_INTERVAL)
}

function stopHeroAutoplay() {
  if (heroAutoplayTimer.value) {
    clearInterval(heroAutoplayTimer.value)
    heroAutoplayTimer.value = null
  }
}

function displayDate(item) {
  const raw = item.release_date || item.air_date || item.start_date || item.time || item.updated_at
  if (!raw) return ''
  const d = new Date(raw)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function loadSeasonalLatest() {
  try {
    const headers = getHeaders()
    const [seasonRes, weeklyRes] = await Promise.all([
      fetch('/api/sync/season/', { headers }),
      fetch('/api/sync/weekly/', { headers })
    ])

    const safeJson = async res => {
      try {
        return res.ok ? await res.json() : {}
      } catch (e) {
        console.warn('解析同步接口数据失败', e)
        return {}
      }
    }
    const isAdminContent = flagRaw => {
      if (flagRaw === undefined || flagRaw === null) return false
      const flag = typeof flagRaw === 'string' ? flagRaw.toLowerCase() : flagRaw
      return flag === true || flag === 1 || flag === 'true' || flag === '1'
    }
    const parseList = data => {
      if (!data) return []
      const rawList =
        data.list ||
        data.results ||
        data.data?.list ||
        data.data?.results ||
        data.data ||
        []
      return Array.isArray(rawList) ? rawList : []
    }

    const [seasonJson, weeklyJson] = await Promise.all([safeJson(seasonRes), safeJson(weeklyRes)])
    const combinedList = [...parseList(seasonJson), ...parseList(weeklyJson)]
    const normalizeItem = item => {
      const release = item.release_date || item.air_date || item.start_date || item.time || item.updated_at
      return {
        ...item,
        id: item.id || item.anime_id,
        title: item.title || item.name || '未命名条目',
        cover: item.cover || item.cover_url || item.cover_image || '',
        summary: item.summary || item.description || item.synopsis || '',
        release_date: release
      }
    }
    const adminOnly = combinedList.filter(item => {
      const flagRaw = item?.is_admin ?? item?.isAdmin
      return isAdminContent(flagRaw)
    })

    const deduped = []
    const seen = new Set()
    adminOnly
      .map(normalizeItem)
      .forEach(item => {
        if (!item.id || seen.has(item.id)) return
        seen.add(item.id)
        deduped.push(item)
      })

    const sorted = deduped.sort((a, b) => {
      const da = new Date(a.release_date || 0).getTime()
      const db = new Date(b.release_date || 0).getTime()
      return db - da
    })

    seasonalList.value = sorted.slice(0, 4)

    // 同步接口无数据时使用旧接口兜底
    if (!seasonalList.value.length) {
      const resp = await getAnimeList({ sort: 'time', page: 1, limit: 50, is_admin: true })
      if (resp?.code === 0) {
        const list = resp.data?.list || []
        seasonalList.value = list
          .map(normalizeItem)
          .filter(item => isAdminContent(item.isAdmin))
          .sort((a, b) => {
            const da = new Date(a.release_date || 0).getTime()
            const db = new Date(b.release_date || 0).getTime()
            return db - da
          })
          .slice(0, 4)
      }
    }
  } catch (e) {
    console.error('加载本季新番失败:', e)
  }
}

function onHeroKeydown(e) {
  if (activeTab.value !== 'anime') return
  if (e.key === 'ArrowRight') {
    scrollToHero(heroVirtualIndex.value + 1, 'smooth')
  }
  if (e.key === 'ArrowLeft') {
    scrollToHero(heroVirtualIndex.value - 1, 'smooth')
  }
}

/* 分页 */
async function changeAnimePage(page) {
  const maxPage = Math.max(1, animeTotalPages.value || 1)
  animePage.value = Math.min(Math.max(1, page), maxPage)
}
async function changeSocialPage(page) {
  socialPage.value = page
  await loadRecommendations()
}

/* 跳转 */
function goToAnimeDetail(animeId) {
  router.push(`/anime/${animeId}`)
}
function goToEntryDetail(entryId) {
  router.push(`/item/${entryId}`)
}
function goToUserProfile(userId) {
  router.push(`/personal/others/${userId}`)
}

/* 用户详情弹窗 */
async function fetchUserProfile(userId) {
  try {
    const { following, followers, animeList } = await fetchUserHomePage(userId)
    selectedUserProfile.value = { following, followers, animeList }
    showUserProfileModal.value = true
  } catch (e) {
    console.error('获取用户主页失败:', e)
    alert('获取用户主页失败')
  }
}
function closeUserProfile() {
  showUserProfileModal.value = false
}

/* ===== 生命周期 ===== */
onMounted(() => {
  loadRecommendations()
})
onUnmounted(() => {
  stopHeroAutoplay()
})
</script>

<style scoped>
.recommendation-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h2 {
  color: #2c3e50;
  font-size: 2.5em;
  margin-bottom: 20px;
  font-weight: 600;
}

.tab-container {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 30px;
}

.tab-btn {
  padding: 12px 30px;
  border: none;
  background: #f8f9fa;
  color: #6c757d;
  border-radius: 25px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.tab-btn.active {
  background: linear-gradient(135deg,  #f4b0d8 0%, #e3919f 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.content-section {
  min-height: 400px;
}

.anime-grid, .entry-grid, .user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.anime-card, .entry-card, .user-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
  position: relative;
}

.anime-card:hover, .entry-card:hover, .user-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.card-image-container {
  position: relative;
  width: 100%;
  height: 280px;
  overflow: hidden;
}

.anime-cover, .entry-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.anime-card:hover .anime-cover,
.entry-card:hover .entry-cover {
  transform: scale(1.05);
}

.rating-badge, .popularity-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 107, 157, 0.9);
  color: white;
  padding: 5px 10px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.star-icon {
  color: #ffd166;
  font-size: 12px;
  text-shadow: 0 0 4px rgba(255, 209, 102, 0.6);
} 

.card-content {
  padding: 15px;
  text-align: center; /* 让整个内容区居中 */
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.card-content h3,
.card-content h4 {
  text-align: center; /* 标题居中 */
}

/* 按钮保持全宽，但文字居中 */
.detail-btn, .profile-btn {
  width: 100%;
  padding: 10px;
  border: none;
  background: linear-gradient(135deg, #f4b0d8 0%,  #e3919f 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  text-align: center; /* 确保按钮文字居中 */
  margin-top: auto;
}


.anime-title, .entry-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #2c3e50;
  line-height: 1.4;
  display: -webkit-box;
  display: box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  
  /* 备用方案：不支持 line-clamp 的浏览器 */
  max-height: 2.8em; /* 2行的高度 */
  min-height: 2.8em;
}


.recommendation-tags {
  display: flex;
  gap: 5px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.tag {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.friend-tag {
  background: #e3f2fd;
  color: #1976d2;
}

.interest-tag {
  background: #f3e5f5;
  color: #e3919f;
}

.hot-tag {
  background: #ffebee;
  color: #c62828;
}

.detail-btn, .profile-btn {
  width: 100%;
  padding: 10px;
  border: none;
  background: linear-gradient(135deg, #f4b0d8 0%,  #e3919f 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}

.detail-btn:hover, .profile-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

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

.mutual-count {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 15px;
}

.social-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 1.5em;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e9ecef;
}

.pagination-section {
  margin-top: 24px;
  padding-top: 8px;
  border-top: 1px solid #f1f3f5;
}
.pagination-info {
  margin-bottom: 12px;
  color: #6c757d;
  font-size: 14px;
  text-align: center;
}
.pagination-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}
.page-btn {
  padding: 8px 14px;
  border: 1px solid #dee2e6;
  background: white;
  color: #495057;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #adb5bd;
}
.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.page-btn.number {
  min-width: 36px;
  text-align: center;
}
.page-btn.number.active {
  background: #ff6b9d;
  color: white;
  border-color: #ff6b9d;
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.35);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px);
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
  padding: 20px 25px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #f4b0d8 0%,  #e3919f 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.3em;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.3s ease;
}

.close-btn:hover {
  background: rgba(255,255,255,0.2);
}

.modal-body {
  padding: 25px;
  max-height: calc(80vh - 80px);
  overflow-y: auto;
}

.profile-section {
  margin-bottom: 25px;
}

.profile-section h4 {
  color: #2c3e50;
  font-size: 1.1em;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.user-list, .anime-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.user-item, .anime-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-item:hover, .anime-item:hover {
  background: #e9ecef;
  transform: translateY(-2px);
}

.small-avatar, .small-cover {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
}

.empty-message {
  color: #6c757d;
  font-style: italic;
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6c757d;
}

.empty-state p {
  font-size: 1.1em;
  margin: 0;
}

/* 新增：精选/热榜/本季新番样式 */
.editorial-sections {
  display: flex;
  flex-direction: column;
  gap: 28px;
  margin-bottom: 32px;
}
.section-block {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  border: 1px solid #f1f3f5;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.section-head h3 {
  margin: 0;
  font-size: 20px;
}
.section-subtitle {
  margin: 2px 0 0;
  color: #6c757d;
  font-size: 13px;
}
.section-actions .chip {
  background: #f5f7fb;
  color: #5c6b8a;
  padding: 6px 10px;
  border-radius: 20px;
  font-size: 12px;
}
.horizontal-scroll {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(260px, 340px);
  gap: 24px;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 50px 48px 100px;
  margin: 0 -24px;
  scroll-snap-type: x mandatory;
  scrollbar-width: none; /* Firefox */
}
.horizontal-scroll::-webkit-scrollbar {
  display: none; /* Chrome/Safari 隐藏滚动条 */
}
.horizontal-scroll:focus {
  outline: none;
  box-shadow: none;
}

.hero-card {
  position: relative;
  min-height: 380px;
  scroll-snap-align: center;
  cursor: pointer;
  transition: transform 0.35s ease, opacity 0.35s ease; /* 移除 box-shadow transition，性能更好 */
  transform: scale(0.82);
  opacity: 0.55;
  transform-origin: center center;
  will-change: transform, opacity;
  background: transparent; 
  transform-style: preserve-3d; 
}
.hero-card.is-active {
  transform: scale(1.2);
  opacity: 1;
  z-index: 10;
}
.hero-frame {
  position: relative;
  height: 100%;
  border-radius: 20px;
  overflow: hidden; 
  box-shadow: 0 12px 28px rgba(0,0,0,0.15);
  transform: translateZ(0);
  background: transparent;
}
.hero-card.is-active .hero-frame {
  box-shadow: 0 26px 60px rgba(0,0,0,0.3);
}
.hero-frame::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  z-index: 2;
  pointer-events: none;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.15); 
}

.hero-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0) 40%, rgba(0,0,0,0.75) 100%);
}
.hero-info {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 16px;
  color: white;
}
.hero-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.primary-tag {
  background: rgba(255, 107, 157, 0.9);
  color: white;
}
.rating-tag {
  background: rgba(255, 209, 102, 0.9);
  color: #7b4d00;
}
.hero-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
}
.hero-summary {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
  max-height: 3.8em;
  overflow: hidden;
}
.podium-grid {
  display: flex;
  justify-content: flex-start;
  gap: 16px;
  align-items: flex-end;
  padding: 12px 12px 8px;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
}
.podium-card {
  position: relative;
  background: #f9fbff;
  border: 1px solid #e6ecf5;
  border-radius: 18px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  flex: 1 1 0;
  max-width: 340px;
  min-width: 240px;
  transform-origin: center bottom;
  scroll-snap-align: start;
}
.podium-card:hover {
  transform: scale(1.02);
  box-shadow: 0 14px 36px rgba(0,0,0,0.12);
}
.podium-card[data-rank="2"] { order: 1; }
.podium-card[data-rank="1"] { order: 2; }
.podium-card[data-rank="3"] { order: 3; }
.podium-card[data-rank="1"] .podium-cover img { height: 320px; }
.podium-card[data-rank="2"] .podium-cover img { height: 280px; }
.podium-card[data-rank="3"] .podium-cover img { height: 260px; }
.podium-card[data-rank="1"] .podium-rank { color: #f5a623; }
.podium-card[data-rank="2"] .podium-rank { color: #9ca5b5; }
.podium-card[data-rank="3"] .podium-rank { color: #c57c48; }
.podium-medal {
  font-size: 32px;
  margin-bottom: 10px;
}
.podium-cover img {
  width: 100%;
  height: 260px;
  object-fit: cover;
  border-radius: 14px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.14);
}
.podium-info h4 {
  margin: 10px 0 8px;
  font-size: 16px;
}
.podium-rank {
  font-weight: 800;
  color: #7b8cff;
}
.meta {
  display: flex;
  gap: 10px;
  color: #6c757d;
  font-size: 13px;
  justify-content: center;
  align-items: center;
}
.seasonal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}
.seasonal-card {
  background: #fbfcff;
  border: 1px solid #e6ecf5;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.seasonal-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0,0,0,0.08);
}
.seasonal-cover {
  position: relative;
  height: 180px;
}
.seasonal-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.seasonal-chip {
  position: absolute;
  left: 10px;
  bottom: 10px;
  background: rgba(255, 107, 157, 0.3);
  color: #ffffffff;
  padding: 6px 10px;
  border-radius: 12px;
  font-size: 12px;
  backdrop-filter: blur(5px);
}
.seasonal-info {
  padding: 12px 12px 14px;
}
.seasonal-info h4 {
  margin: 0 0 6px;
  font-size: 15px;
}
.seasonal-summary {
  margin: 0 0 10px;
  color: #5f6b7c;
  font-size: 13px;
  line-height: 1.4;
  max-height: 3.6em;
  overflow: hidden;
}
.progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-bar {
  flex: 1;
  background: #e9edf6;
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
}
.progress-inner {
  height: 100%;
  background: linear-gradient(90deg, #7b8cff, #ff82c8);
}
.progress-text {
  color: #6c757d;
  font-size: 12px;
}

/* 移动端适配：保证横滑视图可见至少两张、领奖台不溢出 */
@media (max-width: 768px) {
  .horizontal-scroll {
    grid-auto-columns: minmax(65vw, 80vw);
    gap: 16px;
    padding: 20px 16px 60px;
    margin: 0 -12px;
  }
  .hero-card {
    min-height: 300px;
    transform: scale(0.88);
  }
  .hero-card.is-active {
    transform: scale(1.05);
  }
  .hero-frame {
    border-radius: 16px;
  }
  .podium-grid {
    gap: 10px;
    overflow-x: auto;
    padding: 8px 12px;
    scroll-snap-type: x mandatory;
  }
  .podium-card {
    min-width: 65vw;
    max-width: 70vw;
    padding: 10px;
    scroll-snap-align: start;
  }
  .podium-card[data-rank="1"] .podium-cover img { height: 260px; }
  .podium-card[data-rank="2"] .podium-cover img { height: 230px; }
  .podium-card[data-rank="3"] .podium-cover img { height: 210px; }
  .podium-medal {
    font-size: 26px;
    margin-bottom: 6px;
  }
}
/* 响应式设计 */
@media (max-width: 768px) {
  .anime-grid, .entry-grid, .user-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .user-list, .anime-list {
    grid-template-columns: 1fr;
  }
}
</style>
