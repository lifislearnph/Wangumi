// src/services/searchService.js
import axios from 'axios'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '',
  timeout: 10000,
})

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 搜索接口
 * @param {Object} params - 查询参数
 * @param {string} params.query - 搜索关键词
 * @param {'anime' | 'item' | 'person' | 'user' | null} [params.type] 
 * @param {number} [params.page] - 页码
 * @param {number} [params.limit] - 每页数量
 * @param {'relevance' | 'popularity' | 'time'} [params.sort] - 排序方式，默认相关度
 * @returns {Promise<{
 *   query: string,
 *   results: Array<{
 *     id: number,
 *     title: string | null,
 *     name: string | null,
 *     avatar_url: string | null,
 *     cover_url: string | null,
 *     image_url: string | null,
 *     pers_image_url: string | null,
 *     related_score: number,
 *     is_admin: boolean | null,
 *     type: 'anime' | 'item' | 'person' | 'user'
 *   }>,
 *   total: number,
 *   has_result: boolean
 * }>} 搜索结果
 */
export const search = async (params = {}) => {
  try {
    const queryParams = {
      query: params.query || '',
      page: params.page || 1,
      limit: params.limit || 20,
    }
    
    if (params.type) queryParams.type = params.type
    if (params.sort) queryParams.sort = params.sort
    
    const response = await apiClient.get('/api/search/', { params: queryParams })
    console.log('search response', response)
    const data = response?.data || {}
    const results = data.results || {}
    
    // 扁平化处理
    const flattenResults = []
    const types = ['anime', 'item', 'person', 'user']
    
    types.forEach(type => {
      const items = results[type] || []
      if (Array.isArray(items)) {
        items.forEach(item => {
          flattenResults.push({ ...item, type })
        })
      }
    })
    
    return {
      query: data.query || params.query || '',
      results: flattenResults,
      total: typeof data.total === 'number' ? data.total : flattenResults.length,
      has_result: data.has_result || flattenResults.length > 0
    }
    
  } catch (error) {
    console.error('搜索失败:', error)
    
    if (error.response) {
      const errorMessage = error.response.data?.message || 
                          error.response.data?.detail || 
                          `请求失败: ${error.response.status}`
      throw new Error(errorMessage)
    } else if (error.request) {
      throw new Error('网络连接失败，请检查网络设置')
    } else {
      throw new Error('请求配置错误')
    }
  }
}