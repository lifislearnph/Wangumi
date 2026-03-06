<template>
  <span 
    :class="['user-status-badge', statusClass, sizeClass]"
    :title="tooltipText"
  >
    <i :class="statusIcon"></i>
    <span class="status-text">{{ displayText }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 用户状态：'active' 或 'banned'
  status: {
    type: String,
    required: true,
    validator: (value) => ['active', 'banned', '正常', '已封禁'].includes(value)
  },
  // 显示文本，如果不提供则根据状态自动生成
  text: {
    type: String,
    default: ''
  },
  // 组件大小：'small', 'medium', 'large'
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true
  },
  // 是否显示文本
  showText: {
    type: Boolean,
    default: true
  }
})

// 计算状态类
const statusClass = computed(() => {
  const statusValue = props.status.toLowerCase()
  if (statusValue === 'active' || statusValue === '正常') {
    return 'status-active'
  } else if (statusValue === 'banned' || statusValue === '已封禁') {
    return 'status-banned'
  }
  return 'status-unknown'
})

// 计算大小类
const sizeClass = computed(() => `size-${props.size}`)

// 计算显示文本
const displayText = computed(() => {
  if (props.text) return props.text
  
  const statusValue = props.status.toLowerCase()
  if (statusValue === 'active' || statusValue === '正常') {
    return '正常'
  } else if (statusValue === 'banned' || statusValue === '已封禁') {
    return '已封禁'
  }
  return '未知'
})

// 计算图标
const statusIcon = computed(() => {
  const statusValue = props.status.toLowerCase()
  if (statusValue === 'active' || statusValue === '正常') {
    return 'fas fa-check-circle'
  } else if (statusValue === 'banned' || statusValue === '已封禁') {
    return 'fas fa-ban'
  }
  return 'fas fa-question-circle'
})

// 计算tooltip文本
const tooltipText = computed(() => {
  const statusValue = props.status.toLowerCase()
  if (statusValue === 'active' || statusValue === '正常') {
    return '用户账号正常'
  } else if (statusValue === 'banned' || statusValue === '已封禁') {
    return '用户账号已被封禁'
  }
  return '用户状态未知'
})
</script>

<style scoped>
.user-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 500;
  transition: all 0.3s ease;
  user-select: none;
  white-space: nowrap;
}

/* 状态样式 */
.status-active {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(76, 175, 80, 0.25));
  color: #2e7d32;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.status-banned {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.15), rgba(244, 67, 54, 0.25));
  color: #c62828;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.status-unknown {
  background: linear-gradient(135deg, rgba(158, 158, 158, 0.15), rgba(158, 158, 158, 0.25));
  color: #616161;
  border: 1px solid rgba(158, 158, 158, 0.3);
}

/* 大小样式 */
.size-small {
  font-size: 12px;
  padding: 2px 8px;
  gap: 4px;
}

.size-small .status-text {
  font-size: 11px;
}

.size-small i {
  font-size: 11px;
}

.size-medium {
  font-size: 14px;
  padding: 4px 12px;
  gap: 6px;
}

.size-medium .status-text {
  font-size: 13px;
}

.size-medium i {
  font-size: 13px;
}

.size-large {
  font-size: 16px;
  padding: 6px 16px;
  gap: 8px;
}

.size-large .status-text {
  font-size: 15px;
}

.size-large i {
  font-size: 15px;
}

/* 图标样式 */
.user-status-badge i {
  transition: transform 0.3s ease;
}

.user-status-badge:hover i {
  transform: scale(1.1);
}

/* 文本样式 */
.status-text {
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* 悬停效果 */
.user-status-badge:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.status-active:hover {
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.2);
}

.status-banned:hover {
  box-shadow: 0 4px 8px rgba(244, 67, 54, 0.2);
}

.status-unknown:hover {
  box-shadow: 0 4px 8px rgba(158, 158, 158, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .size-large {
    font-size: 14px;
    padding: 5px 14px;
  }
  
  .size-large .status-text {
    font-size: 13px;
  }
  
  .size-large i {
    font-size: 13px;
  }
}
</style>
