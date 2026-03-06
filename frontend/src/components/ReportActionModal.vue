<template>
  <!-- 模态框遮罩 -->
  <div v-if="visible" class="modal-overlay" @click.self="handleClose">
    <div class="modal-container">
      <!-- 模态框头部 -->
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fas fa-gavel"></i>
          处理举报
        </h2>
        <button class="close-btn" @click="handleClose">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <!-- 模态框内容 -->
      <div class="modal-content">
        <!-- 举报信息摘要 -->
        <div v-if="report" class="report-summary">
          <div class="summary-row">
            <span class="summary-label">举报ID</span>
            <span class="summary-value report-id">#{{ report.id }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">举报人</span>
            <span class="summary-value">{{ report.reporter?.username || '未知' }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">举报对象</span>
            <span class="summary-value">{{ report.target_type }} (ID: {{ report.target_id }})</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">举报类型</span>
            <span :class="['category-badge', `category-${report.category?.toLowerCase()}`]">
              {{ report.category_display }}
            </span>
          </div>
        </div>

        <!-- 处理表单 -->
        <form @submit.prevent="handleSubmit" class="action-form">
          <!-- 处理动作选择 -->
          <div class="form-group">
            <label class="form-label">
              <i class="fas fa-tasks"></i>
              处理动作
              <span class="required">*</span>
            </label>
            <div class="action-options">
              <button
                type="button"
                :class="['action-option', { active: formData.action === 'RESOLVED' }]"
                @click="formData.action = 'RESOLVED'"
                :disabled="submitting"
              >
                <div class="option-icon resolved">
                  <i class="fas fa-check-circle"></i>
                </div>
                <div class="option-content">
                  <div class="option-title">同意举报</div>
                  <div class="option-desc">确认违规，处理内容</div>
                </div>
              </button>
              <button
                type="button"
                :class="['action-option', { active: formData.action === 'REJECTED' }]"
                @click="formData.action = 'REJECTED'"
                :disabled="submitting"
              >
                <div class="option-icon rejected">
                  <i class="fas fa-times-circle"></i>
                </div>
                <div class="option-content">
                  <div class="option-title">驳回举报</div>
                  <div class="option-desc">内容未违规，驳回举报</div>
                </div>
              </button>
            </div>
          </div>

          <!-- 处理说明 -->
          <div class="form-group">
            <label class="form-label">
              <i class="fas fa-comment-alt"></i>
              处理说明
            </label>
            <textarea
              v-model="formData.resolution"
              placeholder="请输入处理说明（可选）"
              class="form-textarea"
              rows="3"
              :disabled="submitting"
            ></textarea>
            <div class="form-hint">
              <i class="fas fa-info-circle"></i>
              处理说明将记录在系统中供后续查阅
            </div>
          </div>

          <!-- 同意举报时的额外选项 -->
          <div v-if="formData.action === 'RESOLVED'" class="additional-options">
            <!-- 是否封禁用户 -->
            <div class="form-group">
              <label class="form-label">
                <i class="fas fa-user-slash"></i>
                用户处理
              </label>
              <div class="checkbox-group">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    v-model="formData.ban_user"
                    class="checkbox-input"
                    :disabled="submitting"
                  />
                  <span class="checkbox-custom"></span>
                  <span class="checkbox-text">封禁被举报用户</span>
                </label>
                <p class="checkbox-hint">
                  勾选后，被举报对象的作者将被封禁
                </p>
              </div>
            </div>

            <!-- 封禁时长（如果选择封禁用户） -->
            <div v-if="formData.ban_user" class="form-group">
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
                    placeholder="自定义"
                    class="custom-input"
                    :disabled="submitting"
                  />
                  <span class="unit">天</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 确认提示 -->
          <div class="confirmation-section" v-if="formData.action">
            <div class="confirmation-icon" :class="formData.action.toLowerCase()">
              <i :class="formData.action === 'RESOLVED' ? 'fas fa-exclamation-triangle' : 'fas fa-info-circle'"></i>
            </div>
            <div class="confirmation-content">
              <h4 class="confirmation-title">确认{{ formData.action === 'RESOLVED' ? '同意' : '驳回' }}举报</h4>
              <p class="confirmation-text">
                {{ formData.action === 'RESOLVED'
                  ? '确定要同意此举报吗？' + (formData.ban_user ? `被举报用户将被封禁${formData.ban_duration}天。` : '举报对象内容将被标记。')
                  : '确定要驳回此举报吗？此操作将关闭举报并不采取任何措施。' }}
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
              :class="{
                'btn-resolved': formData.action === 'RESOLVED',
                'btn-rejected': formData.action === 'REJECTED'
              }"
              :disabled="submitting || !formData.action"
            >
              <i v-if="submitting" class="fas fa-spinner fa-spin"></i>
              <i v-else :class="formData.action === 'RESOLVED' ? 'fas fa-check' : 'fas fa-times'"></i>
              {{ submitting ? '处理中...' : (formData.action === 'RESOLVED' ? '同意举报' : '驳回举报') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  // 模态框是否可见
  visible: {
    type: Boolean,
    required: true
  },
  // 举报信息
  report: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['close', 'confirm', 'update:visible'])

// 表单数据
const formData = reactive({
  action: '', // 'RESOLVED' 或 'REJECTED'
  resolution: '',
  ban_user: false,
  ban_duration: 7
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

// 处理提交
const handleSubmit = async () => {
  if (!formData.action) {
    return
  }

  submitting.value = true

  try {
    const submitData = {
      action: formData.action,
      resolution: formData.resolution.trim() || undefined
    }

    // 如果是同意举报且选择封禁用户
    if (formData.action === 'RESOLVED' && formData.ban_user) {
      submitData.ban_user = true
      submitData.ban_duration = formData.ban_duration || 7
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
  formData.action = ''
  formData.resolution = ''
  formData.ban_user = false
  formData.ban_duration = 7
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
  max-width: 600px;
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

/* 举报信息摘要 */
.report-summary {
  background: rgba(255, 107, 157, 0.05);
  border: 1px solid rgba(255, 107, 157, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 107, 157, 0.1);
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.summary-value {
  font-size: 13px;
  color: #333;
  font-weight: 600;
}

.report-id {
  color: #ff6b9d;
  font-size: 15px;
}

.category-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  color: white;
}

.category-harassment {
  background: linear-gradient(135deg, #e91e63, #f06292);
}

.category-spam {
  background: linear-gradient(135deg, #ff9800, #ffb74d);
}

.category-inappropriate {
  background: linear-gradient(135deg, #9c27b0, #ba68c8);
}

.category-copyright {
  background: linear-gradient(135deg, #3f51b5, #7986cb);
}

.category-other {
  background: linear-gradient(135deg, #607d8b, #90a4ae);
}

/* 表单 */
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

/* 处理动作选择 */
.action-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 8px;
}

.action-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.action-option:hover:not(:disabled) {
  border-color: #ff6b9d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.2);
}

.action-option.active {
  border-color: #ff6b9d;
  background: rgba(255, 107, 157, 0.05);
  box-shadow: 0 4px 12px rgba(255, 107, 157, 0.2);
}

.action-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.option-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
  flex-shrink: 0;
}

.option-icon.resolved {
  background: linear-gradient(135deg, #66bb6a, #81c784);
}

.option-icon.rejected {
  background: linear-gradient(135deg, #ef5350, #e57373);
}

.option-content {
  flex: 1;
}

.option-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.option-desc {
  font-size: 11px;
  color: #666;
}

/* 文本域 */
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

.form-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #999;
}

.form-hint i {
  color: #ff6b9d;
}

/* 额外选项 */
.additional-options {
  background: rgba(76, 175, 80, 0.05);
  border: 1px solid rgba(76, 175, 80, 0.2);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 复选框 */
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

/* 封禁时长选择 */
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
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.duration-option:hover:not(:disabled) {
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
}

.custom-input {
  width: 80px;
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  text-align: center;
}

.custom-input:focus {
  outline: none;
  border-color: #ff6b9d;
}

.unit {
  color: #666;
  font-size: 13px;
}

/* 确认提示 */
.confirmation-section {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  margin: 16px 0;
}

.confirmation-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.confirmation-icon.resolved {
  color: #ff9800;
}

.confirmation-icon.rejected {
  color: #2196f3;
}

.confirmation-content {
  flex: 1;
}

.confirmation-title {
  margin: 0 0 8px 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.confirmation-text {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

/* 操作按钮 */
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

.btn-resolved {
  background: linear-gradient(135deg, #66bb6a, #81c784);
}

.btn-resolved:hover:not(:disabled) {
  background: linear-gradient(135deg, #4caf50, #66bb6a);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.btn-rejected {
  background: linear-gradient(135deg, #ef5350, #e57373);
}

.btn-rejected:hover:not(:disabled) {
  background: linear-gradient(135deg, #e53935, #ef5350);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 83, 80, 0.3);
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

  .action-options {
    grid-template-columns: 1fr;
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

  .summary-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .duration-options {
    justify-content: center;
  }

  .duration-option {
    padding: 6px 12px;
    font-size: 12px;
  }

  .custom-input {
    width: 70px;
  }
}
</style>
