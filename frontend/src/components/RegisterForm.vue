<template>
  <div class="register-container">
    <h1>用户注册</h1>
    <form @submit.prevent="handleSubmit">
      <!-- 用户名 -->
      <div class="form-group">
        <label for="username">用户名</label>
        <input
          id="username"
          type="text"
          v-model.trim="form.username"
          @blur="validateUsername"
          placeholder="请输入3-20个字符"
          :class="{ 'is-invalid': errors.username }"
        />
        <p v-if="errors.username" class="error-message">{{ errors.username }}</p>
      </div>

      <!-- 邮箱 -->
      <div class="form-group">
        <label for="email">邮箱</label>
        <input
          id="email"
          type="email"
          v-model.trim="form.email"
          @blur="validateEmail"
          @input="errors.email = ''"
          placeholder="请输入您的邮箱地址"
          :class="{ 'is-invalid': errors.email }"
        />
        <p v-if="errors.email" class="error-message">{{ errors.email }}</p>
      </div>

      <!-- 验证码 -->
      <div class="form-group verification-group">
        <div class="verification-input">
          <input
            type="text"
            v-model.trim="form.code"
            placeholder="请输入验证码"
            :class="{ 'is-invalid': errors.verificationCode }"
          />
          <button
            type="button"
            @click="sendVerificationCode"
            :disabled="isCodeSending || countdown > 0 || !form.email"
          >
            {{ countdown > 0 ? `${countdown}s后重发` : (isCodeSending ? '发送中...' : '发送验证码') }}
          </button>
        </div>
        <p v-if="errors.verificationCode" class="error-message">{{ errors.verificationCode }}</p>
      </div>

      <!-- 密码 -->
      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          type="password"
          v-model.trim="form.password"
          @blur="validatePassword"
          placeholder="请输入至少6位密码"
          :class="{ 'is-invalid': errors.password }"
        /> 
        <!-- 密码强度指示器 -->
        <div v-if="form.password" class="password-strength">
          <div class="strength-bar">
            <div 
              class="strength-fill" 
              :class="strengthClass"
            ></div>
          </div>
          <p class="strength-message" :class="strengthClass">{{ strengthMsg }}</p>
        </div>
        <p v-if="errors.password" class="error-message">{{ errors.password }}</p>
      </div>

      <!-- 确认密码 -->
      <div class="form-group">
        <label for="confirmPassword">确认密码</label>
        <input
          id="confirmPassword"
          type="password"
          v-model.trim="form.confirmPassword"
          @blur="validateConfirmPassword"
          placeholder="请再次输入密码"
          :class="{ 'is-invalid': errors.confirmPassword }"
        />
        <p v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</p>
      </div>

      <!-- 提交按钮 -->
      <button type="submit" class="submit-btn" :disabled="isSubmitting">
        {{ isSubmitting ? '注册中...' : '立即注册' }}
      </button>
    </form>

    <!-- 成功提示模态框 -->
    <div v-if="showSuccessModal" class="modal-overlay" @click.self="closeSuccessModal">
      <div class="modal-content">
        <h2>🎉 注册成功！</h2>
        <p>欢迎您，{{ form.username }}！即将跳转到登录页...</p>
        <button @click="closeSuccessModal">确定</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from "vue-router";
const router = useRouter();


// --- 1. 数据状态管理 ---

// 表单数据
const form = reactive({
  username: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
});

// 错误信息对象
const errors = reactive({
  username: '',
  email: '',
  verificationCode: '',
  password: '',
  confirmPassword: '',
});

// 状态变量
const isCodeSending = ref(false); // 是否正在发送验证码
const countdown = ref(0); // 验证码倒计时
const isSubmitting = ref(false); // 是否正在提交
const showSuccessModal = ref(false); // 是否显示成功模态框
const registered = ref(false); // 是否已成功注册（防止重复提交）
const strengthMsg = ref('');          // 强度文字
const strengthClass = ref('');        // 对应颜色 class

/* // 模拟的“后端”验证码
const mockVerificationCode = ref(''); */


