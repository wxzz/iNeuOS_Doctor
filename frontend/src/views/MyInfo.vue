<template>
  <div class="my-info-container">
    <h1 class="title">Ai体征分析助手</h1>
    <!-- 头像和基本信息卡片 -->
    <div class="card">
      <div class="card-header">
        <div class="avatar" @click="openAvatarModal" title="点击修改头像">
          <img :src="myInfo.avatar ? `data:image/png;base64,${myInfo.avatar}` : defaultAvatar" alt="头像" class="avatar-image" />
        </div>
        <div class="basic-info">
          <div class="name">{{ isLoggedIn ? myInfo.user_account : '未登录' }}</div>
          <div class="status-line">状态：{{ isLoggedIn ? myInfo.status : '未登录' }}</div>
        </div>
        <div class="header-right">
          <div class="balance-row">
            <span class="label">算力点：</span>
            <span class="balance">{{ isLoggedIn ? Number(myInfo.account_credit).toFixed(2) : '0.00' }}</span>
            <button class="charge-btn" @click="openPaymentModal">赞助</button>
          </div>
          <div class="balance-row">
            <span class="label">分成额：</span>
            <span class="balance">{{ isLoggedIn ? Number(myInfo.cash).toFixed(2) : '0.00' }}</span>
            <button class="charge-btn" @click="handleWithdraw">提现</button>
          </div>
        </div>
      </div>
      <div class="info-row">
        <span class="field-label">分析：</span>
        <span class="field-value">{{ isLoggedIn ? myInfo.medical_count : 0 }} 次</span>
      </div>
      <div class="info-row">
        <span class="field-label">消耗：</span>
        <span class="field-value">{{ isLoggedIn ? Number(myInfo.cost_sum).toFixed(2) : '0.00' }} 算力点</span>
      </div>
      <div class="info-row">
        <span class="field-label">注册：</span>
        <span class="field-value">{{ isLoggedIn ? myInfo.create_time : new Date().toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).replace(/\//g, '-') }}</span>
      </div>
      <div class="info-row">
        <span class="field-label">登录：</span>
        <span class="field-value">{{ isLoggedIn && myInfo.last_login_time ? myInfo.last_login_time : '未登录' }}</span>
      </div>
      <div class="info-row">
        <span class="field-label">手机：</span>
        <span class="field-value">{{ myInfo.mobile }}</span>
      </div>
      <div class="info-row">
        <span class="field-label">邮箱：</span>
        <span class="field-value">{{ myInfo.email }}</span>
      </div>
    </div>

    <!-- 底部操作按钮 -->
    <div class="action-buttons">
      <button class="action-btn danger" @click="handleLogout">退出账户</button>
      <button class="action-btn primary" @click="showChangePassword">修改密码</button>
      <button class="action-btn primary" @click="handleSponsor">邀请好友</button>
    </div>

    <!-- 修改密码弹窗 -->
    <ChangePassword v-if="isChangePasswordVisible" @close="hideChangePassword" />

    <input ref="avatarFileInput" type="file" accept="image/*" class="hidden-file-input" @change="handleAvatarFileChange" />

    <div v-if="isAvatarModalVisible" class="avatar-overlay" @click.self="closeAvatarModal">
      <div class="avatar-panel">
        <div class="avatar-header">
          <h3>修改头像</h3>
          <button class="avatar-close" @click="closeAvatarModal">×</button>
        </div>
        <p class="avatar-subtitle">预览 144×144，可拖动滑块调整缩放</p>
        <div class="avatar-preview-box">
          <div class="avatar-preview-frame">
            <img v-if="previewAvatar" :src="previewAvatar" :style="{ transform: `scale(${avatarZoom})` }" alt="头像预览" class="avatar-preview-image" />
            <div v-else class="avatar-preview-placeholder">请选择图片</div>
          </div>
          <div class="avatar-live-144">
            <canvas ref="avatarCanvas" width="144" height="144" class="avatar-canvas"></canvas>
            <span class="avatar-live-label">144×144</span>
          </div>
        </div>
        <div class="avatar-controls">
          <div class="slider-row">
            <span>缩放</span>
            <input type="range" min="1" max="3" step="0.1" v-model.number="avatarZoom" @input="renderAvatarCanvas" />
            <span class="slider-value">{{ avatarZoom.toFixed(1) }}x</span>
          </div>
          <div class="avatar-buttons">
            <button @click="triggerSelectAvatar">选择</button>
            <button class="primary" :disabled="avatarSaving" @click="submitAvatar">修改</button>
          </div>
          <div v-if="avatarError" class="avatar-error">{{ avatarError }}</div>
        </div>
      </div>
    </div>

      <div v-if="isInviteVisible" class="invite-overlay" @click.self="closeInvite">
        <div class="invite-panel">
          <div class="invite-header">
            <h3>邀请好友赚信誉度和提成</h3>
            <button class="invite-close" @click="closeInvite">×</button>
          </div>
          <p class="invite-subtitle">每邀请1位好友注册，奖励9.9信誉度，每天最多2次奖励。<br/>被邀请人充值使用本系统，邀请人获得赞助额的10%提成。</p>

          <div class="invite-link">
            <textarea readonly :value="inviteLink || '正在生成邀请链接...'" rows="3"></textarea>
            <button @click="copyInviteLink" :disabled="!inviteLink">复制链接</button>
          </div>
          <div v-if="inviteLoading" class="invite-hint">正在生成邀请码...</div>
          <div v-if="inviteError" class="invite-error">{{ inviteError }}</div>

          <div class="stats">
            <div class="stat-item">已邀请：<span>{{ invitedCount }}人</span></div>
            <div class="stat-item">获得算力点：<span>{{ Number(increaseCostTotal).toFixed(2) }}</span></div>
            <div class="stat-item">获得分成额：<span>{{ Number(myInfo.cash).toFixed(2) }}</span></div>
          </div>

          <div v-if="inviteLink && !inviteLoading" class="qrcode-section">
            <h4>邀请朋友注册，微信扫描二维码</h4>
            <div class="qrcode-display">
              <canvas ref="inviteQrcodeCanvas" class="invite-qrcode"></canvas>
            </div>
            <button class="download-btn" @click="downloadBrochure">下载邀请朋友注册宣传册</button>
          </div>
        </div>
      </div>

    <!-- 宣传册图片预览弹窗 -->
    <div v-if="isBrochurePreviewVisible" class="brochure-preview-overlay" @click.self="closeBrochurePreview">
      <div class="brochure-preview-panel">
        <div class="brochure-preview-header">
          <h3>邀请朋友注册宣传册</h3>
          <button class="brochure-preview-close" @click="closeBrochurePreview">×</button>
        </div>
        <p class="brochure-preview-tip">移动设备：长按图片保存到相册<br/>电脑：右键图片选择“图片另存为”</p>
        <div class="brochure-preview-content">
          <img v-if="brochureImageUrl" :src="brochureImageUrl" alt="宣传册" class="brochure-preview-image" />
        </div>
      </div>
    </div>

    <!-- 微信支付弹窗 -->
    <div v-if="isPaymentModalVisible" class="payment-modal-overlay" @click="closePaymentModal">
      <div class="payment-modal-content" @click.stop>
        <div class="payment-modal-header">
          <h3>赞助算力点</h3>
          <button class="payment-modal-close-btn" @click="closePaymentModal">×</button>
        </div>
        <div class="payment-modal-body">
          <div class="amount-selector">
            <label>选择赞助额度</label>
            <div class="amount-options">
              <button 
                v-for="amount in paymentAmounts" 
                :key="amount"
                class="amount-btn"
                :class="{ active: selectedAmount === amount }"
                @click="selectedAmount = amount"
              >
                ¥{{ amount.toFixed(2) }}
              </button>
            </div>
          </div>
          <div class="custom-amount">
            <label>自定义额度</label>
            <input 
              v-model="customAmountDisplay" 
              type="text" 
              placeholder="输入赞助额度(9.90~99.00),每天限赞助2次"
              class="amount-input"
              @input="handleCustomAmountInput"
              @blur="formatCustomAmountOnBlur"
            />
          </div>
          <div class="amount-display">
            <span>应付额度：¥{{ finalAmount.toFixed(2) }}</span>
          </div>
          
          <!-- 二维码显示区域 -->
          <div v-if="qrcodeUrl" class="qrcode-container">
            <h4>请使用微信扫码支付</h4>
            <div class="qrcode-wrapper">
              <canvas ref="qrcodeCanvas" class="qrcode-canvas"></canvas>
            </div>
            <p class="order-info">订单号：{{ currentOrderNo }}</p>
            <p class="amount-info">额度：¥{{ currentPayAmount.toFixed(2) }} <span v-if="paymentSuccess" class="payment-success-text">支付完成，自动关闭</span></p>
            <p class="qr-tip">二维码有效期2小时，支付完成后自动关闭弹窗</p>
          </div>
          
          <button 
            v-if="!qrcodeUrl"
            class="pay-btn" 
            @click="initiateWechatPay"
            :disabled="paymentLoading || paymentSuccess || finalAmount <= 0"
          >
            {{ paymentSuccess ? '支付完成，正在关闭...' : (paymentLoading ? '正在支付...' : '微信支付') }}
          </button>
          <div v-if="paymentError" class="payment-error">{{ paymentError }}</div>
        </div>
      </div>
    </div>

    <!-- 提现窗体 -->
    <div v-if="isWithdrawModalVisible" class="withdraw-modal-overlay" @click.self="closeWithdrawModal">
      <div class="withdraw-modal-content">
        <div class="withdraw-modal-header">
          <h3>申请提现</h3>
          <button class="withdraw-modal-close-btn" @click="closeWithdrawModal">×</button>
        </div>
        <div class="withdraw-modal-body">
          <div class="withdraw-amount-group">
            <label for="withdrawRealNameInput">真实姓名</label>
            <input 
              id="withdrawRealNameInput"
              v-model="withdrawRealName" 
              type="text" 
              placeholder="输入真实姓名（中文4字/英文10字）"
              class="withdraw-amount-input"
              @input="handleRealNameInput"
            />
          </div>
          <div class="withdraw-amount-group">
            <label for="withdrawAmountInput">提现额度</label>
            <input 
              id="withdrawAmountInput"
              v-model="withdrawAmount" 
              type="text" 
              placeholder="输入提现额(9.90~99.00),每天限提现1次"
              class="withdraw-amount-input"
              @input="handleWithdrawAmountInput"
            />
          </div>
          <div class="withdraw-tip">
            <span>注:提现额需扣除 <b>1%</b> 手续费,例如:提现100,实际到账99元。</span>
          </div>
          <div v-if="withdrawError" class="withdraw-error">{{ withdrawError }}</div>
          <div class="withdraw-button-group">
            <button class="withdraw-btn primary" @click="handleWithdrawSubmit" :disabled="withdrawLoading">
              {{ withdrawLoading ? '提现中...' : '提现' }}
            </button>
            <button class="withdraw-btn" @click="closeWithdrawModal" :disabled="withdrawLoading">关闭</button>
          </div>
        </div>
      </div>
    </div>

    <BottomNav active="mine" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { getMyInfo, generateInviteCode, updateAvatar } from '@/api/auth'
import ChangePassword from './ChangePassword.vue'
import BottomNav from '@/components/BottomNav.vue'
import defaultAvatar from '@/assets/image/avatar/default_avatar.png'
import QRCode from 'qrcode'
import { marked } from 'marked'
import html2canvas from 'html2canvas'

import inviteMdContent from '@/assets/file/invite.md?raw'
import miniWebchatImg from '@/assets/image/mini_webchat.jpg'
import siteQrcodeImg from '@/assets/image/site_qrcode.jpg'

// 声明微信JS-SDK全局对象
declare const wx: any
declare const WeixinJSBridge: any

const router = useRouter()
const { logout, isLoggedIn } = useAuth()
const isChangePasswordVisible = ref(false)
const isInviteVisible = ref(false)
const inviteLink = ref('')
const inviteCode = ref('')
const inviteLoading = ref(false)
const inviteError = ref('')
const invitedCount = ref(0)
const increaseCostTotal = ref(0)

// 宣传册预览状态
const isBrochurePreviewVisible = ref(false)
const brochureImageUrl = ref('')

// 微信 JS-SDK 配置状态
const wxConfigReady = ref(false)

const isAvatarModalVisible = ref(false)
const avatarFileInput = ref<HTMLInputElement | null>(null)
const avatarCanvas = ref<HTMLCanvasElement | null>(null)
const inviteQrcodeCanvas = ref<HTMLCanvasElement | null>(null)
const previewAvatar = ref('')
const avatarZoom = ref(1)
const avatarSaving = ref(false)
const avatarError = ref('')

// 微信配置缓存
let wechatAppId = ''

// 判断是否在微信浏览器中
const isWeChatBrowser = () => {
  const ua = navigator.userAgent.toLowerCase()
  return ua.includes('micromessenger')
}

// 小程序环境标记
// const isMiniProgram = ref(false)
// let miniPayAckTimer: ReturnType<typeof setTimeout> | null = null
// let miniPayAcked = false


// 初始化小程序 WebView 通信

// 获取微信配置
interface WeChatConfig {
  appid: string
  redirect_uri: string
  component_appid?: string
  mch_id?: string
}

let wechatConfig: WeChatConfig | null = null

const fetchWeChatConfig = async (): Promise<WeChatConfig> => {
  if (wechatConfig) {
    return wechatConfig
  }
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/wechat_config', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data.code === 200 && data.data && data.data.appid) {
        wechatConfig = {
          appid: data.data.appid,
          redirect_uri: data.data.redirect_uri,
          component_appid: data.data.component_appid,
          mch_id: data.data.mch_id
        }
        wechatAppId = data.data.appid  // 保持兼容性
        return wechatConfig
      }
    }
  } catch (err) {
    console.error('获取微信配置失败:', err)
  }
  
  throw new Error('无法获取微信配置')
}

