<template>
  <div class="login-container">
    <!-- 标题 -->
    <h1 class="title">Ai体征分析助手</h1>
    
    <!-- 表单区域 -->
    <div class="form-container">
      <!-- 错误信息显示 -->
      <div v-show="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      
      <!-- 用户名输入框 -->
      <div class="input-group">
        <label class="input-label">用户名称</label>
        <input 
          v-model="username"
          type="text"
          class="input-field"
          placeholder="请输入用户名称"
          @input="errorMessage = ''"
        />
      </div>
      
      <!-- 密码输入框 -->
      <div class="input-group">
        <label class="input-label">用户密码</label>
        <input 
          v-model="password"
          type="password"
          class="input-field"
          placeholder="请输入用户密码"
          @input="errorMessage = ''"
        />
      </div>
    </div>
    
    <!-- 按钮组 -->
    <div class="button-group">
      <button 
        class="btn btn-login" 
        @click="handleLogin"
        :disabled="isLoading"
      >
        {{ isLoading ? '登录中...' : '登录' }}
      </button>
      <button class="btn btn-register" @click="goToRegister">
        注册
      </button>
      <button class="btn btn-back" @click="handleBack">
        返回
      </button>
    </div>
    <div class="icp-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">京ICP备2020048381号-3</a>&nbsp;|
      <span v-if="appVersion" class="version-text">版本:v{{ appVersion }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login } = useAuth()

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const appVersion = (window as { VERSION?: string }).VERSION || ''

const handleLogin = async () => {
  // 验证输入
  if (!username.value || !username.value.trim()) {
    alert('请输入用户名称')
    return
  }
  
  if (!password.value) {
    alert('请输入用户密码')
    return
  }

  // 防止重复提交
  if (isLoading.value) {
    return
  }

  isLoading.value = true

  try {
    const result = await login(username.value.trim(), password.value)
    
    // 严格检查：只有 success 明确为 true 时才跳转
    if (result && result.success === true) {
      // 登录成功，跳转到 MyInfo 页面（用户信息由 MyInfo 页面负责获取并缓存）
      router.push('/my-info')
    } else {
      // 登录失败，不进行跳转，显示错误提示
      const errorMsg = result?.message || '登录失败，请检查用户名和密码'
      errorMessage.value = errorMsg
      // 确保不跳转
      return
    }
  } catch (error) {
    errorMessage.value = '登录失败，请稍后重试'
    // 作为备用，也显示alert
    alert('登录失败，请稍后重试')
    // 确保异常时也不跳转
    return
  } finally {
    isLoading.value = false
  }
}

const handleBack = () => {
  router.push('/')
}

const goToRegister = () => {
  router.push('/register-user')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 20px 20px;
}

.title {
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  width: 100%;
  max-width: 400px;
  box-sizing: border-box;
  margin: 0 auto 16px auto;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #667eea 100%);
  color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  letter-spacing: 1px;
}

.form-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 20px;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  text-align: center;
  padding: 8px;
  background-color: #fdf2f2;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.input-label {
  font-size: 14px;
  color: #333333;
  min-width: 80px;
  text-align: left;
}

.input-field {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #cccccc;
  border-radius: 4px;
  font-size: 14px;
  background-color: #ffffff;
  color: #333333;
  outline: none;
  transition: border-color 0.3s;
}

.input-field:focus {
  border-color: #4A90E2;
}

.input-field::placeholder {
  color: #999999;
}

.button-group {
  display: flex;
  gap: 16px;
  width: 100%;
  max-width: 400px;
  justify-content: center;
}

.btn {
  flex: 1;
  min-width: 80px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  cursor: pointer;
  transition: background-color 0.3s;
  white-space: nowrap;
}

.btn-login {
  background-color: #4A90E2;
}

.btn-login:hover {
  background-color: #357ABD;
}

.btn-login:active {
  background-color: #2E6BA0;
}

.btn-register {
  background-color: #4A90E2;
}

.btn-register:hover {
  background-color: #357ABD;
}

.btn-register:active {
  background-color: #2E6BA0;
}

.btn-back {
  background-color: #4A90E2;
}

.btn-back:hover {
  background-color: #357ABD;
}

.btn-back:active {
  background-color: #2E6BA0;
}

.btn-login:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.btn-login:disabled:hover {
  background-color: #cccccc;
}

.icp-footer {
  margin-top: auto;
  padding: 16px 0 4px;
  font-size: 12px;
  color: #666;
  text-align: center;
}

.icp-footer a {
  color: #666;
  text-decoration: none;
}

.icp-footer a:hover {
  color: #4A90E2;
  text-decoration: underline;
}

.version-text {
  margin-left: 2px;
  color: #666;
}
</style>
