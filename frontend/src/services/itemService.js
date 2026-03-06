// src/services/itemService.js
import axios from 'axios';

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '',
  timeout: 30000, // 上传图片可能需要更长时间
});

// 获取完整的图片URL
export const getFullImageUrl = (relativeUrl) => {
  if (!relativeUrl) return '';

  // 如果是完整的URL，直接返回
  if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) {
    return relativeUrl;
  }

  // 如果是相对路径，在开发环境下通过Vite代理访问，生产环境直接返回相对路径
  // Vite已经配置了 '/media' 代理到后端
  let finalUrl = relativeUrl;

  if (finalUrl.startsWith('/media/')) {
    // 已经是 /media/ 开头，保持不变
  } else if (finalUrl.startsWith('media/')) {
    // 少了一个斜杠，补上
    finalUrl = `/${finalUrl}`;
  } else if (finalUrl.startsWith('/')) {
    // 已经是绝对路径（可能是服务器路径），保持不变
  } else {
    // 兜底：添加/media/前缀
    finalUrl = `/media/${finalUrl}`;
  }

  // 编码URL中的中文字符和特殊字符，但保留斜杠
  // 将URL分割成路径部分，对文件名部分进行编码
  const parts = finalUrl.split('/');
  const encodedParts = parts.map((part) => {
    // 跳过空字符串（来自开头的 /）和 'media' 部分
    if (part === '' || part === 'media' || part === 'covers') return part;
    // 对文件名部分进行URI编码，这样可以处理中文和特殊字符
    try {
      // 如果已经编码过，先解码再编码，避免双重编码
      const decoded = decodeURIComponent(part);
      return encodeURIComponent(decoded);
    } catch (e) {
      // 如果解码失败，直接编码
      return encodeURIComponent(part);
    }
  });

  return encodedParts.join('/');
};

// 请求拦截器 - 添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 上传图片 - 多种方案
 * @param {File} file - 图片文件
 * @returns {Promise<string>} 图片URL
 */
export const uploadImage = async (file) => {
  // 方案1: 尝试使用用户头像上传接口
  try {
    const imageUrl = await uploadImageViaAvatar(file);
    return imageUrl;
  } catch (error) {
    console.warn('头像接口上传失败，尝试其他方案:', error.message);
  }

  // 方案2: 使用Base64编码直接创建条目
  try {
    const imageUrl = await convertToBase64(file);
    return imageUrl;
  } catch (error) {
    console.warn('Base64转换失败，尝试其他方案:', error.message);
  }

  // 方案3: 使用第三方图片服务（如imgbb）
  try {
    const imageUrl = await uploadToThirdParty(file);
    return imageUrl;
  } catch (error) {
    console.warn('第三方上传失败:', error.message);
  }

  // 所有方案都失败
  throw new Error('所有图片上传方案都失败，请检查网络连接或联系管理员');
};

/**
 * 方案1: 通过用户头像接口上传
 */
const uploadImageViaAvatar = async (file) => {
  const formData = new FormData();
  formData.append('avatar', file);

  const response = await apiClient.post('/api/user/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  // 尝试多种可能的返回格式
  const imageUrl =
    response?.data?.data?.url ||
    response?.data?.url ||
    response?.data?.avatar_url ||
    response?.data?.data?.avatar_url ||
    response?.data?.data?.file_url ||
    response?.data?.file_url;

  if (!imageUrl) {
    throw new Error('上传成功但未返回图片地址');
  }

  return imageUrl;
};

/**
 * 方案2: 转换为Base64（适用于小图片）
 */
const convertToBase64 = async (file) => {
  // 检查文件大小，Base64适合小于2MB的图片
  if (file.size > 5 * 1024 * 1024) {
    throw new Error('文件过大，不适合Base64编码');
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('文件读取失败'));
    reader.readAsDataURL(file);
  });
};

/**
 * 方案3: 上传到第三方图片服务
 */