const myInfo = ref({
  user_account: '',
  account_credit: 0,
  create_time: '',
  last_login_time: '',
  status: '',
  mobile: '',
  email: '',
  avatar: '',
  medical_count: 0,
  cost_sum: 0,
  cash: 0
})

// 初始化微信 JS-SDK
const initWxConfig = async () => {
  if (!isWeChatBrowser()) {
    return false
  }

  try {
    const token = localStorage.getItem('token')
    const currentUrl = window.location.href.split('#')[0] // 获取当前页面URL（不含hash）
        
    // 调用后端接口获取签名
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/wechat_js_signature', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ url: currentUrl })
    })

    if (!response.ok) {
      throw new Error('获取微信签名失败')
    }

    const result = await response.json()

    if (result.code !== 200 || !result.data) {
      throw new Error(result.message || '签名配置获取失败')
    }

    const { appId, timestamp, nonceStr, signature } = result.data

    // 配置微信 JS-SDK
    await new Promise<void>((resolve, reject) => {
      wx.config({
        debug: false, // 生产环境设为 false
        appId: appId,
        timestamp: timestamp,
        nonceStr: nonceStr,
        signature: signature,
        jsApiList: [
          'chooseWXPay' // 微信支付接口
        ]
      })

      wx.ready(() => {
        wxConfigReady.value = true
        resolve()
      })

      wx.error((err: any) => {
        wxConfigReady.value = false
        reject(err)
      })
    })

    return true
  } catch (err) {
    console.error('初始化微信 JS-SDK 失败:', err)
    wxConfigReady.value = false
    return false
  }
}

