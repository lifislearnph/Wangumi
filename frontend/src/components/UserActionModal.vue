<template>
  <!-- 模态框遮罩 -->
  <div v-if="visible" class="modal-overlay" @click.self="handleClose">
    <div class="modal-container">
      <!-- 模态框头部 -->
      <div class="modal-header">
        <h2 class="modal-title">
          <i :class="modalIcon"></i>
          {{ modalTitle }}
        </h2>
        <button class="close-btn" @click="handleClose">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <!-- 模态框内容 -->
      <div class="modal-content">
        <!-- 用户信息 -->
        <div class="user-info" v-if="user">
          <div class="user-avatar">
            <img 
              :src="user.profile?.avatar || '/default-avatar.png'" 
              :alt="user.username"
              class="avatar"
            />
          </div>
          <div class="user-details">
            <h3 class="username">{{ user.username }}</h3>
            <p class="user-email">{{ user.email }}</p>
            <div class="user-status">
              <UserStatusBadge :status="user.status" size="small" />
            </div>
          </div>
        </div>

        <!-- 表单区域 -->
        <form @submit.prevent="handleSubmit" class="action-form">
          <!-- 理由输入 -->
          <div class="form-group">
            <label class="form-label">
              <i class="fas fa-comment-alt"></i>
              {{ actionType === 'ban' ? '封禁理由' : '解封理由' }}
              <span class="required">*</span>
            </label>
            <textarea
              v-model="formData.reason"
              :placeholder="actionType === 'ban' ? '请输入封禁理由...' : '请输入解封理由...'"
              class="form-textarea"
              rows="3"
              required
              :disabled="submitting"
            ></textarea>
            <div v-if="formErrors.reason" class="error-message">
              <i class="fas fa-exclamation-circle"></i>
              {{ formErrors.reason }}
            </div>
          </div>

          <!-- 封禁时长（仅封禁时显示） -->
          <div class="form-group" v-if="actionType === 'ban'">
            <label class="form-label">
              <i class="fas fa-calendar-alt"></i>
              封禁时长（天）
            </label>
            <div class="duration-options">
              <button
                v-for="duration in durationOptions"
                :key="duration.value"
                type="button"
                :class="['duration-option', { active: formData.ban_duration === duration.value }]"
                @click="formData.ban_duration = duration.value"
                :disabled="submitting"
              >
                {{ duration.label }}
              </button>
              <div class="custom-duration">
                <input
                  type="number"
                  v-model="formData.ban_duration"
                  min="1"
                  max="365"
                  placeholder="自定义天数"
                  class="custom-input"
                  :disabled="submitting"
                />
                <span class="unit">天</span>
              </div>
            </div>
          </div>


          <!-- 确认提示 -->
          <div class="confirmation-section">
            <div class="confirmation-icon">
              <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="confirmation-content">
              <h4 class="confirmation-title">确认操作</h4>
              <p class="confirmation-text">
                {{ actionType === 'ban' 
                  ? `确定要封禁用户 "${user?.username}" 吗？此操作将禁止用户登录和访问平台。` 
                  : `确定要解封用户 "${user?.username}" 吗？此操作将恢复用户的正常访问权限。` }}
              </p>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="modal-actions">
            <button
              type="button"
              class="btn btn-cancel"
              @click="handleClose"
              :disabled="submitting"
            >
              <i class="fas fa-times"></i>
              取消
            </button>
            <button
              type="submit"
              class="btn btn-confirm"
              :class="{ 'btn-danger': actionType === 'ban', 'btn-success': actionType === 'unban' }"
              :disabled="submitting || !formData.reason.trim()"
            >
              <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
              <i v-else :class="actionType === 'ban' ? 'fas fa-ban' : 'fas fa-check-circle'"></i>
              {{ submitting ? '处理中...' : confirmButtonText }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import UserStatusBadge from './UserStatusBadge.vue'

const props = defineProps({
  // 模态框是否可见
  visible: {
    type: Boolean,
    required: true
  },
  // 操作类型：'ban' 或 'unban'
  actionType: {
    type: String,
    required: true,
    validator: (value) => ['ban', 'unban'].includes(value)
  },
  // 用户信息
  user: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close', 'confirm', 'update:visible'])

// 表单数据
const formData = reactive({
  reason: '',
  ban_duration: 7
})

// 表单错误
const formErrors = reactive({
  reason: ''
})

// 提交状态
const submitting = ref(false)

// 封禁时长选项
const durationOptions = [
  { value: 1, label: '1天' },
  { value: 3, label: '3天' },
  { value: 7, label: '7天' },
  { value: 30, label: '30天' },
  { value: 90, label: '90天' }
]

// 计算属性
const modalTitle = computed(() => {
  return props.actionType === 'ban' ? '封禁用户' : '解封用户'
})

const modalIcon = computed(() => {
  return props.actionType === 'ban' ? 'fas fa-ban' : 'fas fa-check-circle'
})

const confirmButtonText = computed(() => {
  return props.actionType === 'ban' ? '确认封禁' : '确认解封'
})

// 表单验证
const validateForm = () => {
  let isValid = true
  formErrors.reason = ''

  if (!formData.reason.trim()) {
    formErrors.reason = props.actionType === 'ban' ? '请输入封禁理由' : '请输入解封理由'
    isValid = false
  } else if (formData.reason.trim().length < 5) {
    formErrors.reason = '理由至少需要5个字符'
    isValid = false
  }

  if (props.actionType === 'ban' && formData.ban_duration < 1) {
    formData.ban_duration = 1
  }

  return isValid
}

// 处理提交
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  submitting.value = true

  try {
    const submitData = {
      reason: formData.reason.trim()
    }

    if (props.actionType === 'ban') {
      submitData.ban_duration = formData.ban_duration
    }

    emit('confirm', submitData)
  } catch (error) {
    console.error('表单提交错误:', error)
  } finally {
    submitting.value = false
  }
}

// 处理关闭
const handleClose = () => {
  if (submitting.value) return
  resetForm()
  emit('update:visible', false)
  emit('close')
}

// 重置表单
const resetForm = () => {
  formData.reason = ''
  formData.ban_duration = 7
  formErrors.reason = ''
}

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-container {
  background: linear-gradient(135deg, #ffffff, #f8f9fa);
  border-radius: 20px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
  background: linear-gradient(135deg, #ff6b9d, #ff8eb4);
  border-radius: 20px 20px 0 0;
  color: white;
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  font-size: 16px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.modal-content {
  padding: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 107, 157, 0.05);
  border-radius: 12px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 107, 157, 0.1);
}

.user-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #ff6b9d;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.username {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.user-email {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
}

.user-status {
  display: inline-block;
}

.action-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.form-label i {
  color: #ff6b9d;
}

.required {
  color: #ff4081;
}

.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  transition: all 0.3s ease;
  background: white;
}

.form-textarea:focus {
  outline: none;
  border-color: #ff6b9d;
  box-shadow: 0 0 0 3px rgba(255, 107, 157, 0.1);
}

.form-textarea:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #ff4081;
  font-size: 12px;
  margin-top: 4px;
}

