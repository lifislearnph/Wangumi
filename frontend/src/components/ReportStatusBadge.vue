<template>
  <span :class="['status-badge', statusClass, sizeClass]">
    <i :class="statusIcon"></i>
    <span class="status-text">{{ statusText }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 状态值: PENDING, RESOLVED, REJECTED
  status: {
    type: String,
    required: true,
    validator: (value) => ['PENDING', 'RESOLVED', 'REJECTED'].includes(value)
  },
  // 尺寸: small, medium, large
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  }
})

// 状态类名
const statusClass = computed(() => {
  const statusMap = {
    'PENDING': 'status-pending',
    'RESOLVED': 'status-resolved',
    'REJECTED': 'status-rejected'
  }
  return statusMap[props.status] || 'status-pending'
})

// 尺寸类名
const sizeClass = computed(() => {
  return `size-${props.size}`
})

// 状态图标
const statusIcon = computed(() => {
  const iconMap = {
    'PENDING': 'fas fa-clock',
    'RESOLVED': 'fas fa-check-circle',
    'REJECTED': 'fas fa-times-circle'
  }
  return iconMap[props.status] || 'fas fa-question-circle'
})

// 状态文本
const statusText = computed(() => {
  const textMap = {
    'PENDING': '待处理',
    'RESOLVED': '已处理',
    'REJECTED': '已驳回'
  }
  return textMap[props.status] || '未知'
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 12px;
  font-weight: 600;
  white-space: nowrap;
  transition: all 0.3s ease;
}

/* 状态颜色 */
.status-pending {
  background: linear-gradient(135deg, #ffa726, #ffb74d);
  color: white;
}

.status-resolved {
  background: linear-gradient(135deg, #66bb6a, #81c784);
  color: white;
}

.status-rejected {
  background: linear-gradient(135deg, #ef5350, #e57373);
  color: white;
}

/* 尺寸 */
.size-small {
  padding: 4px 10px;
  font-size: 11px;
  border-radius: 10px;
}

.size-small i {
  font-size: 10px;
}

.size-medium {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 12px;
}

.size-medium i {
  font-size: 12px;
}

.size-large {
  padding: 8px 16px;
  font-size: 15px;
  border-radius: 14px;
}

.size-large i {
  font-size: 14px;
}

.status-text {
  line-height: 1;
}
</style>