onMounted(async () => {
  // 只要 token 存在就获取用户信息，不依赖 isLoggedIn 状态
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const result = await getMyInfo()
      if (result.code === 200 && result.data) {
        myInfo.value = result.data
        // 缓存用户头像供其他页面使用
        localStorage.setItem('user_avatar', result.data.avatar || '')
      } else {
        // Token无效，跳转到登录页
        localStorage.removeItem('token')
        router.push('/login')
        return
      }
    } catch (err) {
      // 后台接口无法访问，跳转到登录页
      router.push('/login')
      return
    }
  } else {
    // 没有 token，跳转到登录页
    router.push('/login')
    return
  }
  
  // 如果在微信浏览器中，且有 code 参数，自动打开支付弹窗
  const urlParams = new URLSearchParams(window.location.search)
  const code = urlParams.get('code')
  const savedAmount = sessionStorage.getItem('pending_pay_amount')
  const isProcessing = sessionStorage.getItem('is_processing_payment')
  
  if (isWeChatBrowser() && code && savedAmount && isProcessing === 'true') {
    console.log('[支付流程] 检测到OAuth授权返回，code:', code.substring(0, 10) + '...', '额度:', savedAmount)
    
    // 清除处理标志，防止刷新页面时重复处理
    sessionStorage.removeItem('is_processing_payment')
    
    try {
      // 先初始化微信JS-SDK
      console.log('[支付流程] 开始初始化微信JS-SDK')
      const initSuccess = await initWxConfig()
      
      if (!initSuccess) {
        console.error('[支付流程] 微信JS-SDK初始化失败')
        // 清除保存的金额，避免重复处理
        sessionStorage.removeItem('pending_pay_amount')
        alert('微信支付初始化失败，请重试')
        return
      }
      
      console.log('[支付流程] 微信JS-SDK初始化成功，wxConfigReady:', wxConfigReady.value)
      
      // 确保弹窗状态是关闭的，避免重复打开
      isPaymentModalVisible.value = false
      await nextTick()
      
      // 打开支付弹窗
      openPaymentModal()
      console.log('[支付流程] 支付弹窗已打开，isPaymentModalVisible:', isPaymentModalVisible.value)
      
      // 等待DOM渲染完成
      await nextTick()
      
      // 设置loading状态，表示正在处理支付
      paymentLoading.value = true
      console.log('[支付流程] 已设置paymentLoading为true')
      
      // 延迟触发支付，确保弹窗已完全渲染
      setTimeout(async () => {
        console.log('[支付流程] 开始自动触发支付，paymentLoading:', paymentLoading.value)
        try {
          await initiateWechatJSAPIPay()
          console.log('[支付流程] 自动触发支付完成')
        } catch (err) {
          console.error('[支付流程] 自动触发支付失败:', err)
          paymentError.value = '支付初始化失败: ' + (err instanceof Error ? err.message : '未知错误')
          paymentLoading.value = false
          alert('支付失败: ' + paymentError.value)
        }
      }, 1000) // 增加延迟到1秒，确保所有组件就绪
    } catch (err) {
      console.error('[支付流程] 处理OAuth回调异常:', err)
      sessionStorage.removeItem('pending_pay_amount')
      alert('支付处理异常: ' + (err instanceof Error ? err.message : '未知错误'))
    }
  }

  const withdrawPendingRaw = sessionStorage.getItem('pending_withdraw')
  const isProcessingWithdraw = sessionStorage.getItem('is_processing_withdraw')

  if (isWeChatBrowser() && code && withdrawPendingRaw && isProcessingWithdraw === 'true') {
    sessionStorage.removeItem('is_processing_withdraw')

    try {
      const pending = JSON.parse(withdrawPendingRaw) as { realName: string; amount: number }
      isWithdrawModalVisible.value = true
      withdrawLoading.value = true
      withdrawRealName.value = pending.realName
      withdrawAmount.value = pending.amount.toFixed(2)
      await submitWithdrawDirect(pending.realName, pending.amount)
    } catch (err) {
      sessionStorage.removeItem('pending_withdraw')
      withdrawLoading.value = false
      alert('提现处理异常: ' + (err instanceof Error ? err.message : '未知错误'))
    }
  }

  const withdrawStatus = urlParams.get('withdrawStatus')
  const outBillNo = urlParams.get('outBillNo')
  const withdrawErrMsg = urlParams.get('errMsg')

  if (withdrawStatus || outBillNo || withdrawErrMsg) {
    withdrawLoading.value = false
    if (withdrawStatus === 'fail') {
      const errMsg = withdrawErrMsg ? decodeURIComponent(withdrawErrMsg) : '提现失败'
      withdrawError.value = errMsg
      alert(errMsg)
    } else if (outBillNo) {
      isWithdrawModalVisible.value = true
      withdrawLoading.value = true
      startWithdrawQuery(outBillNo)
    }

    const cleanUrl = new URL(window.location.href)
    cleanUrl.searchParams.delete('withdrawStatus')
    cleanUrl.searchParams.delete('outBillNo')
    cleanUrl.searchParams.delete('errMsg')
    window.history.replaceState({}, document.title, cleanUrl.pathname + cleanUrl.search)
  }
})

const renderAvatarCanvas = () => {
  if (!isAvatarModalVisible.value || !avatarCanvas.value || !previewAvatar.value) return
  const ctx = avatarCanvas.value.getContext('2d')
  if (!ctx) return

  const img = new Image()
  img.onload = () => {
    ctx.clearRect(0, 0, 144, 144)
    const { width, height } = img
    const side = Math.min(width, height)
    const sourceSide = side / avatarZoom.value
    const sx = Math.max(0, (width - sourceSide) / 2)
    const sy = Math.max(0, (height - sourceSide) / 2)
    ctx.drawImage(img, sx, sy, sourceSide, sourceSide, 0, 0, 144, 144)
  }
  img.src = previewAvatar.value
}

const buildAvatarDataUrl = () => {
  return new Promise<string>((resolve, reject) => {
    if (!previewAvatar.value) {
      reject(new Error('no image'))
      return
    }
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = 144
      canvas.height = 144
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('canvas context'))
        return
      }
      const { width, height } = img
      const side = Math.min(width, height)
      const sourceSide = side / avatarZoom.value
      const sx = Math.max(0, (width - sourceSide) / 2)
      const sy = Math.max(0, (height - sourceSide) / 2)
      ctx.drawImage(img, sx, sy, sourceSide, sourceSide, 0, 0, 144, 144)
      resolve(canvas.toDataURL('image/png'))
    }
    img.onerror = reject
    img.src = previewAvatar.value
  })
}

const openAvatarModal = async () => {
  if (!isLoggedIn.value) {
    alert('请先登录')
    return
  }
  avatarError.value = ''
  avatarZoom.value = 1
  previewAvatar.value = myInfo.value.avatar ? `data:image/png;base64,${myInfo.value.avatar}` : defaultAvatar
  isAvatarModalVisible.value = true
  await nextTick()
  renderAvatarCanvas()
}

const closeAvatarModal = () => {
  isAvatarModalVisible.value = false
  avatarSaving.value = false
  avatarError.value = ''
}

const triggerSelectAvatar = () => {
  avatarFileInput.value?.click()
}

const handleAvatarFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // 限制头像文件大小为128KB
  const maxSize = 128 * 1024 // 128KB
  if (file.size > maxSize) {
    avatarError.value = '头像图片不能超过128KB，请选择更小的图片。'
    target.value = ''
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    previewAvatar.value = reader.result as string
    avatarZoom.value = 1
    nextTick(renderAvatarCanvas)
  }
  reader.readAsDataURL(file)
  target.value = ''
}

const submitAvatar = async () => {
  if (!previewAvatar.value) {
    avatarError.value = '请先选择图片'
    return
  }
  avatarSaving.value = true
  avatarError.value = ''
  try {
    const dataUrl = await buildAvatarDataUrl()
    const res = await updateAvatar({ image_data: dataUrl })
    if (res.code === 200 && res.data) {
      myInfo.value.avatar = res.data.avatar
      // 存储新头像到 localStorage，便于其他页面读取
      if (res.data.avatar) {
        localStorage.setItem('user_avatar', res.data.avatar)
      }
      isAvatarModalVisible.value = false
    } else {
      avatarError.value = res.message || '头像更新失败'
    }
  } catch (err) {
    avatarError.value = '头像更新失败，请重试'
  } finally {
    avatarSaving.value = false
  }
}

watch(previewAvatar, () => {
  if (isAvatarModalVisible.value) {
    nextTick(renderAvatarCanvas)
  }
})

watch(avatarZoom, () => {
  if (isAvatarModalVisible.value) {
    renderAvatarCanvas()
  }
})

const showChangePassword = () => {
  isChangePasswordVisible.value = true
}

const hideChangePassword = () => {
  isChangePasswordVisible.value = false
}

// 提现相关状态
const isWithdrawModalVisible = ref(false)
const withdrawRealName = ref('')
const withdrawAmount = ref('')
const withdrawError = ref('')
const withdrawLoading = ref(false)
let withdrawQueryTimer: ReturnType<typeof setInterval> | null = null
let withdrawOutBillNo = ''


const handleWithdraw = () => {
  // 检测是否为手机端
  const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  if (!isMobileDevice) {
    alert('在手机端微信中进行提现操作，确保实时提现成功')
    return
  }
  
  //检测是否在微信浏览器中
  if (!isWeChatBrowser()) {
    alert('在微信浏览器中进行提现操作，确保实时提现成功')
    return
  }

  
  const cash = Number(myInfo.value.cash) || 0
  
  if (cash < 9.90) {
    alert('当前提成额不足,至少9.90才能提现')
    return
  }
  
  // 打开提现窗体
  withdrawRealName.value = ''
  withdrawAmount.value = ''
  withdrawError.value = ''
  withdrawLoading.value = false
  isWithdrawModalVisible.value = true
}

const closeWithdrawModal = () => {
  isWithdrawModalVisible.value = false
  withdrawRealName.value = ''
  withdrawAmount.value = ''
  withdrawError.value = ''
  withdrawLoading.value = false
}

