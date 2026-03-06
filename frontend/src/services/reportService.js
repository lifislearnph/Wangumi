// src/services/reportService.js
import axios from 'axios';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '',
  timeout: 10000,
});

// 添加请求拦截器
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
    code: 200,
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
 * 获取举报列表
 * @param {Object} params 查询参数
 * @param {string} params.status - 举报状态筛选: PENDING/RESOLVED/REJECTED
 * @param {number} params.page - 页码，默认1
 * @param {number} params.page_size - 每页数量，默认20
 * @returns {Promise} 举报列表数据
 */
export const getReportList = async (params = {}) => {
  try {
    const queryParams = {
      status: params.status || undefined,
      page: params.page || 1,
      page_size: Math.min(params.page_size || 20, 50)
    };

    // 移除undefined参数
    Object.keys(queryParams).forEach(key => {
      if (queryParams[key] === undefined) {
        delete queryParams[key];
      }
    });

    const response = await apiClient.get('/api/admin/reports/', { params: queryParams });
    return handleResponse(response);
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 获取单个举报详情
 * @param {number} reportId - 举报ID
 * @returns {Promise} 举报详情数据
 */
export const getReportDetail = async (reportId) => {
  try {
    const response = await apiClient.get(`/api/admin/reports/${reportId}/`);
    return handleResponse(response);
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 处理举报
 * @param {number} reportId - 举报ID
 * @param {Object} data - 处理数据
 * @param {string} data.action - 处理动作: RESOLVED/REJECTED
 * @param {string} data.resolution - 处理说明
 * @param {boolean} data.ban_user - 是否封禁用户
 * @param {number} data.ban_duration - 封禁天数
 * @returns {Promise} 处理结果
 */
export const handleReport = async (reportId, data) => {
  try {
    const requestData = {
      action: data.action,
      resolution: data.resolution || '',
      ban_user: data.ban_user || false,
      ban_duration: data.ban_duration || 7
    };

    const response = await apiClient.post(`/api/admin/reports/${reportId}/handle/`, requestData);
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
  const token = localStorage.getItem('access_token');
  if (!token) return false;
  return true;
};

export default {
  getReportList,
  getReportDetail,
  handleReport,
  isAdminUser
};