// --- 2. 校验逻辑 ---

// 校验用户名
const validateUsername = () => {
  if (!form.username) {
    errors.username = '用户名不能为空';
  } else if (form.username.length < 3 || form.username.length > 20) {
    errors.username = '用户名长度必须在3-20个字符之间';
  } else {
    errors.username = '';
  }
};

// 校验邮箱
const validateEmail = () => {
  const emailRegex = /^\S+@\S+\.\S+$/;
  if (!form.email) {
    errors.email = '邮箱不能为空';
  } else if (!emailRegex.test(form.email)) {
    errors.email = '请输入正确的邮箱格式';
  } else {
    errors.email = '';
  }
};

// 校验密码
const validatePassword = () => {
  const p = form.password

  /* ====== 错误逻辑（红字） ====== */
  if (!p) {
    errors.password = '密码不能为空'
  } else if (p.length < 6) {
    errors.password = '密码长度不能少于6位'
  } else {
    errors.password = ''          // 通过基础校验
  }

  /* ====== 强度提示（彩字） ====== */
  if (!p) {                       // 空输入不提示强度
    strengthMsg.value = ''
    strengthClass.value = ''
  } else if (p.length < 6) {      // 长度不达标只给错误，不给强度
    strengthMsg.value = ''
    strengthClass.value = ''
  } else if (!/[A-Z]/.test(p) || !/[0-9]/.test(p)) {
    strengthMsg.value = '建议包含大写字母和数字'
    strengthClass.value = 'medium'
  } else {
    strengthMsg.value = '密码强度良好'
    strengthClass.value = 'strong'
  }

  /* 联动确认密码 */
  if (form.confirmPassword) validateConfirmPassword()
}

 

// 校验确认密码
const validateConfirmPassword = () => {
  if (!form.confirmPassword) {
    errors.confirmPassword = '请再次输入密码';
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致';
  } else {
    errors.confirmPassword = '';
  }
};

// 校验验证码
const validateVerificationCode = () => {
  // 仅做必填校验，验证码是否正确应由后端在注册接口中校验
  if (!form.code) {
    errors.verificationCode = '验证码不能为空';
  } else {
    errors.verificationCode = '';
  }
};


// --- 3. 交互逻辑 ---

// 发送验证码
const sendVerificationCode = async () => {
  // 校验邮箱
  validateEmail();
  if (errors.email) return;

  isCodeSending.value = true;
  try {
    console.log(`正在向 ${form.email} 发送验证码（调用后端接口）...`);
    
    const payload = { email: form.email };

    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      redirect: 'follow',
    };

    const res = await fetch('/api/send_verification_code/', requestOptions);
    const text = await res.text();

    let returnedCode = null;
    try {
      const parsed = text ? JSON.parse(text) : null;
      if (parsed) {
        if (typeof parsed === 'object' && parsed.code) returnedCode = String(parsed.code);
        else if (typeof parsed === 'string') returnedCode = parsed;
      }
    } catch (e) {
      if (text && /\d{4,6}/.test(text)) returnedCode = text.match(/\d{4,6}/)?.[0] || null;
    }

    if (returnedCode) {
      mockVerificationCode.value = returnedCode;
      alert(`验证码已发送到邮箱 ${form.email}\n(服务器返回验证码: ${mockVerificationCode.value})`);
    } else {
      alert(`验证码已发送到邮箱 ${form.email}（请查收）`);
    }

    countdown.value = 60;
    const timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) {
        clearInterval(timer);
      }
    }, 1000);
  } catch (err) {
    console.error('发送验证码接口调用失败', err);
    errors.verificationCode = '发送验证码失败，请稍后重试';
  } finally {
    isCodeSending.value = false;
  }
};