const handleRealNameInput = (e: Event) => {
  const input = e.target as HTMLInputElement
  let value = input.value
  
  // 计算字符长度：中文算2个字符，英文/数字算1个字符
  let length = 0
  for (let i = 0; i < value.length; i++) {
    const char = value[i] || ''
    // 判断是否为中文字符（包括中文标点）
    if (/[\u4e00-\u9fa5]/.test(char as string)) {
      length += 2
    } else {
      length += 1
    }
  }
  
  // 如果超过10个字符长度（相当于4个中文或10个英文），则截断
  if (length > 10) {
    let newValue = ''
    let currentLength = 0
    for (let i = 0; i < value.length; i++) {
      const char = value[i]
      const charLength = /[\u4e00-\u9fa5]/.test(char as string) ? 2 : 1
      if (currentLength + charLength <= 10) {
        newValue += char
        currentLength += charLength
      } else {
        break
      }
    }
    withdrawRealName.value = newValue
    input.value = newValue
  } else {
    withdrawRealName.value = value
  }
}

const validateRealName = (name: string): boolean => {
  // 计算字符长度：中文算2个字符，英文/数字算1个字符
  let length = 0
  for (let i = 0; i < name.length; i++) {
    const char = name[i] || ''
    if (/[\u4e00-\u9fa5]/.test(char as string)) {
      length += 2
    } else {
      length += 1
    }
  }
  return length > 0 && length <= 10
}

const handleWithdrawAmountInput = (e: Event) => {
  const input = e.target as HTMLInputElement
  let value = input.value
  
  // 只允许数字和一个小数点
  value = value.replace(/[^\d.]/g, '')
  
  // 确保只有一个小数点
  const parts = value.split('.')
  if (parts.length > 2) {
    value = parts[0] + '.' + parts.slice(1).join('')
  }
  
  // 限制小数点后最多2位
  if (parts.length === 2 && parts[1] && parts[1].length > 2) {
    value = parts[0] + '.' + parts[1].substring(0, 2)
  }
  
  withdrawAmount.value = value
  input.value = value
}

const startWithdrawQuery = (outBillNo: string) => {
  // 清除旧的定时器
  if (withdrawQueryTimer) {
    clearInterval(withdrawQueryTimer)
  }

  withdrawOutBillNo = outBillNo
  let retryCount = 0
  const maxRetries = 60 // 最多轮询60次（2秒*60=2分钟）

  console.log('开始轮询提现状态，订单号：', outBillNo)

  withdrawQueryTimer = setInterval(async () => {
    retryCount++
    console.log(`轮询第 ${retryCount} 次，查询订单 ${outBillNo}`)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch(window.VITE_GLOB_API_URL + `/api/wechat_withdraw_query?out_bill_no=${outBillNo}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      const data = await response.json()

      console.log('查询提现状态返回:', data)

      if (data.success) {
        // 查询成功，停止定时器
        console.log('提现成功！停止轮询')
        if (withdrawQueryTimer) {
          clearInterval(withdrawQueryTimer)
          withdrawQueryTimer = null
        }
        sessionStorage.removeItem('pending_withdraw')
        withdrawLoading.value = false
        closeWithdrawModal()

        // 更新用户信息
        if (isLoggedIn.value) {
          const result = await getMyInfo()
          console.log('刷新后的用户信息:', result)
          if (result.code === 200 && result.data) {
            myInfo.value = result.data
          }
        }

        return
      } else {
        console.log(`状态未就绪，state: ${data.state}, is_notify: ${data.is_notify}`)
      }

      // 如果达到最大重试次数，停止轮询
      if (retryCount >= maxRetries) {
        if (withdrawQueryTimer) {
          clearInterval(withdrawQueryTimer)
          withdrawQueryTimer = null
        }
        withdrawLoading.value = false
        console.log('提现查询超时，已停止轮询')
      }
    } catch (err) {
      withdrawLoading.value = false
      console.error('查询提现状态失败:', err)
    }
  }, 2000) // 每2秒查询一次
}

const submitWithdrawDirect = async (realName: string, amount: number) => {
  let keepLoading = false
  withdrawLoading.value = true
  try {
    const code = getWeChatCode()

    if (!code) {
      const config = await fetchWeChatConfig()
      sessionStorage.setItem('pending_withdraw', JSON.stringify({ realName, amount }))
      sessionStorage.setItem('is_processing_withdraw', 'true')

      keepLoading = true
      isWithdrawModalVisible.value = true

      const authParams = new URLSearchParams({
        appid: config.appid,
        redirect_uri: config.redirect_uri,
        response_type: 'code',
        scope: 'snsapi_base',
        state: 'wechat_withdraw_' + Date.now()
      })

      window.location.href = `https://open.weixin.qq.com/connect/oauth2/authorize?${authParams.toString()}#wechat_redirect`
      return
    }

    clearWeChatCode()

    const token = localStorage.getItem('token')
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/wechat_withdraw', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        real_name: realName,
        amount: amount,
        code: code,
        pay_scene: 'h5'
      })
    })
    
    const data = await response.json()
    
    if (data.code === 200 || data.success) {
      // 提现成功，获取out_bill_no用于后续轮询查询
      const outBillNo = data.data?.out_bill_no
      
      // 提现成功，调用微信确认收款
      if (data.data && data.data.package_info && data.data.state === 'WAIT_USER_CONFIRM') {
        keepLoading = true
        try {
          const config = await fetchWeChatConfig()
          //const wx = (window as any).wx
          //const WeixinJSBridge = (window as any).WeixinJSBridge
          
          if (wx && WeixinJSBridge) {
            // 获取微信JS SDK权限
            const currentUrl = window.location.href.split('#')[0]
            const jsSDKTicketResponse = await fetch(window.VITE_GLOB_API_URL + '/api/wechat_js_signature', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                url: currentUrl
              })
            })
            const ticketData = await jsSDKTicketResponse.json()
            
            if (ticketData.code === 200 && ticketData.data) {
              // 配置微信JS SDK
              wx.config({
                debug: false,
                appId: ticketData.data.appId,
                timestamp: ticketData.data.timestamp,
                nonceStr: ticketData.data.nonceStr,
                signature: ticketData.data.signature,
                jsApiList: ['requestMerchantTransfer']
              })
              
              wx.ready(function () {
                wx.checkJsApi({
                  jsApiList: ['requestMerchantTransfer'],
                  success: function (res: any) {
                    if (res.checkResult['requestMerchantTransfer']) {
                      // 调用微信确认收款
                      WeixinJSBridge.invoke(
                        'requestMerchantTransfer',
                        {
                          mchId: config.mch_id || '',
                          appId: ticketData.data.appId,
                          package: data.data.package_info
                        },
                        async function (res: any) {
                          if (res.err_msg === 'requestMerchantTransfer:ok') {
                            console.log('确认收款成功:', res)
                            // 提现成功，启动定时器轮询查询状态
                            if (outBillNo) {
                              startWithdrawQuery(outBillNo)
                            }
                          } else {
                            console.error('确认收款失败:', res)
                            withdrawLoading.value = false
                            alert('确认收款失败: ' + (res.err_msg || '未知错误'))
                          }
                        }
                      )
                    } else {
                      withdrawLoading.value = false
                      alert('你的微信版本过低，请更新至最新版本')
                    }
                  }
                })
              })
            } else {
              withdrawLoading.value = false
              alert('获得用户微信授权失败，提现申请已提交,'+ticketData.message || '')
            }
          } else {
            withdrawLoading.value = false
            alert('获得微信实例失败')
          }
        } catch (err) {
          console.error('调用微信确认收款失败:', err)
          withdrawLoading.value = false
          alert('提现申请已提交'+(err instanceof Error ? '，错误信息：' + err.message : '收款确认失败'))
        }
      } else if (outBillNo) {
        keepLoading = true
        startWithdrawQuery(outBillNo)
      } else {
        withdrawLoading.value = false
      } 
    } else {
      withdrawError.value = '提现失败：' + (data.message || '未知错误')
    }
  
  } catch (err) {
    withdrawError.value = '提现失败: ' + (err instanceof Error ? err.message : '可能是服务器或是授权问题')
    console.error('提现错误:', err)
  } finally {
    if (!keepLoading) {
      withdrawLoading.value = false
    }
  }
}