const uploadToThirdParty = async (file) => {
  // 使用imgbb作为示例（免费图片托管服务）
  const API_KEY = 'your-imgbb-api-key';

  if (!API_KEY || API_KEY === 'your-imgbb-api-key') {
    throw new Error('未配置第三方图片服务API Key');
  }

  const formData = new FormData();
  formData.append('image', file);

  const response = await fetch(`https://api.imgbb.com/1/upload?key=${API_KEY}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`第三方上传失败: ${response.status}`);
  }

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.error?.message || '第三方上传失败');
  }

  return data.data.url;
};

/**
 * 临时方案：使用占位符图片
 * @param {File} file - 图片文件
 * @returns {Promise<string>} 占位符图片URL
 */
export const uploadImageFallback = async (file) => {
  console.warn('使用临时占位符图片方案');

  // 生成一个基于文件名的占位符图片
  const fileName = encodeURIComponent(file.name);
  const fileSize = Math.round(file.size / 1024); // KB

  // 使用 placeholder.com 生成占位符
  const placeholderUrl = `https://via.placeholder.com/400x600/ff6b9d/ffffff?text=${fileName}+${fileSize}KB`;

  return placeholderUrl;
};

/**
 * 创建条目（支持直接上传图片）
 * @param {Object} itemData - 条目数据
 * @param {string} itemData.title - 条目标题
 * @param {File} itemData.imageFile - 条目图片文件（可选，如果提供则直接上传）
 * @param {string} itemData.cover - 条目封面URL（如果没有imageFile则使用）
 * @returns {Promise<Object>} 创建结果
 */
export const createItem = async (itemData) => {
  try {
    // 如果有图片文件，使用FormData上传
    if (itemData.imageFile) {
      const formData = new FormData();
      formData.append('title', itemData.title);
      formData.append('cover', itemData.imageFile); // 后端接受 'cover' 字段名

      // 其他可选字段
      if (itemData.title_cn) formData.append('title_cn', itemData.title_cn);
      if (itemData.description) formData.append('description', itemData.description);
      if (itemData.status) formData.append('status', itemData.status);
      if (itemData.total_episodes) formData.append('total_episodes', itemData.total_episodes);
      if (itemData.release_date) formData.append('release_date', itemData.release_date);

      // genres需要特殊处理
      if (itemData.genres && itemData.genres.length > 0) {
        itemData.genres.forEach(genre => {
          formData.append('genres', genre);
        });
      }

      const response = await apiClient.post('/api/anime', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response?.data || {
        code: -1,
        message: '未获取到数据',
        data: null
      };
    }

    // 否则使用JSON格式（如果已经有cover URL）
    const response = await apiClient.post('/api/anime', {
      title: itemData.title,
      cover: itemData.cover || '', // 使用 cover 而不是 cover_url
      title_cn: itemData.title_cn || '',
      description: itemData.description || '',
      genres: itemData.genres || [],
      release_date: itemData.release_date || null,
      status: itemData.status || '',
      total_episodes: itemData.total_episodes || 0,
    });

    return response?.data || {
      code: -1,
      message: '未获取到数据',
      data: null
    };
  } catch (error) {
    console.error('创建条目失败:', error);
    if (error.response) {
      throw new Error(error.response.data?.message || `请求失败: ${error.response.status}`);
    } else if (error.request) {
      throw new Error('网络连接失败，请检查网络设置');
    } else {
      throw new Error('请求配置错误');
    }
  }
};

/**
 * 获取条目列表
 * @param {Object} params - 查询参数
 * @param {string} params.sort - 排序方式
 * @param {string} params.category - 分类
 * @param {number} params.page - 页码
 * @param {number} params.limit - 每页数量
 * @returns {Promise<Object>} 条目列表
 */
export const getItemList = async (params = {}) => {
  try {
    const query = {
      sort: params.sort,
      category: Array.isArray(params.category)
        ? params.category.join(',')
        : params.category,
      page: params.page,
      limit: params.limit,
    };

    // 使用 /api/anime/user_entries 端点，该端点只返回用户条目 (is_admin=false)
    const response = await apiClient.get('/api/anime/user_entries', { params: query });

    const respData = response?.data;
    let finalData = respData;
    
    if (respData && typeof respData === 'object' && 'code' in respData && 'data' in respData) {
      finalData = respData;
    } else {
      // 规范化响应
      finalData = {
        code: 0,
        message: 'success',
        data: respData
      };
    }

    // 注意：不再需要前端过滤，因为 /api/anime/user_entries 已经只返回用户条目
    // 分页信息由后端正确计算，无需前端重新计算

    return finalData;
  } catch (error) {
    console.error('获取条目列表失败:', error);
    throw error;
  }
};

/**
 * 获取条目详情
 * @param {number} id - 条目ID
 * @returns {Promise<Object>} 条目详情
 */
export const getItemDetail = async (id) => {
  try {
    const response = await apiClient.get(`/api/anime/${id}`);

    return response?.data || {
      code: -1,
      message: '未获取到数据',
      data: null
    };
  } catch (error) {
    console.error('获取条目详情失败:', error);
    if (error.response) {
      throw new Error(error.response.data?.message || `请求失败: ${error.response.status}`);
    } else if (error.request) {
      throw new Error('网络连接失败，请检查网络设置');
    } else {
      throw new Error('请求配置错误');
    }
  }
};

/**
 * 删除条目
 * @param {number} id - 条目ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteItem = async (id) => {
  try {
    const response = await apiClient.delete(`/api/anime/${id}`);

    return response?.data || {
      code: 0,
      message: '删除成功',
      data: null
    };
  } catch (error) {
    console.error('删除条目失败:', error);
    if (error.response) {
      // 特殊处理 403 错误
      if (error.response.status === 403) {
        // 检查用户是否已登录
        const token = localStorage.getItem('access_token');
        if (token) {
          // 用户已登录但无权限
          throw new Error('没有权限删除此条目');
        } else {
          // 用户未登录
          throw new Error('需要登录才能删除条目');
        }
      }
      throw new Error(error.response.data?.message || `请求失败: ${error.response.status}`);
    } else if (error.request) {
      throw new Error('网络连接失败，请检查网络设置');
    } else {
      throw new Error('请求配置错误');
    }
  }
};


/**
 * 更新条目
 * @param {number} id - 条目ID
 * @param {Object} itemData - 更新的条目数据
 * @param {string} itemData.title - 条目标题（可选）
 * @param {string} itemData.description - 条目描述（可选）
 * @param {string} itemData.cover - 封面URL（可选）
 * @param {File} itemData.coverFile - 封面图片文件（可选，如果提供则直接上传）
 * @returns {Promise<Object>} 更新结果
 */
export const updateItem = async (id, itemData) => {
  try {
    // 检查是否有任何修改内容
    const hasTitleChange = itemData.title !== undefined && itemData.title !== null;
    const hasDescriptionChange = itemData.description !== undefined && itemData.description !== null;
    const hasCoverUrlChange = itemData.cover !== undefined && itemData.cover !== null;
    const hasCoverFileChange = itemData.coverFile !== undefined && itemData.coverFile !== null;

    if (!hasTitleChange && !hasDescriptionChange && !hasCoverUrlChange && !hasCoverFileChange) {
      throw new Error('没有提供任何修改内容');
    }

    // 如果有图片文件，使用FormData上传
    if (itemData.coverFile) {
      const formData = new FormData();
      formData.append('item_id', id.toString());

      // 只添加有变化的字段
      if (hasTitleChange) {
        formData.append('title', itemData.title);
      }
      if (hasDescriptionChange) {
        formData.append('description', itemData.description);
      }

      // 添加封面文件
      formData.append('cover', itemData.coverFile);

      console.log('更新条目请求数据（FormData）:', {
        item_id: id.toString(),
        title: hasTitleChange ? itemData.title : '未修改',
        description: hasDescriptionChange ? itemData.description : '未修改',
        cover: '文件上传'
      });
      const response = await apiClient.post('/api/edit_item/', formData, {
        timeout: 60000 
      });

      console.log('更新条目响应:', response.data);
      return response?.data || {
        code: 0,
        message: '更新成功',
        data: null
      };
    }

    // 否则使用JSON格式（如果只有URL或文本修改）
    const updatePayload = {
      item_id: id.toString()
    };

    // 只添加有变化的字段
    if (hasTitleChange) {
      updatePayload.title = itemData.title;
    }
    if (hasDescriptionChange) {
      updatePayload.description = itemData.description;
    }
    if (hasCoverUrlChange) {
      updatePayload.cover = itemData.cover;
    }

    console.log('更新条目请求数据（JSON）:', updatePayload);
    const response = await apiClient.post('/api/edit_item/', updatePayload, {
        timeout: 10000
    });
    
    console.log('更新条目响应:', response.data);

    return response?.data || {
      code: 0,
      message: '更新成功',
      data: null
    };
  } catch (error) {
    console.error('更新条目失败:', error);
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
         throw new Error('上传超时，请检查网络或图片是否过大');
    }

    if (error.response) {
      // 特殊处理 403 错误
      if (error.response.status === 403) {
        // 检查用户是否已登录
        const token = localStorage.getItem('access_token');
        if (token) {
          // 用户已登录但无权限
          throw new Error('没有权限修改此条目');
        } else {
          // 用户未登录
          throw new Error('需要登录才能修改条目');
        }
      }
      throw new Error(error.response.data?.message || `请求失败: ${error.response.status}`);
    } else if (error.request) {
      throw new Error('网络连接失败，请检查网络设置');
    } else {
      throw new Error(error.message || '请求配置错误');
    }
  }
};