// 提交表单
const handleSubmit = async () => {
  // 提交前，对所有字段进行一次完整校验
  validateUsername();
  validateEmail();
  validatePassword();
  validateConfirmPassword();
  validateVerificationCode();

  // 检查是否还有错误
  const hasErrors = Object.values(errors).some(error => error);
  if (hasErrors) {
    console.log('请修正表单错误后再提交');
    return;
  }

  if (isSubmitting.value || registered.value) return;

  Object.keys(errors).forEach(k => { errors[k] = ''; });

  isSubmitting.value = true;
  console.log('正在提交注册信息（调用后端）...', form);

  try {
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form) 
    };

    const res = await fetch('/api/register/', requestOptions);
    const text = await res.text();

    let parsed = null;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch (e) {
      // ignore
    }

    if (!res.ok) {
      const msg = (parsed && (parsed.message || parsed.error)) || text || res.statusText;
      errors.verificationCode = String(msg);
      console.error('注册接口返回错误', msg);
      isSubmitting.value = false;
      return;
    }

    Object.keys(errors).forEach(k => { errors[k] = ''; });
    
    try {
      const token = (parsed && (parsed.token || parsed.accessToken)) || null;
      const user = (parsed && parsed.user) || null;
      if (form.email) {
        localStorage.setItem("user_email", form.email);
      }
      if (token) localStorage.setItem('token', token);
      if (user) localStorage.setItem('currentUser', JSON.stringify(user));
    } catch (e) {
      // ignore
    }
    
    registered.value = true;
    isSubmitting.value = false;
    showSuccessModal.value = true;
    console.log('注册成功，后端返回：', parsed ?? text);
    
    setTimeout(() => {
      showSuccessModal.value = false;
      try { router.push('/login'); } catch (e) { console.warn('跳转失败', e); }
    }, 1200);
  } catch (err) {
    console.error('调用注册接口失败', err);
    errors.verificationCode = '注册失败，请稍后重试';
    isSubmitting.value = false;
  }
};

// 关闭成功模态框
const closeSuccessModal = () => {
  showSuccessModal.value = false;
  setTimeout(() => {
    router.push("/login");
  }, 2000);
  console.log('准备跳转到登录页...');
};

</script>

<style scoped>
/* --- 4. 样式 --- */
.register-container {
  max-width: 1000px;
  margin: 40px auto;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #fff;
}

h1 {
  text-align: center;
  color: #e58c8c;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}

input[type="text"],
input[type="email"],
input[type="password"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 14px;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #007bff;
}

input.is-invalid {
  border-color: #dc3545;
}

.error-message {
  color: #dc3545;
  font-size: 12px;
  margin-top: 5px;
  height: 16px; /* 固定高度防止布局抖动 */
}

/* 密码强度样式 */
.password-strength {
  margin-top: 8px;
}

.strength-bar {
  width: 100%;
  height: 4px;
  background-color: #e9ecef;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 5px;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.strength-fill.weak {
  width: 33%;
  background-color: #dc3545;
}

.strength-fill.medium {
  width: 66%;
  background-color: #ffc107;
}

.strength-fill.strong {
  width: 100%;
  background-color: #28a745;
}

.strength-message {
  font-size: 12px;
  margin: 0;
  height: 16px;
}

.strength-message.weak {
  color: #dc3545;
}

.strength-message.medium {
  color: #ffc107;
}

.strength-message.strong {
  color: #28a745;
}

.verification-group .verification-input {
  display: flex;
  gap: 10px;
}

.verification-group input {
  flex: 1;
}

.verification-group button {
  padding: 10px 15px;
  border: 1px solid #ec92bf;
  background-color:#ec92bf;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  transition: background-color 0.3s;
}

.verification-group button:hover:not(:disabled) {
  background-color: #0056b3;
}

.verification-group button:disabled {
  background-color: #a0cfff;
  border-color: #a0cfff;
  cursor: not-allowed;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  border: none;
  background-color: #f48398;
  color: white;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s;
}

.submit-btn:hover:not(:disabled) {
  background-color:  #f48398;
}

.submit-btn:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

 

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  max-width: 350px;
}

.modal-content h2 {
  margin-bottom: 15px;
}

.modal-content p {
  color: #666;
  margin-bottom: 20px;
}

.modal-content button {
  padding: 10px 20px;
  border: none;
  background-color: #ec92bf;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}
</style>