const handleWithdrawSubmit = async () => {
  const realName = withdrawRealName.value.trim()
  const amount = Number(withdrawAmount.value) || 0
  
  if (!realName) {
    withdrawError.value = '请输入真实姓名'
    return
  }
  
  if (!validateRealName(realName)) {
    withdrawError.value = '真实姓名长度不符合要求（中文4字/英文10字）'
    return
  }
  
  if (amount < 9.90 || amount > 99.00) {
    withdrawError.value = '提现额度为9.90~99.00之间'
    return
  }
  
  withdrawLoading.value = true
  withdrawError.value = ''

  const canUseMiniProgram = !!(wx?.miniProgram?.getEnv)
  if (canUseMiniProgram) {
    wx.miniProgram.getEnv((res: any) => {
      if (res && res.miniprogram) {
        const params = new URLSearchParams({
          realName,
          amount: String(amount),
          token: localStorage.getItem('token') || '',
          apiBase: window.VITE_GLOB_API_URL
        })

        wx.miniProgram.navigateTo({
          url: `/pages/withdraw/index?${params.toString()}`,
          fail: () => {
            withdrawLoading.value = false
            withdrawError.value = '跳转提现页失败，请重试'
          }
        })
      } else {
        submitWithdrawDirect(realName, amount)
      }
    })
  }
  else {
    await submitWithdrawDirect(realName, amount)
  }
}

const handleSponsor = async () => {
  inviteError.value = ''
  inviteLink.value = ''
  inviteCode.value = ''
  isInviteVisible.value = true
  inviteLoading.value = true
  try {
    const res = await generateInviteCode()
    if (res.code === 200 && res.data) {
      inviteLink.value = res.data.invite_link
      inviteCode.value = res.data.invite_code
      invitedCount.value = res.data.invite_count ?? 0
      increaseCostTotal.value = res.data.increase_cost_total ?? 0
      // 邀请链接生成后，等待DOM更新，再生成二维码
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 200)) // 额外延迟确保canvas完全渲染
      generateInviteQRCode()
    } else {
      inviteError.value = res.message || '生成邀请码失败'
    }
  } catch (err) {
    inviteError.value = '生成邀请码失败，请稍后重试'
  } finally {
    inviteLoading.value = false
  }
}

const closeInvite = () => {
  isInviteVisible.value = false
}

const copyInviteLink = async () => {
  if (!inviteLink.value) return
  try {
    await navigator.clipboard.writeText(inviteLink.value)
    alert('已复制邀请链接')
  } catch (e) {
    const textarea = document.createElement('textarea')
    textarea.value = inviteLink.value
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    alert('已复制邀请链接')
  }
}

const generateInviteQRCode = async () => {
  // 重试逻辑，确保canvas已挂载
  let retries = 0
  const maxRetries = 5
  
  while (retries < maxRetries) {
    if (inviteLink.value && inviteQrcodeCanvas.value) {
      try {
        // 设置canvas宽高
        inviteQrcodeCanvas.value.width = 200
        inviteQrcodeCanvas.value.height = 200
        
        await QRCode.toCanvas(inviteQrcodeCanvas.value, inviteLink.value, {
          width: 200,
          margin: 1,
          color: {
            dark: '#000000',
            light: '#FFFFFF'
          }
        })
        console.log('邀请二维码生成成功')
        return
      } catch (err) {
        console.error('生成邀请二维码失败:', err)
        return
      }
    }
    
    // 等待DOM渲染
    await new Promise(resolve => setTimeout(resolve, 100))
    retries++
  }
  
  console.warn('邀请二维码生成失败：canvas未就绪，link:', !!inviteLink.value, 'canvas:', !!inviteQrcodeCanvas.value)
}

const downloadBrochure = async () => {
  try {
    // 1. 获取二维码的base64图片
    if (!inviteQrcodeCanvas.value) {
      alert('二维码未生成，请稍后重试')
      return
    }
    const qrCodeDataUrl = inviteQrcodeCanvas.value.toDataURL('image/png')

    // 2. 读取markdown模板内容并替换占位符
    let markdownContent = inviteMdContent
    markdownContent = markdownContent.replace('{user}', myInfo.value.user_account || '用户')
    // 三张图片排成一行，使用flex容器
      const imgRowHtml = `
      <div style=\"display: flex; justify-content: center; align-items: flex-end; gap: 24px; margin: 20px 0;\">
        <div style=\"display: flex; flex-direction: column; align-items: center;\">
          <div style=\"font-size: 20px; color: red; font-weight: bold; margin-bottom: -10px;\">微信扫一扫注册</div>
          <img src=\"${qrCodeDataUrl}\" style=\"width: 200px; height: 200px;\" />
        </div>
        <img src=\"${miniWebchatImg}\" style=\"width: 200px; height: 200px;\" />
        <img src=\"${siteQrcodeImg}\" style=\"width: 200px; height: 200px;\" />
      </div>
    `;
    markdownContent = markdownContent.replace('{qr_code_img}', imgRowHtml)
    markdownContent = markdownContent.replace('{mini_webchat.jpg}', '')
    markdownContent = markdownContent.replace('{site_qrcode.jpg}', '')

    // 3. 将markdown转换为HTML
    const htmlContent = await marked.parse(markdownContent)

    // 4. 创建临时容器用于渲染HTML
    const container = document.createElement('div')
    container.style.cssText = `
      position: fixed;
      left: -9999px;
      top: 0;
      width: 794px;
      padding: 40px;
      background: white;
      font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
      line-height: 1.8;
      color: #333;
    `

    container.innerHTML = `
      <style>
        h1 { font-size: 32px; color: #667eea; margin: 20px 0; text-align: center; }
        h3 { font-size: 24px; color: #764ba2; margin: 15px 0; text-align: center; }
        h4 { font-size: 20px; color: #4A90E2; margin: 15px 0; text-align: center; }
        p { font-size: 16px; margin: 10px 0; text-indent: 2em; }
        center { text-align: center; }
        img { display: block; margin: 20px auto; }
      </style>
      ${htmlContent}
    `

    document.body.appendChild(container)

    // 5. 使用html2canvas将HTML转换为canvas
    const canvas = await html2canvas(container, {
      scale: 2,
      backgroundColor: '#ffffff',
      logging: false,
      useCORS: true
    })

    // 6. 移除临时容器
    document.body.removeChild(container)

    // 7. 将canvas转换为DataURL
    const imageDataUrl = canvas.toDataURL('image/png')
    brochureImageUrl.value = imageDataUrl

    // 8. 判断设备类型
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)

    if (isMobile) {
      // 移动设备：显示预览弹窗，让用户长按保存
      isBrochurePreviewVisible.value = true
    } else {
      // PC端：直接下载
      directDownloadBrochure()
    }

  } catch (err) {
    console.error('生成宣传册失败:', err)
    alert('生成宣传册失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
}

// 关闭宣传册预览
const closeBrochurePreview = () => {
  isBrochurePreviewVisible.value = false
  brochureImageUrl.value = ''
}

// 直接下载宣传册图片
const directDownloadBrochure = () => {
  if (!brochureImageUrl.value) {
    alert('图片未生成，请重试')
    return
  }
  
  const fileName = `邀请朋友注册宣传册_${myInfo.value.user_account}_${Date.now()}.png`
  const link = document.createElement('a')
  link.href = brochureImageUrl.value
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  alert('宣传册已下载')
}

const handleLogout = async () => {
  if (confirm('确定要退出账户吗？')) {
    try {
      // 调用退出接口，清除前后端登录状态
      const result = await logout()
      
      // 无论接口是否成功，本地状态已清除，统一跳转到首页
      // 退出后跳转到首页（未登录状态）
      router.push('/')
    } catch (error) {
      console.error('退出失败:', error)
      // 即使发生异常，也跳转到首页
      router.push('/')
    }
  }
}

// 公用调试函数
const api_debug = async (message: string) => {
  try {
    const token = localStorage.getItem('token')
    const debugRes = await fetch(window.VITE_GLOB_API_URL + '/api/debug', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: message,
        timestamp: new Date().toISOString(),
        page: 'MyInfo'
      })
    })
    const debugData = await debugRes.json()
  } catch (debugErr) {
  }
}

// 支付相关状态
const isPaymentModalVisible = ref(false)
const paymentAmounts = [9.90, 29.70, 49.50, 99.00]
const selectedAmount = ref(9.90)
const customAmount = ref(0)
const customAmountDisplay = ref('')
const paymentLoading = ref(false)
const paymentError = ref('')
const qrcodeCanvas = ref<HTMLCanvasElement | null>(null)
const qrcodeUrl = ref('')
const currentOrderNo = ref('')
const currentPayAmount = ref(0)
const paymentSuccess = ref(false)
let paymentCheckTimer: ReturnType<typeof setInterval> | null = null

// 处理自定义金额输入
const handleCustomAmountInput = (event: Event) => {
  const input = event.target as HTMLInputElement
  let value = input.value
  
  // 只允许数字和一个小数点
  value = value.replace(/[^\d.]/g, '')
  
  // 只允许一个小数点
  const parts = value.split('.')
  if (parts.length > 2) {
    value = parts[0] + '.' + parts.slice(1).join('')
  }
  
  // 限制小数点后最多2位
  if (parts.length === 2 && parts[1] && parts[1].length > 2) {
    value = parts[0] + '.' + parts[1].substring(0, 2)
  }
  
  customAmountDisplay.value = value
  customAmount.value = value ? parseFloat(value) : 0
}