.error-message i {
  font-size: 14px;
}

.duration-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.duration-option {
  padding: 8px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 20px;
  background: white;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.duration-option:hover {
  border-color: #ff6b9d;
  color: #ff6b9d;
}

.duration-option.active {
  background: #ff6b9d;
  border-color: #ff6b9d;
  color: white;
}

.duration-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.custom-duration {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.custom-input {
  width: 100px;
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.custom-input:focus {
  outline: none;
  border-color: #ff6b9d;
}

.unit {
  color: #666;
  font-size: 14px;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #e0e0e0;
  border-radius: 4px;
  position: relative;
  transition: all 0.3s ease;
}

.checkbox-input:checked + .checkbox-custom {
  background: #ff6b9d;
  border-color: #ff6b9d;
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.checkbox-text {
  font-size: 14px;
  color: #333;
}

.checkbox-hint {
  font-size: 12px;
  color: #666;
  margin: 0;
  padding-left: 30px;
}

.confirmation-section {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 193, 7, 0.2);
  margin: 16px 0;
}

.confirmation-icon {
  color: #ff9800;
  font-size: 24px;
}

.confirmation-content {
  flex: 1;
}

.confirmation-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.confirmation-text {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-cancel:hover:not(:disabled) {
  background: #e0e0e0;
  transform: translateY(-2px);
}

.btn-confirm {
  color: white;
}

.btn-danger {
  background: linear-gradient(135deg, #ff4081, #ff6b9d);
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #e91e63, #ff4081);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 64, 129, 0.3);
}

.btn-success {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
}

.btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #388e3c, #4caf50);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-container {
    max-width: 95%;
    margin: 10px;
  }
  
  .modal-header {
    padding: 16px 20px;
  }
  
  .modal-title {
    font-size: 18px;
  }
  
  .modal-content {
    padding: 20px;
  }
  
  .user-info {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .user-details {
    text-align: center;
  }
  
  .duration-options {
    justify-content: center;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .modal-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .close-btn {
    align-self: flex-end;
    margin-top: -40px;
  }
  
  .duration-option {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .custom-input {
    width: 80px;
  }
}
</style>
