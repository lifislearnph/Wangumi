// src/services/adminService.js
import axios from 'axios';

// 创建 axios 实例，baseURL 从环境变量读取
// 如果没有设置环境变量，使用空字符串，但所有API路径都包含/api前缀
const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '',
  timeout: 10000,
});

// 添加管理员权限的请求拦截器
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 统一响应处理
function handleResponse(response) {
  const data = response?.data;
  if (data && typeof data === 'object' && 'code' in data) {
    return data;
  }
  
  // 如果后端返回格式不一致，进行标准化
  return {
    code: 0,
    message: 'success',
    data: data || null
  };
}

function handleError(error) {
  console.error('API调用失败:', error);
  
  if (error.response) {
    // 服务器返回错误状态码
    const errorData = error.response.data;
    return {
      code: error.response.status,
      message: errorData?.message || errorData?.detail || `请求失败: ${error.response.status}`,
      data: null
    };
  } else if (error.request) {
    // 请求已发出但没有收到响应
    return {
      code: -1,
      message: '网络连接失败，请检查网络设置',
      data: null
    };
  } else {
    // 请求配置错误
    return {
      code: -2,
      message: error.message || '请求配置错误',
      data: null
    };
  }
}

/**
 * 获取用户列表
 * @param {Object} params 查询参数
 * @param {number} params.page - 页码，从1开始
 * @param {number} params.page_size - 每页数量，最大50
 * @param {string} params.search - 搜索关键词（用户名、邮箱、昵称）
 * @param {string} params.status - 状态筛选：active=正常, banned=已封禁
 * @param {string} params.order_by - 排序字段
 * @returns {Promise} 用户列表数据
 */
export const getUserList = async (params = {}) => {
  try {
    const queryParams = {
      page: params.page || 1,
      page_size: Math.min(params.page_size || 20, 50),
      search: params.search || undefined,
      status: params.status || undefined,
      order_by: params.order_by || '-date_joined'
    };

    // 移除undefined参数
    Object.keys(queryParams).forEach(key => {
      if (queryParams[key] === undefined) {
        delete queryParams[key];
      }
    });

    // 使用/api前缀确保路径正确
    const response = await apiClient.get('/api/admin/users/', { params: queryParams });
    return handleResponse(response);
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 获取单个用户状态
 * @param {number} userId - 用户ID
 * @returns {Promise} 用户状态数据
 */
export const getUserStatus = async (userId) => {
  try {
    const response = await apiClient.get(`/api/admin/users/${userId}/status/`);
    return handleResponse(response);
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 封禁用户
 * @param {number} userId - 用户ID
 * @param {Object} data - 封禁数据
 * @param {string} data.reason - 封禁理由
 * @param {number} data.ban_duration - 封禁天数
 * @returns {Promise} 封禁结果
 */
export const banUser = async (userId, data) => {
  try {
    const requestData = {
      reason: data.reason,
      ban_duration: data.ban_duration || 7
    };

    const response = await apiClient.post(`/api/admin/users/${userId}/ban/`, requestData);
    return handleResponse(response);
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 解封用户
 * @param {number} userId - 用户ID
 * @param {Object} data - 解封数据
 * @param {string} data.reason - 解封理由
 * @returns {Promise} 解封结果
 */
export const unbanUser = async (userId, data = {}) => {
  try {
    const requestData = {
      reason: data.reason || ''
    };

    const response = await apiClient.post(`/api/admin/users/${userId}/unban/`, requestData);
    return handleResponse(response);
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 检查当前用户是否为管理员
 * @returns {boolean} 是否为管理员
 */
export const isAdminUser = () => {
  // 这里可以根据实际需求实现更复杂的权限检查
  // 例如从JWT token中解析用户角色
  const token = localStorage.getItem('access_token');
  if (!token) return false;
  
  // 简单实现：假设有token且访问管理页面就是管理员
  // 实际项目中应该从后端获取用户角色信息
  return true;
};

export default {
  getUserList,
  getUserStatus,
  banUser,
  unbanUser,
  isAdminUser
};