// 失去焦点时格式化显示
const formatCustomAmountOnBlur = () => {
  if (customAmount.value > 0) {
    customAmountDisplay.value = customAmount.value.toFixed(2)
  } else {
    customAmountDisplay.value = ''
  }
}

// 计算最终支付金额
const finalAmount = computed(() => {
  return customAmount.value > 0 ? customAmount.value : selectedAmount.value
})

// 打开支付弹窗
const openPaymentModal = () => {
  if (!isLoggedIn.value) {
    alert('请先登录')
    return
  }
  isPaymentModalVisible.value = true
  selectedAmount.value = 9.90
  customAmount.value = 0.00
  customAmountDisplay.value = ''
  paymentError.value = ''
}

// 关闭支付弹窗
const closePaymentModal = () => {
  // 清除定时器
  if (paymentCheckTimer) {
    clearInterval(paymentCheckTimer)
    paymentCheckTimer = null
  }
  
  isPaymentModalVisible.value = false
  paymentError.value = ''
  paymentLoading.value = false
  qrcodeUrl.value = ''
  currentOrderNo.value = ''
  currentPayAmount.value = 0
  paymentSuccess.value = false
  customAmountDisplay.value = ''
  
  // 注意：不在这里清除sessionStorage，因为跳转授权时需要保留
  // sessionStorage会在支付完成后或授权返回时清除
}

const handlePaymentSuccess = async () => {
  paymentSuccess.value = true
  paymentError.value = ''
  paymentLoading.value = false

  sessionStorage.removeItem('pending_pay_amount')
  sessionStorage.removeItem('is_processing_payment')
  sessionStorage.removeItem('pending_pay_order_no')

  setTimeout(async () => {
    closePaymentModal()
    if (isLoggedIn.value) {
      const result = await getMyInfo()
      if (result.code === 200 && result.data) {
        myInfo.value = result.data
      }
    }
  }, 2000)
}

const handlePaymentCancel = () => {
  paymentError.value = '支付已取消'
  paymentLoading.value = false

  sessionStorage.removeItem('pending_pay_amount')
  sessionStorage.removeItem('is_processing_payment')
  sessionStorage.removeItem('pending_pay_order_no')
}

const handlePaymentFail = (errMsg?: string) => {
  paymentError.value = '支付失败: ' + (errMsg || '未知错误')
  paymentLoading.value = false

  sessionStorage.removeItem('pending_pay_amount')
  sessionStorage.removeItem('is_processing_payment')
  sessionStorage.removeItem('pending_pay_order_no')
}

// 从URL中获取微信OAuth code
const getWeChatCode = (): string | null => {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('code')
}

// 清除URL中的code参数（防止重复使用）
const clearWeChatCode = () => {
  const url = new URL(window.location.href)
  url.searchParams.delete('code')
  url.searchParams.delete('state')
  window.history.replaceState({}, document.title, url.pathname + url.search)
}

// 查询订单状态
const queryOrderStatus = async (out_trade_no: string) => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(window.VITE_GLOB_API_URL + `/api/wechat_pay_query?out_trade_no=${encodeURIComponent(out_trade_no)}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()    
      // 检查业务数据中的 trade_state
      if (data.trade_state === 'SUCCESS') {
        return true
      }
    }
    return false
  } catch (err) {
    console.error('查询订单状态失败:', err)
    return false
  }
}

// 启动支付状态检查定时器
const startPaymentCheck = (order_no: string) => {
  // 清除之前的定时器（如果有）
  if (paymentCheckTimer) {
    clearInterval(paymentCheckTimer)
  }
  
  // 每2秒检查一次订单状态
  paymentCheckTimer = setInterval(async () => {
    const isSuccess = await queryOrderStatus(order_no)
    
    if (isSuccess) {
      paymentSuccess.value = true
      
      // 清除定时器
      if (paymentCheckTimer) {
        clearInterval(paymentCheckTimer)
        paymentCheckTimer = null
      }
      
      // 延迟2秒后关闭弹窗并刷新用户信息
      setTimeout(async () => {
        closePaymentModal()
        
        // 刷新用户信息
        if (isLoggedIn.value) {
          const result = await getMyInfo()
          if (result.code === 200 && result.data) {
            myInfo.value = result.data
          }
        }
      }, 2000)
    }
  }, 2000)
}

// 生成并显示二维码
const showQRCode = async (code_url: string, order_no: string, amount: number) => {
  qrcodeUrl.value = code_url
  currentOrderNo.value = order_no
  currentPayAmount.value = Number(amount) || 0
  paymentSuccess.value = false
  
  await nextTick()
  
  if (qrcodeCanvas.value) {
    try {
      await QRCode.toCanvas(qrcodeCanvas.value, code_url, {
        width: 200,
        margin: 1,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      })
      
      // 启动支付状态检查
      startPaymentCheck(order_no)
    } catch (err) {
      paymentError.value = '生成二维码失败，请重试'
    }
  }
}

// JSAPI支付 - 使用微信 JS-SDK
const initiateWechatJSAPIPay = async () => {
  try {
    const token = localStorage.getItem('token')
    
    console.log('[JSAPI支付] 开始支付流程')
    
    // 第一步：初始化微信 JS-SDK（如果还未初始化）
    if (!wxConfigReady.value) {
      console.log('[JSAPI支付] 微信JS-SDK未就绪，开始初始化')
      const initSuccess = await initWxConfig()

      if (!initSuccess) {
        throw new Error('微信 JS-SDK 初始化失败')
      }
      console.log('[JSAPI支付] 微信JS-SDK初始化完成')
    } else {
      console.log('[JSAPI支付] 微信JS-SDK已就绪')
    }

    // 第二步：检查是否有 OAuth code
    const urlParams = new URLSearchParams(window.location.search)
    let code = urlParams.get('code')
    // 获取微信配置
    const config = await fetchWeChatConfig()
    
    if (!code) {
      console.log('[JSAPI支付] 未找到OAuth code，需要进行授权')
      
      // 保存支付金额到 sessionStorage，授权后恢复
      const amountToSave = finalAmount.value.toString()
      sessionStorage.setItem('pending_pay_amount', amountToSave)
      // 设置支付处理标志，防止重复打开弹窗
      sessionStorage.setItem('is_processing_payment', 'true')
      
      console.log('[JSAPI支付] 已保存支付额度:', amountToSave, '到sessionStorage')
      console.log('[JSAPI支付] 验证sessionStorage:', sessionStorage.getItem('pending_pay_amount'))
      
      // 跳转前只关闭弹窗，不清除sessionStorage（closePaymentModal会清除）
      isPaymentModalVisible.value = false
      paymentLoading.value = false
      
      console.log('[JSAPI支付] 已关闭支付弹窗，准备跳转授权')
      
      // 等待弹窗完全关闭后再跳转
      await nextTick()
      
      // 构建授权URL（无需 component_appid）
      const redirectUri = config.redirect_uri
      const state = 'jsapi_pay_' + Date.now()
      
      const authParams = new URLSearchParams({
        appid: config.appid,
        redirect_uri: redirectUri,
        response_type: 'code',
        scope: 'snsapi_base',
        state: state
      })
      
      const authUrl = `https://open.weixin.qq.com/connect/oauth2/authorize?${authParams.toString()}#wechat_redirect`
      
      console.log('[JSAPI支付] 即将跳转到微信授权页面，URL:', authUrl.substring(0, 100) + '...')
      
      // 延迟跳转，确保所有状态都已更新
      setTimeout(() => {
        console.log('[JSAPI支付] 正在执行跳转...')
        window.location.href = authUrl
      }, 100)
      return // 跳转后函数停止执行
    }
    
    console.log('[JSAPI支付] 已获得OAuth code，继续支付流程')
    
    // 清除URL中的code参数
    const newUrl = window.location.pathname + window.location.hash
    window.history.replaceState({}, document.title, newUrl)
    console.log('[JSAPI支付] 已清除URL中的code参数')
    
    // 从 sessionStorage 恢复支付金额（如果有）
    const savedAmount = sessionStorage.getItem('pending_pay_amount')
    console.log('[JSAPI支付] 尝试从sessionStorage恢复金额:', savedAmount)
    
    if (savedAmount) {
      const amount = parseFloat(savedAmount)
      if (amount > 0) {
        customAmount.value = 0
        selectedAmount.value = amount
        console.log('[JSAPI支付] 已恢复支付金额:', amount, 'selectedAmount:', selectedAmount.value, 'finalAmount:', finalAmount.value)
      }
      // 注意：这里不删除pending_pay_amount，等支付成功或失败后再删除
    } else {
      console.warn('[JSAPI支付] sessionStorage中没有找到保存的金额')
    }

    // 第三步：调用后端创建JSAPI支付订单
    console.log('[JSAPI支付] 开始创建支付订单')
    const orderRes = await fetch(window.VITE_GLOB_API_URL + '/api/wechat_jsapi_pay', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        pay_amount: finalAmount.value,
        code: code,
        pay_scene: 'h5'
      })
    })

    const orderData = await orderRes.json()
    
    if (!orderRes.ok) {
      throw new Error('创建支付订单失败,'+orderData.error || orderData.message )
    }

    if (!orderData.success || !orderData.result) {
      throw new Error('创建支付订单失败,'+orderData.error || orderData.message )
    }
    
    console.log('[JSAPI支付] 支付订单创建成功')
    
    // 第四步：确认微信 JS-SDK 已准备好
    // 检查 wx 对象是否存在
    if (typeof wx === 'undefined') {
      throw new Error('微信 JS-SDK 未加载，请在微信中打开')
    }
    
    // 如果 JS-SDK 还未准备好，等待一段时间
    if (!wxConfigReady.value) {
      console.log('[JSAPI支付] 微信JS-SDK未就绪，等待1秒')
      await new Promise((resolve) => setTimeout(resolve, 1000))
      
      if (!wxConfigReady.value) {
        throw new Error('微信 JS-SDK 未就绪，请重试')
      }
    }
    
    const paymentParams = orderData.result
    
    console.log('[JSAPI支付] 开始调起微信支付，参数:', {
      timestamp: paymentParams.timeStamp,
      nonceStr: paymentParams.nonceStr?.substring(0, 10) + '...',
      package: paymentParams.package?.substring(0, 30) + '...',
      signType: paymentParams.signType,
      paySign: paymentParams.paySign?.substring(0, 20) + '...'
    })
    
    // 重置loading状态，准备调起支付
    paymentLoading.value = false
    
    wx.chooseWXPay({
      timestamp: paymentParams.timeStamp,
      nonceStr: paymentParams.nonceStr,
      package: paymentParams.package,
      signType: paymentParams.signType,
      paySign: paymentParams.paySign,
      success: async (res: any) => {
        console.log('[JSAPI支付] 支付成功，响应:', res)
        paymentSuccess.value = true
        paymentError.value = ''
        paymentLoading.value = false
        
        // 清除支付相关的sessionStorage
        sessionStorage.removeItem('pending_pay_amount')
        sessionStorage.removeItem('is_processing_payment')
        
        // 延迟关闭弹窗并刷新用户信息
        setTimeout(async () => {
          closePaymentModal()
          if (isLoggedIn.value) {
            const result = await getMyInfo()
            if (result.code === 200 && result.data) {
              myInfo.value = result.data
            }
          }
        }, 2000)
      },
      cancel: (res: any) => {
        console.log('[JSAPI支付] 用户取消支付，响应:', res)
        paymentError.value = '支付已取消'
        paymentLoading.value = false
        
        // 清除支付相关的sessionStorage
        sessionStorage.removeItem('pending_pay_amount')
        sessionStorage.removeItem('is_processing_payment')
      },
      fail: (res: any) => {
        console.error('[JSAPI支付] 支付失败，响应:', res)
        paymentError.value = '支付失败: ' + (res.errMsg || '未知错误')
        paymentLoading.value = false
        
        // 清除支付相关的sessionStorage
        sessionStorage.removeItem('pending_pay_amount')
        sessionStorage.removeItem('is_processing_payment')
      }
    })
  } catch (err) {
    console.error('[JSAPI支付] 发生错误:', err)
    paymentLoading.value = false
    const errorMsg = err instanceof Error ? err.message : 'JSAPI支付失败，请稍后重试'
    paymentError.value = errorMsg
    console.error('[JSAPI支付] 错误详情:', err)
    
    // 清除支付相关的sessionStorage
    sessionStorage.removeItem('pending_pay_amount')
    sessionStorage.removeItem('is_processing_payment')
    
    // 显示错误提示
    alert('支付失败: ' + errorMsg)
  }
}

