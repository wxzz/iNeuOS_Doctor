<template>
  <div class="register-user-container">
    <!-- 标题 -->
    <h1 class="title">Ai体征分析助手</h1>
    
    <!-- 表单区域 -->
    <div class="form-container">
      <!-- 用户名输入框 -->
      <div class="input-group">
        <label class="input-label">用户名称</label>
        <input 
          v-model="username"
          type="text"
          class="input-field"
          placeholder="中文不少于3个，其他不少于6位"
        />
      </div>
      
      <!-- 密码输入框 -->
      <div class="input-group">
        <label class="input-label">输入密码</label>
        <input 
          v-model="password"
          type="password"
          class="input-field"
          placeholder="不少于8位字母和数字"
        />
      </div>
      
      <!-- 确认密码输入框 -->
      <div class="input-group">
        <label class="input-label">确认密码</label>
        <input 
          v-model="confirmPassword"
          type="password"
          class="input-field"
          placeholder="请再次输入密码"
        />
      </div>

       <!-- 输入手机号 -->
      <div class="input-group">
        <label class="input-label">手机号码</label>
        <input 
          v-model="phoneNumber"
          type="text"
          class="input-field"
          placeholder="请输入手机号码"
          @input="handlePhoneInput"
          maxlength="13"
        />
      </div>

      <!-- 手机验证码输入与发送 -->
      <div class="input-group code-group">
        <label class="input-label">短信验证码</label>
        <input
          v-model="smsCode"
          type="text"
          class="input-field code-input"
          placeholder="请输入6位验证码"
          maxlength="6"
          @input="handleCodeInput"
        />
        <button
          class="send-btn"
          type="button"
          @click="handleSendCode"
          :disabled="isSending || countdown > 0"
        >
          {{ sendButtonText }}
        </button>
      </div>
    </div>

    <!-- 图形验证码弹窗 -->
    <div v-if="showCaptchaModal" class="captcha-modal" @click="closeCaptchaModal">
      <div class="captcha-content" @click.stop>
        <div class="captcha-header">
          <h3>请输入图形验证码</h3>
          <button class="close-btn" @click="closeCaptchaModal">×</button>
        </div>
        <div class="captcha-body">
          <canvas
            ref="captchaCanvas"
            width="150"
            height="50"
            class="captcha-canvas"
            @click="refreshCaptcha"
          ></canvas>
          <button class="refresh-btn" @click="refreshCaptcha" title="刷新验证码">
            ⟳
          </button>
        </div>
        <input
          v-model="captchaInput"
          type="text"
          class="captcha-input"
          placeholder="请输入图形验证码"
          maxlength="4"
          @keyup.enter="verifyCaptcha"
        />
        <div class="captcha-footer">
          <button class="captcha-btn cancel-btn" @click="closeCaptchaModal">取消</button>
          <button class="captcha-btn confirm-btn" @click="verifyCaptcha">确定</button>
        </div>
      </div>
    </div>
    
    <!-- 协议复选框 -->
    <div class="input-group" style="align-items: flex-start; margin-left: -30px; margin-top: -5px; margin-bottom: 10px;">
      <input type="checkbox" id="user-license" v-model="isUserLicense" style="margin-top: 2px;" />
      <label for="user-license" style="font-size: 13px; color: #666; user-select: none;">
        阅读及同意
        <a href="javascript:void(0);" style="color: #4A90E2; text-decoration: underline;" @click="showLicenseModal = true">
          《Ai体征分析助手用户注册及使用协议》
        </a>
      </label>
    </div>

    <!-- 协议弹窗 -->
    <div v-if="showLicenseModal" class="license-modal" @click.self="showLicenseModal = false">
      <div class="license-content">
        <div class="license-header">
          <span class="license-title">用户协议</span>
          <button class="close-btn" @click="showLicenseModal = false">×</button>
        </div>
        <div class="license-body">
          <v-md-preview :text="licenseContent" />
        </div>
      </div>
    </div>

    <!-- 按钮组 -->
    <div class="button-group">
      <button 
        class="btn btn-register" 
        @click="handleRegister"
        :disabled="isLoading"
      >
        {{ isLoading ? '注册中...' : '注册' }}
      </button>
      <button class="btn btn-back" @click="handleBack">
        登录
      </button>
    </div>
    <div class="icp-footer">
      <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">京ICP备2020048381号-3</a>&nbsp;|
      <span v-if="appVersion" class="version-text">版本:v{{ appVersion }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import VMdPreview from '@kangc/v-md-editor/lib/preview';
import '@kangc/v-md-editor/lib/style/preview.css';
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';
import '@kangc/v-md-editor/lib/theme/style/github.css';
VMdPreview.use(githubTheme);
import licenseMd from '@/assets/file/user_license.md?raw'

const isUserLicense = ref(false)
const showLicenseModal = ref(false)
const licenseContent = ref(licenseMd)
import { ref, computed, onUnmounted, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { registerUser, sendVerifySmsCode } from '@/api/register'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const phoneNumber = ref('')
const smsCode = ref('')
const isLoading = ref(false)
const isSending = ref(false)
const countdown = ref(0)
const inviteCode = ref<string>((route.query.invite as string) || '')
const appVersion = (window as { VERSION?: string }).VERSION || ''
let countdownTimer: number | null = null

// 图形验证码相关
const showCaptchaModal = ref(false)
const captchaCanvas = ref<HTMLCanvasElement | null>(null)
const captchaInput = ref('')
const captchaCode = ref('')

const sendButtonText = computed(() => {
  if (isSending.value) return '发送中...'
  if (countdown.value > 0) return `${countdown.value}s`
  return '发送'
})

const handleRegister = async () => {
   
  // 验证输入
  if (!username.value || !username.value.trim()) {
    alert('请输入用户名')
    return
  }
  const name = username.value.trim();
  // 判断是否全为中文
  const isChinese = /^[\u4e00-\u9fa5]+$/.test(name);
  if (isChinese) {
    if (name.length < 3) {
      alert('中文用户名长度不少于3个汉字');
      return;
    }
  } else {
    // 英文、数字、混合
    if (name.length < 6) {
      alert('英文或数字用户名长度不少于6位');
      return;
    }
  }
  
  if (!password.value) {
    alert('请输入密码,密码长度不小于8位')
    return
  }

  // 密码长度验证（可选）
  if (password.value.length < 8) {
    alert('密码长度至少为8位')
    return
  }
  
  if (password.value !== confirmPassword.value) {
    alert('两次输入的密码不一致')
    return
  }
  // 手机号码验证
  const phoneRegex = /^1[3-9]\d{9}$/
  const unformattedPhone = phoneNumber.value.replace(/-/g, '')
  if (!unformattedPhone || !phoneRegex.test(unformattedPhone)) {
    alert('请输入正确的手机号码（11位数字）')
    return
  }

  if (!smsCode.value || !smsCode.value.trim()) {
    alert('请输入短信验证码')
    return
  }

   if (!isUserLicense.value) {
      alert('注册用户需要阅读及同意注册及使用协议')
      return
    }

  // 防止重复提交
  if (isLoading.value) {
    return
  }

  isLoading.value = true

  try {
    // 调用注册接口
    const result = await registerUser({
      user: username.value.trim(),
      pwd1: password.value,
      pwd2: confirmPassword.value,
      invite: inviteCode.value,
      phone: phoneNumber.value.replace(/-/g, ''),
      sms_code: smsCode.value.trim(),
      is_user_license: isUserLicense.value,
    })

    if (result.code === 200) {
      // 注册成功
      alert(result.message || '注册成功！')
      // 根据需求，注册成功后可以跳转到登录页面或我的页面
      // 这里跳转到登录页面
      router.push('/login')
    } else {
      // 注册失败
      alert(result.message || '注册失败')
    }
  } catch (error) {
    console.error('注册失败:', error)
    alert('注册失败，请稍后重试')
  } finally {
    isLoading.value = false
  }
}

const handleBack = () => {
  // 返回到登录页面
  router.push('/login')
}

// 手机号码格式化处理
const handlePhoneInput = (event: Event) => {
  let input = (event.target as HTMLInputElement).value
  // 只保留数字
  let digits = input.replace(/\D/g, '')
  // 限制为11位
  digits = digits.slice(0, 11)
  
  // 格式化为 XXX-XXXX-XXXX
  if (digits.length <= 3) {
    phoneNumber.value = digits
  } else if (digits.length <= 7) {
    phoneNumber.value = `${digits.slice(0, 3)}-${digits.slice(3)}`
  } else {
    phoneNumber.value = `${digits.slice(0, 3)}-${digits.slice(3, 7)}-${digits.slice(7)}`
  }
}

// 短信验证码仅保留数字，限制6位
const handleCodeInput = (event: Event) => {
  const digits = (event.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 6)
  smsCode.value = digits
}

// 生成图形验证码
const generateCaptcha = () => {
  // 生成4位随机数字+字母验证码
  const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
  let code = ''
  for (let i = 0; i < 4; i++) {
    code += chars[Math.floor(Math.random() * chars.length)]
  }
  captchaCode.value = code

  // 绘制验证码到canvas
  nextTick(() => {
    if (!captchaCanvas.value) return
    
    const canvas = captchaCanvas.value
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 绘制背景
    ctx.fillStyle = '#f0f0f0'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // 绘制干扰线
    for (let i = 0; i < 3; i++) {
      ctx.strokeStyle = `rgb(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255})`
      ctx.beginPath()
      ctx.moveTo(Math.random() * canvas.width, Math.random() * canvas.height)
      ctx.lineTo(Math.random() * canvas.width, Math.random() * canvas.height)
      ctx.stroke()
    }

    // 绘制验证码文字
    ctx.font = 'bold 30px Arial'
    ctx.textBaseline = 'middle'
    
    for (let i = 0; i < code.length; i++) {
      const char = code[i] || ''
      const x = 20 + i * 30
      const y = 25 + (Math.random() - 0.5) * 10
      const angle = (Math.random() - 0.5) * 0.4
      
      ctx.save()
      ctx.translate(x, y)
      ctx.rotate(angle)
      ctx.fillStyle = `rgb(${Math.random() * 100}, ${Math.random() * 100}, ${Math.random() * 100})`
      ctx.fillText(char, 0, 0)
      ctx.restore()
    }

    // 绘制干扰点
    for (let i = 0; i < 30; i++) {
      ctx.fillStyle = `rgb(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255})`
      ctx.beginPath()
      ctx.arc(
        Math.random() * canvas.width,
        Math.random() * canvas.height,
        1,
        0,
        2 * Math.PI
      )
      ctx.fill()
    }
  })
}

// 刷新验证码
const refreshCaptcha = () => {
  generateCaptcha()
  captchaInput.value = ''
}

// 打开图形验证码弹窗
const openCaptchaModal = () => {
  showCaptchaModal.value = true
  captchaInput.value = ''
  nextTick(() => {
    generateCaptcha()
  })
}

// 关闭图形验证码弹窗
const closeCaptchaModal = () => {
  showCaptchaModal.value = false
  captchaInput.value = ''
}

// 验证图形验证码
const verifyCaptcha = () => {
  if (!captchaInput.value) {
    alert('请输入图形验证码')
    return
  }

  if (captchaInput.value.toLowerCase() !== captchaCode.value.toLowerCase()) {
    alert('图形验证码错误，请重新输入')
    refreshCaptcha()
    return
  }

  // 验证通过，关闭弹窗并发送短信验证码
  closeCaptchaModal()
  sendSmsCode()
}

// 发送短信验证码（先验证图形验证码）
const handleSendCode = () => {
  // 防止重复点击
  if (isSending.value || countdown.value > 0) return

  const phoneRegex = /^1[3-9]\d{9}$/
  const unformattedPhone = phoneNumber.value.replace(/-/g, '')
  if (!unformattedPhone || !phoneRegex.test(unformattedPhone)) {
    alert('请先输入正确的手机号码（11位数字）')
    return
  }

  // 打开图形验证码弹窗
  openCaptchaModal()
}

// 实际发送短信验证码
const sendSmsCode = () => {
  const unformattedPhone = phoneNumber.value.replace(/-/g, '')
  
  isSending.value = true

  sendVerifySmsCode(unformattedPhone)
    .then((res) => {
      if (res.code === 200) {
        // 启动60秒倒计时
        countdown.value = 60
        countdownTimer = window.setInterval(() => {
          countdown.value -= 1
          if (countdown.value <= 0) {
            countdown.value = 0
            if (countdownTimer) {
              clearInterval(countdownTimer)
              countdownTimer = null
            }
          }
        }, 1000)
        //alert(res.message || '验证码已发送')
      } else {
        alert(res.message || '发送失败')
      }
    })
    .catch((error) => {
      console.error('发送验证码失败:', error)
      alert('发送失败，请稍后重试')
    })
    .finally(() => {
      isSending.value = false
    })
}

onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})
</script>

