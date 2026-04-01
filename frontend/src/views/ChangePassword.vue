<template>
  <div class="change-password-overlay" @click.self="handleBack">
    <div class="change-password-container">
      <h1 class="title">修改密码</h1>
      
      <div class="form-container">
        <div class="input-row">
          <label class="input-label">用户名称</label>
          <input 
            type="text" 
            class="input-field" 
            v-model="username"
            placeholder="请输入用户名称"
            readonly
          />
        </div>

        <div class="input-row">
          <label class="input-label">旧密码</label>
          <input 
            type="password" 
            class="input-field" 
            v-model="oldPassword"
            placeholder="请输入旧密码"
          />
        </div>

        <div class="input-row">
          <label class="input-label">新密码</label>
          <input 
            type="password" 
            class="input-field" 
            v-model="password"
            placeholder="请输入新密码"
          />
        </div>
        
        <div class="input-row">
          <label class="input-label">确认密码</label>
          <input 
            type="password" 
            class="input-field" 
            v-model="confirmPassword"
            placeholder="请再次输入密码"
          />
        </div>
      </div>
      
      <div class="button-container">
        <button class="action-button modify-btn" @click="handleModify" :disabled="isLoading">
          {{ isLoading ? '修改中...' : '修改' }}
        </button>
        <button class="action-button return-btn" @click="handleBack">返回</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'
import { changePassword } from '../api/auth'

const { userInfo } = useAuth()

const username = ref(userInfo.value.user_account || '')
const oldPassword = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)

const emit = defineEmits<{
  close: []
}>()

const handleModify = async () => {
  // 验证输入
  if (!username.value || !oldPassword.value || !password.value || !confirmPassword.value) {
    alert('请填写完整信息')
    return
  }
  
  if (password.value !== confirmPassword.value) {
    alert('两次输入的密码不一致')
    return
  }

  // 防止重复提交
  if (isLoading.value) {
    return
  }

  isLoading.value = true

  try {
    const result = await changePassword({
      user: username.value,
      old_pwd: oldPassword.value,
      new_pwd: password.value,
    })

    if (result.code === 200) {
      alert('密码修改成功')
      emit('close')
    } else {
      alert(result.message || '密码修改失败')
    }
  } catch (error) {
    console.error('修改密码异常:', error)
    alert('密码修改失败，请稍后重试')
  } finally {
    isLoading.value = false
  }
}

const handleBack = () => {
  emit('close')
}
</script>

<style scoped>
.change-password-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.change-password-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.title {
  text-align: center;
  font-size: 16px;
  font-weight: bold;
  width: 100%;
  max-width: 500px;
  box-sizing: border-box;
  margin: 0 auto 10px auto;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #667eea 100%);
  color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.form-container {
  margin-bottom: 20px;
}

.input-row {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.input-label {
  width: 100px;
  font-size: 14px;
  color: #333;
  text-align: left;
  flex-shrink: 0;
}

.input-field {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
  margin-left: -20px;
}

.input-field:focus {
  border-color: #4A90E2;
}

.input-field::placeholder {
  color: #999;
}

.button-container {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.action-button {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
  min-width: 100px;
}

.modify-btn {
  background-color: #4A90E2;
  color: #fff;
}

.modify-btn:hover {
  background-color: #357ABD;
}

.return-btn {
  background-color: #4A90E2;
  color: #fff;
}

.return-btn:hover {
  background-color: #357ABD;
}
</style>