// NATIVE支付 - 显示二维码
const initiateWechatNativePay = async () => {
  try {
    const token = localStorage.getItem('token')
    
    const orderRes = await fetch(window.VITE_GLOB_API_URL + '/api/wechat_native_pay', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        pay_amount: finalAmount.value
      })
    })
    
    const orderData = await orderRes.json()
    if (!orderRes.ok) {
      throw new Error('创建支付订单失败,'+orderData.error || orderData.message)
    }

    if (!orderData.success || !orderData.code_url) {
      throw new Error('创建支付订单失败,'+orderData.error || orderData.message)
    }

    const { code_url, out_trade_no, pay_amount } = orderData

    paymentLoading.value = false
    
    // 生成并显示二维码
    await showQRCode(code_url, out_trade_no, pay_amount)

  } catch (err) {
    paymentLoading.value = false
    paymentError.value = err instanceof Error ? err.message : 'NATIVE支付失败，请稍后重试'
    console.error('NATIVE支付错误:', err)
  }
}

// 发起微信支付 - 根据环境选择支付方式
const initiateWechatPay = async () => {

  if (finalAmount.value < 9.90 || finalAmount.value > 99.0) {
    paymentError.value = '请输入有效的支付额度为：9.90~99.00';
    return;
  }

  console.log('[发起支付] 开始支付流程，额度:', finalAmount.value, '是否微信浏览器:', isWeChatBrowser())
  
  paymentLoading.value = true
  paymentError.value = ''

  try {
    // 判断是否为微信小程序环境
    const canUseMiniProgram = !!(wx?.miniProgram?.getEnv)
    if (canUseMiniProgram) {
      const isMiniEnv = await new Promise((resolve) => {
        wx.miniProgram.getEnv((res: any) => {
          resolve(!!(res && res.miniprogram))
        })
      })
      if (isMiniEnv) {
        // 小程序WebView内，跳转到小程序原生支付页
        try {
          const token = localStorage.getItem('token') || ''
          const amount = finalAmount.value
          const params = new URLSearchParams({
            amount: String(amount),
            token,
            apiBase: window.VITE_GLOB_API_URL
          })

          wx.miniProgram.navigateTo({
            url: `/pages/pay/index?${params.toString()}`,
            fail: () => {
              paymentLoading.value = false
              paymentError.value = '跳转小程序支付页失败，请重试'
              alert(paymentError.value)
            }
          })
        } catch (err) {
          paymentLoading.value = false
          paymentError.value = err instanceof Error ? err.message : '小程序支付跳转失败'
          alert('支付错误: ' + paymentError.value)
        }
        return
      }
    }
    // 非小程序：判断是否在微信浏览器中
    if (isWeChatBrowser()) {
      console.log('[发起支付] 调用JSAPI支付方式')
      await initiateWechatJSAPIPay()
    } else {
      console.log('[发起支付] 调用NATIVE支付方式')
      await initiateWechatNativePay()
    }
    console.log('[发起支付] 支付流程执行完成')
  } catch (err) {
    console.error('[发起支付] 支付流程异常:', err)
    paymentLoading.value = false
    paymentError.value = err instanceof Error ? err.message : '支付失败，请稍后重试'
    alert('支付错误: ' + paymentError.value)
  }
}
</script>

<style scoped>
.my-info-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 134px;
  background-color: #f5f5f5;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 14px;
  color: #333;
}

.title {
  font-size: 16px;
  font-weight: bold;
  text-align: center;
  width: 100%;
  max-width: 360px;
  box-sizing: border-box;
  margin: 0 auto 16px auto;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #667eea 100%);
  color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  letter-spacing: 1px;
}

.card {
  width: 100%;
  max-width: 360px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 16px 16px 12px;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.basic-info {
  flex: 1;
}

.name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 5px;
}