<!-- 协议弹窗样式 -->
<style scoped>
.license-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.license-content {
  background: #fff;
  border-radius: 10px;
  max-width: 600px;
  width: 90vw;
  max-height: 80vh;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18);
  padding: 0 0 16px 0;
  display: flex;
  flex-direction: column;
}
.license-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px 0 20px;
  font-size: 16px;
  font-weight: bold;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 10;
  /* 增加下边框以区分内容 */
  border-bottom: 1px solid #eee;
}
.license-title {
  font-size: 17px;
  color: #222;
  font-weight: bold;
  letter-spacing: 1px;
}

.license-body {
  padding: 10px 20px 0 20px;
  font-size: 14px;
  color: #333;
  overflow-y: auto;
  flex: 1 1 auto;
  max-height: calc(80vh - 56px);
}
.close-btn {
  background: none;
  border: none;
  font-size: 26px;
  color: #888;
  cursor: pointer;
  margin-left: -10px;
}
.close-btn:hover {
  color: #333;
}
</style>

<style scoped>
.register-user-container {
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
  gap: 10px;
  margin-bottom: 15px;
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

.input-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-label {
  font-size: 16px;
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

.code-group {
  gap: 7px;
}

.code-input {
  flex: 0 1 auto;
  width: calc(100% - 20px);
  margin-left: 2px;
}

.send-btn {
  padding: 10px 14px;
  background-color: #4A90E2;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.3s;
}

.send-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.send-btn:not(:disabled):hover {
  background-color: #357ABD;
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
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #ffffff;
  cursor: pointer;
  transition: background-color 0.3s;
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

.btn-register:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.btn-register:disabled:hover {
  background-color: #cccccc;
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

/* 图形验证码弹窗样式 */
.captcha-modal {
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

.captcha-content {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 16px;
  width: 90%;
  max-width: 300px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.captcha-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.captcha-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.captcha-body {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.captcha-canvas {
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background-color: #f9f9f9;
}

.refresh-btn {
  background-color: #4A90E2;
  color: #ffffff;
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s;
}

.refresh-btn:hover {
  background-color: #357ABD;
}

.captcha-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #cccccc;
  border-radius: 4px;
  font-size: 16px;
  box-sizing: border-box;
  margin-bottom: 12px;
  text-align: center;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.captcha-input:focus {
  border-color: #4A90E2;
  outline: none;
}

.captcha-footer {
  display: flex;
  gap: 12px;
}

.captcha-btn {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.cancel-btn {
  background-color: #999;
  color: #fff;
}

.cancel-btn:hover {
  background-color: #777;
}

.confirm-btn {
  background-color: #4A90E2;
  color: #fff;
}

.confirm-btn:hover {
  background-color: #357ABD;
}
</style>