.status-line {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.balance-row {
  display: flex;
  align-items: center;
  gap: 2px;
  padding-left: 20px;
  white-space: nowrap;
}

.label {
  color: #666;
  margin-right: -15px;
}

.balance {
  color: #333;
  display: inline-block;
  width: 60px;
  min-width: 60px;
  text-align: right;
}

.charge-btn {
  height: 28px;
  padding: 0 7px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #4A90E2;
  background-color: #4A90E2;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.charge-btn:hover {
  background-color: #357ABD;
  border-color: #357ABD;
}

.info-row {
  display: flex;
  margin-top: 4px;
}

.field-label {
  width: 52px;
  color: #666;
}

.field-value {
  flex: 1;
  color: #333;
}

.action-buttons {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 8px;
}

.action-btn {
  min-width: 110px;
  padding: 10px 18px;
  border-radius: 4px;
  border: none;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.action-btn.primary {
  background-color: #4A90E2;
  color: #fff;
}

.action-btn.primary:hover {
  background-color: #357ABD;
}

.action-btn.danger {
  background-color: #ffffff;
  color: #4A90E2;
  border: 1px solid #4A90E2;
}

.action-btn.danger:hover {
  background-color: #f0f6ff;
}

.invite-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.invite-panel {
  width: 90%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  padding: 20px;
  box-sizing: border-box;
}

.invite-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.invite-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.invite-close {
  background: none;
  border: none;
  font-size: 22px;
  color: #666;
  cursor: pointer;
  line-height: 1;
}

.invite-close:hover {
  color: #4A90E2;
}

.invite-subtitle {
  margin: 0 0 12px 0;
  color: #666;
  font-size: 14px;
}

.invite-link {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.invite-link input,
.invite-link textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
  background: #f9fafb;
  min-height: 68px;
  resize: vertical;
}

.invite-link button {
  padding: 10px 14px;
  background-color: #4A90E2;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  min-width: 80px;
}

.invite-link button:disabled {
  background-color: #a5c5f5;
  cursor: not-allowed;
}

.invite-hint {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.invite-error {
  font-size: 13px;
  color: #e74c3c;
  margin-bottom: 6px;
}

.stats {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  color: #333;
  justify-content: space-between;
  font-size: 14px;
}

.stat-item {
  display: flex;
  gap: 2px;
  white-space: nowrap;
  flex-shrink: 1;
  min-width: 0;
}

.stats span {
  color: #4A90E2;
  font-weight: 600;
}

/* 手机端优化 */
@media (max-width: 420px) {
  .stats {
    gap: 6px;
    font-size: 12px;
  }
  
  .stat-item {
    gap: 1px;
  }
}

.qrcode-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.qrcode-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.qrcode-display {
  padding: 10px;
  background-color: #fff;
  border-radius: 8px;
  border: 1px solid #ddd;
  margin-bottom: 12px;
}

.invite-qrcode {
  display: block;
  width: 200px;
  height: 200px;
}

.download-btn {
  width: 100%;
  padding: 10px 16px;
  background-color: #4A90E2;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.download-btn:hover {
  background-color: #357ABD;
}

.download-btn:active {
  transform: scale(0.98);
}

/* 宣传册预览弹窗样式 */
.brochure-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1300;
  padding: 20px;
  box-sizing: border-box;
}

.brochure-preview-panel {
  width: 100%;
  max-width: 850px;
  max-height: 95vh;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.brochure-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background-color: #f9fafb;
}

.brochure-preview-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.brochure-preview-close {
  background: none;
  border: none;
  font-size: 28px;
  color: #666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s;
}

.brochure-preview-close:hover {
  background-color: #f0f0f0;
  color: #333;
}

.brochure-preview-tip {
  margin: 0;
  padding: 12px 20px;
  background-color: #fff3cd;
  border-bottom: 1px solid #ffeaa7;
  color: #856404;
  font-size: 14px;
  text-align: center;
  line-height: 1.6;
}

.brochure-preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brochure-preview-image {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: white;
}

.brochure-preview-actions {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  background-color: #f9fafb;
}

.brochure-download-btn {
  width: 100%;
  padding: 12px 20px;
  background-color: #4A90E2;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.brochure-download-btn:hover {
  background-color: #357ABD;
}

.brochure-download-btn:active {
  transform: scale(0.98);
}

.hidden-file-input {
  display: none;
}

.avatar-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
}

.avatar-panel {
  width: 92%;
  max-width: 520px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
  padding: 18px 18px 16px;
  box-sizing: border-box;
}

.avatar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.avatar-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.avatar-close {
  background: none;
  border: none;
  font-size: 22px;
  color: #666;
  cursor: pointer;
  line-height: 1;
}

.avatar-subtitle {
  margin: 0 0 12px 0;
  color: #666;
  font-size: 13px;
}

.avatar-preview-box {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.avatar-preview-frame {
  flex: 1;
  min-width: 180px;
  max-width: 260px;
  aspect-ratio: 1 / 1;
  border: 1px dashed #d0d7e2;
  border-radius: 10px;
  overflow: hidden;
  background: #fafbff;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.avatar-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.15s ease;
}

.avatar-preview-placeholder {
  color: #999;
  font-size: 13px;
}

.avatar-live-144 {
  width: 144px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.avatar-canvas {
  width: 144px;
  height: 144px;
  border-radius: 10px;
  border: 1px solid #d0d7e2;
  background: #fff;
}

.avatar-live-label {
  font-size: 12px;
  color: #666;
}

.avatar-controls {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #333;
}

.slider-row input[type="range"] {
  flex: 1;
}

.slider-value {
  width: 44px;
  text-align: right;
  color: #666;
}

.avatar-buttons {
  display: flex;
  gap: 10px;
}

.avatar-buttons button {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #4A90E2;
  background: #fff;
  color: #4A90E2;
  cursor: pointer;
}

.avatar-buttons button.primary {
  background: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
}

.avatar-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.avatar-error {
  color: #e74c3c;
  font-size: 13px;
}

/* 支付弹窗样式 */
.payment-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.payment-modal-content {
  width: 90%;
  max-width: 420px;
  max-height: 90vh;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.payment-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.payment-modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.payment-modal-close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}

.payment-modal-close-btn:hover {
  color: #4A90E2;
}

.payment-modal-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.amount-selector {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.amount-selector label {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.amount-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.amount-btn {
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background-color: #f9fafb;
  color: #333;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.amount-btn:hover {
  border-color: #4A90E2;
  background-color: #f0f6ff;
}

.amount-btn.active {
  background-color: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
}

.custom-amount {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.custom-amount label {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

.amount-input {
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  background-color: #f9fafb;
}

.amount-input:focus {
  outline: none;
  border-color: #4A90E2;
  background-color: #fff;
}

.amount-display {
  padding: 10px;
  background-color: #f0f6ff;
  border-radius: 6px;
  text-align: center;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.amount-display span {
  color: #e74c3c;
}

.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.qrcode-container h4 {
  margin: 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.qrcode-wrapper {
  padding: 10px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.qrcode-canvas {
  display: block;
  width: 200px;
  height: 200px;
}

.order-info,
.amount-info {
  margin: 0;
  font-size: 12px;
  color: #666;
  text-align: center;
  line-height: 1.4;
}

.amount-info {
  font-size: 14px;
  font-weight: 600;
  color: #e74c3c;
}

.payment-success-text {
  color: #27ae60;
  font-size: 12px;
  margin-left: 6px;
  font-weight: normal;
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.qr-tip {
  margin: 0;
  font-size: 12px;
  color: #999;
  text-align: center;
  line-height: 1.5;
}

.pay-btn {
  padding: 10px;
  background-color: #4A90E2;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pay-btn:hover:not(:disabled) {
  background-color: #357ABD;
}

.pay-btn:disabled {
  background-color: #a5c5f5;
  cursor: not-allowed;
}

.payment-error {
  padding: 8px;
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 12px;
  line-height: 1.4;
}

/* 提现窗体样式 */
.withdraw-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.withdraw-modal-content {
  width: 90%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}

.withdraw-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.withdraw-modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.withdraw-modal-close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}

.withdraw-modal-close-btn:hover {
  color: #4A90E2;
}

.withdraw-modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.withdraw-amount-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.withdraw-amount-group label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.withdraw-amount-input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  color: #333;
  background-color: #f9fafb;
  box-sizing: border-box;
}

.withdraw-amount-input:focus {
  outline: none;
  border-color: #4A90E2;
  background-color: #fff;
}

.withdraw-error {
  padding: 8px 10px;
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  color: #856404;
  font-size: 13px;
  line-height: 1.4;
}

.withdraw-tip {
  margin: 6px 0 0 0;
  padding: 8px 10px;
  background: #f0f6ff;
  border-radius: 6px;
  color: #357ABD;
  font-size: 13px;
  line-height: 1.6;
  border: 1px solid #e5e7eb;
}

.withdraw-button-group {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

.withdraw-btn {
  flex: 1;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #ddd;
  background-color: #f9fafb;
  color: #333;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.withdraw-btn:hover {
  border-color: #4A90E2;
  background-color: #f0f6ff;
  color: #4A90E2;
}

.withdraw-btn.primary {
  background-color: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
}

.withdraw-btn.primary:hover {
  background-color: #357ABD;
  border-color: #357ABD;
}

/* 响应式设计 */
@media (max-width: 640px) {
  .payment-modal-content {
    width: 95%;
    margin: 0 10px;
  }
   
  .amount-options {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
