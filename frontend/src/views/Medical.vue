<template>
  <div class="medical-container">
    <TitleBar
      title="医学诊室"
      :is-logged-in="isLoggedIn"
      :user-avatar="userAvatar"
      :user-status-title="userStatusTitle"
      @status-click="handleUserStatusClick"
    />
     <!-- 免责声明 -->
      <div class="disclaimer">
        注:结果由Ai生成,不能替代正规医院,请咨询专业医疗机构
      </div>

    <div class="tabs-wrapper">
      <button class="tab-btn" :class="{ active: activeTab === 'consultation' }" @click="activeTab = 'consultation'">
        病情问诊
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'analysis' }" @click="activeTab = 'analysis'">
        医学分析
      </button>
    </div>

    <div v-if="activeTab === 'consultation'" class="consultation-tab">
      <div ref="consultationResultRef" class="consultation-result">
        <div v-if="!consultationMessages.length" class="result-placeholder">
          &lt;经过优化的医学人工智能模型，问诊结果在此回复。&gt;<br>
          &lt;医学影像分析到【医学分析】：<br>
          (1)医学影像：CT扫描、核磁共振、组织病理成像等;<br>
          (2)临床影像：胸部X光片、皮肤科图像、眼科图像等;<br>
          (3)医疗数据：医生诊断病历、电子健康记录、解剖特征数据等。&gt;
        </div>
        <div v-else class="consultation-chat">
          <div v-for="msg in consultationMessages" :key="msg.id" :class="['chat-item', msg.role]">
            <div class="chat-bubble">
              <div class="chat-header">
                <img
                  :src="msg.role === 'assistant' ? assistantAvatar : userAvatar"
                  :alt="msg.role === 'assistant' ? 'Ai体征分析助手' : '用户头像'"
                  class="chat-avatar"
                />
                <div class="chat-name">
                  {{ msg.role === 'assistant' ? 'Ai体征分析助手' : userDisplayName }}
                </div>
              </div>
              <div
                v-if="msg.role === 'assistant'"
                class="chat-content result-content markdown-body"
                v-html="formatConsultationMessage(msg.content)"
              ></div>
              <div v-else class="chat-content" v-text="msg.content"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="consultation-input-wrapper">
        <textarea
          v-model="consultationText"
          class="consultation-input"
          :placeholder="consultationPlaceholder"
          :disabled="isOcrRecognizing"
        ></textarea>
        <input
          ref="consultationFileInput"
          type="file"
          accept=".png,.jpg,.jpeg,image/png,image/jpeg"
          @change="handleConsultationAttachmentSelect"
          style="display: none"
        />
        <div class="consultation-actions">
          <div class="consultation-left-actions">
            <button class="thinking-toggle" :class="{ active: deepThinking }" @click="toggleDeepThinking">
              深度思考
            </button>
            <span v-if="isOcrRecognizing" class="ocr-recognizing-tip">正在识别内容...</span>
          </div>
          <div class="consultation-right-actions">
            <button class="attachment-btn" @click="selectConsultationAttachment" :disabled="isOcrRecognizing">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 12.5L14.5 7C16.1569 5.34315 18.8431 5.34315 20.5 7C22.1569 8.65685 22.1569 11.3431 20.5 13L12 21.5C9.51472 23.9853 5.48528 23.9853 3 21.5C0.514719 19.0147 0.514719 14.9853 3 12.5L11 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button class="send-btn" @click="submitConsultation" :disabled="isConsulting || isOcrRecognizing">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 4L12 20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M6 10L12 4L18 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="analysis-tab">
      <!-- 分析类型选择 -->
      <div class="analysis-type-select">
        <label for="analysisType" class="analysis-type-label">分析提示</label>
        <select id="analysisType" v-model="selectedAnalysisType" @change="handleAnalysisTypeChange" class="analysis-type-combobox">
          <option value="<无>" >&lt;无&gt;</option>
          <option value="分析医学影像(CT\MRI\X光片)，描述解剖结构、异常情况与关键特征，给出明确医学影像描述。">分析医学影像(CT\MRI\X光片)，描述解剖结构、异常情况与关键特征，给出明确医学影像描述。</option>
          <option value="分析病理切片图像，描述关键病理特征、形态改变或病灶指标，给出明确结构化结论。">分析病理切片图像，描述关键病理特征、形态改变或病灶指标，给出明确结构化结论。</option>
          <option value="分析电子健康记录(EHR)和医生诊断病历，提取关键病史、临床表现、检查结果与治疗记录，归纳诊断依据。">分析电子健康记录(EHR)和医生诊断病历，提取关键病史、临床表现、检查结果与治疗记录，归纳诊断依据。</option>
          <option value="分析医疗数据(影像\病历)，指出数据间一致性、矛盾点或临床线索，给出综合分析摘要。">分析医疗数据(影像\病历)，指出数据间一致性、矛盾点或临床线索，给出综合分析摘要。</option>
        </select>
      </div>

      <!-- 文本输入区域 -->
      <textarea 
        v-model="medicalText"
        class="text-input" 
        placeholder="<上传医学影像及对影像描述，输入不超过1024字。>"
      ></textarea>

      <!-- 操作按钮 -->
      <div class="button-group">
        <button class="btn btn-primary" @click="selectImage">
          选择影像
        </button>
        <button class="btn btn-primary" @click="clearImage">
          清除影像
        </button>
         <button class="btn btn-primary" @click="openMedicalDemo">
          分析案例
        </button>
        <button class="btn btn-primary" @click="submitDiagnosis" :disabled="isDiagnosing">
          {{ isDiagnosing ? '正在分析' : '提交分析' }}
        </button>
      </div>

      <!-- 图片上传区域 -->
      <div class="image-upload-area" @click="selectImage">
        <div v-if="!selectedImage" class="image-placeholder">
          <svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <img v-else :src="selectedImage" alt="上传的影像" class="uploaded-image" />
        <input 
          ref="fileInput"
          type="file" 
          accept="image/*" 
          @change="handleImageSelect"
          style="display: none"
        />
      </div>

      <!-- 分析结果输出区域 -->
      <div class="result-section">
        <button 
          class="btn btn-copy" 
          @click="copyResult"
        >
          {{ copyButtonText }}
        </button>
        <div class="result-output">
          <div v-if="!diagnosisResult" class="result-placeholder">
            &lt;返回医学分析结果&gt;
          </div>
          <div v-else class="result-content markdown-body" v-html="formattedResult"></div>
        </div>
      </div>

      <!-- 医学案例弹窗 -->
      <div v-if="showDemoModal" class="modal-overlay" @click="closeMedicalDemo">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>医学分析案例</h2>
            <button class="close-btn" @click="closeMedicalDemo">×</button>
          </div>
          <div class="modal-body">
            <div class="demo-images">
              <div class="demo-image-item">
                <h3 class="demo-title">案例1:肺部病变影像</h3>
                <img src="/src/assets/medical_demo/demo1.jpg" alt="案例1" class="demo-image" />
              </div>
              <div class="demo-image-item">
                <h3 class="demo-title">案例2:左眼部外伤导致眼压升高</h3>
                <img src="/src/assets/medical_demo/demo2.jpg" alt="案例2" class="demo-image" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BottomNav active="home" icpPrefix="分析由AI完成,仅供参考" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import {
  submitDiagnosis as submitDiagnosisApi,
  submitMedicalConsultationStream,
  submitMedicalChatOcr
} from '../api/medical'
import { getMyInfo } from '../api/auth'
import { marked } from 'marked'
import defaultAvatar from '@/assets/image/avatar/default_avatar.png'
import consultationLogo from '@/assets/image/avatar/default_avatar.png'
import TitleBar from '@/components/TitleBar.vue'
import { onMounted } from 'vue'
import BottomNav from '@/components/BottomNav.vue'

const router = useRouter()
const { checkLogin } = useAuth()
const medicalText = ref('')
const selectedAnalysisType = ref('<无>')
const activeTab = ref<'consultation' | 'analysis'>('consultation')

const handleAnalysisTypeChange = () => {
  if (selectedAnalysisType.value !== '<无>') {
    medicalText.value = selectedAnalysisType.value
  }
}
const diagnosisResult = ref('')
const selectedImage = ref<string | null>(null)
const consultationText = ref('')
const consultationMessages = ref<
  Array<{ id: number; role: 'user' | 'assistant'; content: string }>
>([])
const consultationResultRef = ref<HTMLElement | null>(null)
const deepThinking = ref(true)
const isConsulting = ref(false)
const isOcrRecognizing = ref(false)
const isLoggedIn = ref(false)
const userAvatar = ref('')
const userName = ref('')
const userStatusTitle = computed(() => isLoggedIn.value ? userName.value : '点击登录')
const fileInput = ref<HTMLInputElement | null>(null)
const consultationFileInput = ref<HTMLInputElement | null>(null)
const isDiagnosing = ref(false)
const showDemoModal = ref(false)
const copyButtonText = ref('复制结果')
const consultationLogoRef = consultationLogo

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
})

// 计算属性：将 markdown 转换为 HTML
const formattedResult = computed(() => {
  if (!diagnosisResult.value) return ''
  return marked(diagnosisResult.value) as string
})

const formatConsultationMessage = (content: string) => {
  if (!content) return ''
  return marked(content) as string
}

const extractDiagnosisResultText = (response: any): string => {
  const candidates = [
    response?.data?.result,
    response?.data?.analysis_result,
    response?.result,
    response?.analysis_result,
    response?.message
  ]

  for (const value of candidates) {
    if (typeof value === 'string' && value.trim()) {
      return value
    }
  }

  return ''
}

const consultationPlaceholder = computed(() =>
  isLoggedIn.value
    ? '<我理解您的担忧，会尽力帮助您！详细描述身体情况>'
    : '<我理解您的担忧，会尽力帮助您！详细描述身体情况（请先注册/登录）>'
)

const userDisplayName = computed(() => userName.value || '用户')
const assistantAvatar = defaultAvatar

const selectImage = () => {
  fileInput.value?.click()
}

const handleImageSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    const maxSizeBytes = 2 * 1024 * 1024
    if (file.size > maxSizeBytes) {
      alert('上传的图像需小于2MB')
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      return
    }
    const reader = new FileReader()
    reader.onload = (e) => {
      selectedImage.value = e.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const clearImage = () => {
  selectedImage.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const openMedicalDemo = () => {
  // 显示医学案例弹窗
  showDemoModal.value = true
}

const closeMedicalDemo = () => {
  // 关闭医学案例弹窗
  showDemoModal.value = false
}

const copyResult = async () => {
  if (!diagnosisResult.value) return

  const textToCopy = diagnosisResult.value

  const fallbackCopy = () => {
    const textarea = document.createElement('textarea')
    textarea.value = textToCopy
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    return ok
  }

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(textToCopy)
    } else {
      const ok = fallbackCopy()
      if (!ok) {
        throw new Error('fallback copy failed')
      }
    }

    copyButtonText.value = '已复制'
    setTimeout(() => {
      copyButtonText.value = '复制结果'
    }, 2000)
  } catch (error) {
    console.error('复制失败:', error)
    alert('复制失败，请手动复制')
  }
}

const submitDiagnosis = async () => {
  if (!checkLogin()) {
    router.push('/my-info')
    return
  }

  if (!medicalText.value.trim()) {
    alert('请输入医学文字')
    return
  }

  if (medicalText.value.length > 1024) {
    alert('输入医学文字长度大于1024')
    return
  }

   // 获取用户算力点
  let credit = 0
  try {
    const info = await getMyInfo()
    credit = info?.data?.account_credit ?? 0
  } catch (e) {
    alert('获取算力点失败，请重试')
    return
  }

  if (credit < 9.90) {
    alert('您的算力点不足9.90，请到[ 我的 ]菜单中赞助。')
    return
  }

  if (!window.confirm('医学分析将消耗9.90算力点，请问是否继续？')) {
    return
  }

  // 设置诊断状态
  isDiagnosing.value = true

  try {
    const data: any = {
      prompt_txt: medicalText.value
    }

    // 如果有选择图片，添加到请求中
    if (selectedImage.value) {
      data.image_data = selectedImage.value
    }

    // 清空上次结果
    diagnosisResult.value = "<请耐心等待大约5~10分钟，返回医学分析结果。正在分析时可以退出当前页面，到[ 分析记录 ]查看结果。>"

    const response = await submitDiagnosisApi(data)

    if (response.code == 200) {
      const resultText = extractDiagnosisResultText(response)
      if (resultText) {
        diagnosisResult.value = resultText
      } else {
        diagnosisResult.value = '<分析已完成，但未返回可展示的结果文本，请到[ 分析记录 ]查看详情。>'
      }
    } else {
      alert(response.message || '分析失败，请稍后重试')
    }
  } catch (error: any) {
    console.error('代理连接超时:', error)
    alert(error?.message || "服务暂未返回结果，稍后在[业务管理]->[分析记录]查看结果")
  } finally {
    // 无论成功还是失败，都恢复按钮状态
    isDiagnosing.value = false
  }
}

const toggleDeepThinking = () => {
  deepThinking.value = !deepThinking.value
}

const selectConsultationAttachment = () => {
  if (!checkLogin()) {
    router.push('/login')
    return
  }
  consultationFileInput.value?.click()
}

const handleConsultationAttachmentSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }

  const fileName = file.name || ''
  const ext = fileName.includes('.') ? fileName.split('.').pop()?.toLowerCase() || '' : ''
  const allowedExt = ['png', 'jpg', 'jpeg']
  if (!allowedExt.includes(ext)) {
    alert('仅支持png/jpg/jpeg格式图片')
    if (consultationFileInput.value) {
      consultationFileInput.value.value = ''
    }
    return
  }

  const maxSizeBytes = 2 * 1024 * 1024
  if (file.size > maxSizeBytes) {
    alert('上传的图片需小于2MB')
    if (consultationFileInput.value) {
      consultationFileInput.value.value = ''
    }
    return
  }

  isOcrRecognizing.value = true
  try {
    const result = await submitMedicalChatOcr(file)
    if (result?.code !== 200) {
      alert(result?.message || 'OCR识别失败')
      return
    }

    const ocrText = String(result?.data?.ocr_text || '').trim()
    if (!ocrText) {
      alert('未识别到可用文本，请更换清晰图片后重试')
      return
    }

    if (consultationText.value.trim()) {
      consultationText.value = `${consultationText.value.trim()}\n${ocrText}`
    } else {
      consultationText.value = ocrText
    }
  } catch (error) {
    console.error('OCR识别失败:', error)
    alert('OCR识别失败，请稍后重试')
  } finally {
    isOcrRecognizing.value = false
    if (consultationFileInput.value) {
      consultationFileInput.value.value = ''
    }
  }
}

const scrollConsultationToBottom = () => {
  const container = consultationResultRef.value
  if (!container) return
  container.scrollTop = container.scrollHeight
}

const submitConsultation = async () => {
  if (!checkLogin()) {
    router.push('/login')
    return
  }

  if (!consultationText.value.trim()) {
    alert('请输入病情描述')
    return
  }

  isConsulting.value = true
  const now = Date.now()
  const submittedText = consultationText.value.trim()
  consultationMessages.value.push({
    id: now,
    role: 'user',
    content: submittedText
  })
  consultationMessages.value.push({
    id: now + 1,
    role: 'assistant',
    content: ''
  })
  const assistantIndex = consultationMessages.value.length - 1
  await nextTick()
  scrollConsultationToBottom()

  try {
    const response = await submitMedicalConsultationStream({
      prompt_txt: submittedText,
      deep_thinking: deepThinking.value
    })

    if (!response.ok) {
      let message = '分析失败'
      try {
        const err = await response.json()
        message = err?.message || message
      } catch (error) {
        // ignore json parse error
      }
      alert(message)
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      alert('服务暂未返回结果，请稍后重试')
      return
    }

    const decoder = new TextDecoder('utf-8')
    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }
      if (consultationMessages.value[assistantIndex]) {
        consultationMessages.value[assistantIndex].content += decoder.decode(value, { stream: true })
      }
      await nextTick()
      scrollConsultationToBottom()
    }
  } catch (error: any) {
    console.error('问诊失败:', error)
    alert('服务暂未返回结果，请稍后重试')
  } finally {
    consultationText.value = ''
    isConsulting.value = false
  }
}

/*
const loadUserStatus = async () => {
  isLoggedIn.value = checkLogin()
  if (isLoggedIn.value) {
    const token = localStorage.getItem('token')
    try {
      const response = await fetch(window.VITE_GLOB_API_URL + '/api/user_info', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const result = await response.json()
      if (result.code === 200 && result.data) {
        userName.value = result.data.userAccount || result.data.realName || '用户'
        // 头像处理：如果有base64数据的头像，使用头像；否则使用默认头像
        userAvatar.value = result.data.avatar ? `data:image/png;base64,${result.data.avatar}` : defaultAvatar
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      userAvatar.value = defaultAvatar
    }
  }
}*/

const handleUserStatusClick = () => {
  if (isLoggedIn.value) {
    router.push('/my-info')
  } else {
    router.push('/login')
  }
}

// 页面加载时获取用户状态
//loadUserStatus()

onMounted(async () => {
  const isLogged = checkLogin()
  isLoggedIn.value = isLogged
  if (isLogged) {
    const cachedUserAccount = localStorage.getItem('user_account')
    if (cachedUserAccount) {
      userName.value = cachedUserAccount
    }
    const cachedAvatar = localStorage.getItem('user_avatar')
    if (cachedAvatar) {
      // 如果是 base64 且没有前缀，自动加上
      userAvatar.value = cachedAvatar.startsWith('data:image') ? cachedAvatar : `data:image/png;base64,${cachedAvatar}`
    } else {
      userAvatar.value = defaultAvatar
    }
  } else {
    userAvatar.value = defaultAvatar
  }
})
</script>

<style scoped>
.analysis-tab {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}

.analysis-type-select {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -10px 0px 0px 0px;
}
.analysis-type-label {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #357abd;
  font-weight: 500;
  gap: 5px;
  width: 75px;
}
.analysis-type-icon {
  vertical-align: middle;
  margin-right: 2px;
}
.analysis-type-combobox {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  padding: 5px 12px;
  border: 1px solid #4A90E2;
  border-radius: 5px;
  font-size: 14px;
  background: #f5f8ff;
  color: #333;
  outline: none;
  transition: border-color 0.3s;
  box-shadow: 0 2px 8px rgba(74,144,226,0.04);
  box-sizing: border-box;
  line-height: 1;
}

@media (max-width: 600px) {
  .analysis-type-combobox {
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 14px;
    line-height: 1.2;
  }
}
.analysis-type-combobox:focus {
  border-color: #357abd;
  background: #fff;
}
.analysis-type-combobox option {
  padding: 6px 10px;
  font-size: 14px;
}
.tabs-wrapper {
  display: flex;
  gap: 10px;
  background: #fff;
  padding: 6px;
  border-radius: 10px;
  border: 1px solid #e6ecf7;
  box-shadow: 0 2px 10px rgba(74, 144, 226, 0.08);
  margin-top: -5px;
}

.tab-btn {
  flex: 1;
  padding: 10px 8px;
  border: none;
  background: #f3f6fb;
  color: #4a5568;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn.active {
  background: #4A90E2;
  color: #fff;
  box-shadow: 0 6px 16px rgba(74, 144, 226, 0.3);
}

.consultation-tab {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: -5px;
  flex: 1;
  padding-bottom: 0px;
}

.consultation-result {
  min-height: 0;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fafafa;
  box-sizing: border-box;
  height: calc(
    var(--consult-viewport-height)
    - var(--consult-top-offset)
    - var(--consult-input-height)
    - var(--consult-input-gap)
    - var(--bottom-nav-height)
    - var(--consult-safe-bottom)
  );
  max-height: none;
  overflow-y: auto;
  flex: 0 0 auto;
  margin-bottom: var(--consult-input-gap);
}

.consultation-chat {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.chat-item.assistant {
  justify-content: flex-start;
}

.chat-item.user {
  justify-content: flex-end;
}

.chat-item.user .chat-bubble {
  order: 1;
}

.chat-item.user .chat-avatar {
  order: 2;
}

.chat-bubble {
  max-width: calc(82% + 40px);
  border-radius: 12px;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #e6ecf7;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chat-item.user .chat-bubble {
  background: #e8f2ff;
  border-color: #cfe3ff;
  transform: translateX(5px);
}

.chat-item.assistant .chat-bubble {
  background: #e8f2ff;
  border-color: #cfe3ff;
  border-radius: 8px;
  padding: 12px;
  box-shadow: none;
  transform: translateX(-5px);
}

.chat-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #e2e8f0;
  background: #fff;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.chat-name {
  font-size: 14px;
  color: #4a5568;
  margin-bottom: 0px;
  font-weight: 700;
}

.chat-item.user .chat-header {
  justify-content: flex-end;
}

.chat-item.user .chat-header .chat-avatar {
  order: 2;
}

.chat-item.user .chat-header .chat-name {
  order: 1;
}

.chat-content {
  font-size: 14px;
  color: #2d3748;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-item.assistant .chat-content {
  padding-left: 0px;
}

.chat-content.result-content {
  color: #333;
  line-height: 1.0;
  font-size: 14px;
}

.chat-content.markdown-body {
  line-height: 1.0;
  color: #333;
}

.chat-content.result-content.markdown-body {
  line-height: 1.2;
  color: #333;
  margin-top: 20px;
}

.chat-content.markdown-body p {
  margin-bottom: 0px;

}

.chat-content.markdown-body h1,
.chat-content.markdown-body h2,
.chat-content.markdown-body h3,
.chat-content.markdown-body h4,
.chat-content.markdown-body h5,
.chat-content.markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.20;
  color: #24292e;
}

.consultation-input-wrapper {
  position: fixed;
  left: 20px;
  right: 20px;
  bottom: calc(24px + var(--bottom-nav-height) + var(--consult-input-gap) + var(--consult-safe-bottom));
  z-index: 950;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 12px;
  box-sizing: border-box;
  margin-top: 0;
  margin-bottom: -12px;
}

.consultation-input {
  width: 100%;
  min-height: 100px;
  padding: 10px;
  border: none;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  background-color: transparent;
  box-sizing: border-box;
  padding-bottom: 20px;
}

.consultation-input:focus {
  outline: none;
}

.consultation-input:focus::placeholder {
  color: transparent;
}

.consultation-actions {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.consultation-right-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.consultation-left-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-toggle {
  border: 1px solid #d6e4ff;
  background: #f4f8ff;
  color: #4A90E2;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.thinking-toggle.active {
  background: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
}

.ocr-recognizing-tip {
  font-size: 12px;
  color: #4A90E2;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #4A90E2;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.attachment-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid #d6e4ff;
  background: #f4f8ff;
  color: #4A90E2;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.attachment-btn:disabled {
  background: #f3f4f6;
  color: #94a3b8;
  border-color: #e2e8f0;
  cursor: not-allowed;
}

.send-btn:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
}
.medical-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 124px;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  gap: 10px;
  --bottom-nav-height: 56px;
  --consult-input-gap: 20px;
  --consult-input-height: 200px;
  --consult-top-offset: 130px;
  --consult-viewport-height: 100dvh;
  --consult-safe-bottom: 0px;
}

@media (max-width: 600px) {
  .medical-container {
    --consult-viewport-height: 100svh;
    --consult-safe-bottom: env(safe-area-inset-bottom, 0px);
  }

  .consultation-input-wrapper {
    left: 12px;
    right: 12px;
  }

  .nav-btn {
    padding: 10px;
    font-size: 14px;
    gap: 4px;
  }


  .consultation-tab {
    width: calc(100% + 16px);
    margin-left: -8px;
    margin-right: -8px;
  }
}

.title-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 16px 0;
  padding: 4px 10px;
  background: linear-gradient(135deg, #667eea 0%, #667eea 100%);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);

.title-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
  letter-spacing: 1px;
  margin: 0;
  }

  .title-subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.85);
    margin: 3px 0 0 0;
    font-weight: 400;
    letter-spacing: 0.5px;
  flex: 1;
}

.user-status {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
  margin-left: 10px;
}

.user-status:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.login-text {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
}

.user-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.disclaimer {
  background-color: #fff;
  color: #ff4444;
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: bold;
  line-height: 1.0;
  text-align: center;
  margin-top: -20px;
}

.text-input{
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  background-color: #fff;
  box-sizing: border-box;
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-copy {
  align-self: flex-start;
  padding: 10px 8px 10px 8px;
  background-color: #28a745;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: -6px;
}

.btn-copy:hover {
  background-color: #218838;
}

.result-output {
  width: 100%;
  min-height: 400px;
  padding: 12px;
  padding-left: 22px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  background-color: #fafafa;
  box-sizing: border-box;
  overflow-y: auto;
}

.text-input:focus {
  outline: none;
  border-color: #4A90E2;
}

.text-input:focus::placeholder {
  color: transparent;
}

.result-placeholder {
  color: #999;
  font-size: 14px;
}

.result-content {
  color: #333;
  line-height: 1.8;
}


.button-group {
  display: flex;
  gap: 12px;
}

.btn {
  flex: 1;
  padding: 10px 8px 10px 8px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #4A90E2;
  color: #fff;
  font-size: 14px;
}

.btn-primary:hover {
  background-color: #357ABD;
}

.btn-secondary {
  background-color: #357ABD;
}

.btn-secondary:hover {
  background-color: #357ABD;
}

.btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn:disabled:hover {
  background-color: #ccc;
}

.image-upload-area {
  width: 100%;
  min-height: 200px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 200px;
}

.uploaded-image {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.bottom-nav {
  position: fixed;
  bottom: 24px;
  left: 0;
  right: 0;
  display: flex;
  background-color: #fff;
  border-top: 1px solid #ddd;
  padding: 8px 0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.icp-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 24px;
  line-height: 24px;
  text-align: center;
  font-size: 12px;
  background-color: #fff;
  color: #666;
  border-top: 1px solid #eee;
  z-index: 999;
}

.icp-footer a {
  color: #666;
  text-decoration: none;
}

.icp-footer a:hover {
  color: #4A90E2;
  text-decoration: underline;
}

.nav-menu-wrapper {
  flex: 1;
  position: relative;
}

.nav-btn {
  flex: 1;
  width: 100%;
  padding: 12px;
  border: none;
  background-color: transparent;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-weight: 500;
}

.menu-icon {
  display: inline-block;
  font-size: 16px;
}

.nav-btn:hover {
  color: #4A90E2;
  background-color: rgba(74, 144, 226, 0.08);
}

.nav-btn.active {
  color: #4A90E2;
  font-weight: bold;
}

.menu-arrow {
  display: inline-block;
  margin-left: 2px;
  font-size: 10px;
}

.business-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: linear-gradient(to bottom, #ffffff, #fafafa);
  border: 2px solid #4A90E2;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -8px 24px rgba(74, 144, 226, 0.15), 0 -4px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  animation: slideUpMenu 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 100;
}

@keyframes slideUpMenu {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-item {
  width: 100%;
  padding: 14px 16px;
  border: none;
  background-color: transparent;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  border-bottom: 1px solid #e8f0ff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
}

.item-icon {
  display: inline-block;
  font-size: 16px;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:hover {
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.12), rgba(118, 75, 162, 0.08));
  color: #4A90E2;
  padding-left: 20px;
  padding-right: 12px;
  font-weight: 600;
}

/* 医学案例弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 1000px;
  height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #ddd;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 32px;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: color 0.3s;
}

.close-btn:hover {
  color: #4A90E2;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  justify-content: center;
}

.demo-images {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
}

.demo-image-item {
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.demo-title {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: bold;
  color: #f78a04;
  align-self:center;
}

.demo-image {
  width: 100%;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Markdown 样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
  font-size: 14px;
  line-height: 1.8;
  word-wrap: break-word;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 20px;
  margin-bottom: 15px;
  font-weight: 500;
  line-height: 1.2;
  color: #24292e;
}

.markdown-body h1 {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h2 {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-body h3 {
  font-size: 1.25em;
}

.markdown-body h4 {
  font-size: 1em;
}

.markdown-body p {
  margin-top: 0;
  margin-bottom: 16px;
}

.markdown-body ul,
.markdown-body ol {
  margin-top: 0;
  margin-bottom: 16px;
  padding-left: 2em;
}

.markdown-body li {
  margin-bottom: 8px;
}

.markdown-body li + li {
  margin-top: 0.25em;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

.markdown-body pre {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.markdown-body pre code {
  display: inline;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}

.markdown-body strong {
  font-weight: 600;
}

.markdown-body em {
  font-style: italic;
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}

.markdown-body table {
  border-spacing: 0;
  border-collapse: collapse;
  margin-bottom: 16px;
  width: 100%;
}

.markdown-body table th,
.markdown-body table td {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}

.markdown-body table th {
  font-weight: 600;
  background-color: #f6f8fa;
}

.markdown-body table tr {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}

.markdown-body table tr:nth-child(2n) {
  background-color: #f6f8fa;
}

.markdown-body a {
  color: #0366d6;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.consultation-result :deep(.chat-content.markdown-body h1),
.consultation-result :deep(.chat-content.markdown-body h2),
.consultation-result :deep(.chat-content.markdown-body h3),
.consultation-result :deep(.chat-content.markdown-body h4),
.consultation-result :deep(.chat-content.markdown-body h5),
.consultation-result :deep(.chat-content.markdown-body h6) {
  margin-top: 0px;
  margin-bottom: -10px;
  line-height: 0;
}

.consultation-result :deep(.chat-content.markdown-body p) {
  margin-top: 5px;
  margin-bottom: 5px;
}

.consultation-result :deep(.chat-content.markdown-body h1 + p),
.consultation-result :deep(.chat-content.markdown-body h2 + p),
.consultation-result :deep(.chat-content.markdown-body h3 + p),
.consultation-result :deep(.chat-content.markdown-body h4 + p),
.consultation-result :deep(.chat-content.markdown-body h5 + p),
.consultation-result :deep(.chat-content.markdown-body h6 + p) {
  margin-top: 6px;
}

.consultation-result :deep(.chat-content.markdown-body ul),
.consultation-result :deep(.chat-content.markdown-body ol) {
  margin-top: 0px;
  margin-bottom: 0px;
  padding-left: 1.0em;
}

.consultation-result :deep(.chat-content.markdown-body p + ul),
.consultation-result :deep(.chat-content.markdown-body p + ol) {
  margin-top: -25px;
}

.consultation-result :deep(.chat-content.markdown-body ul + p),
.consultation-result :deep(.chat-content.markdown-body ol + p) {
  margin-top: -25px;
}

.consultation-result :deep(.chat-content.markdown-body li) {
  margin-bottom: 0px;
  line-height: 1.2;
}

.consultation-result :deep(.chat-content.markdown-body li + li) {
  margin-top: 0px;
}

.consultation-result :deep(.chat-content.markdown-body li > p) {
  margin: 0;
}

.consultation-result :deep(.chat-content.markdown-body li > ul),
.consultation-result :deep(.chat-content.markdown-body li > ol) {
  margin-top: 0px;
  margin-bottom: -40px;
}

.consultation-result :deep(.chat-content.markdown-body ul ul),
.consultation-result :deep(.chat-content.markdown-body ul ol),
.consultation-result :deep(.chat-content.markdown-body ol ul),
.consultation-result :deep(.chat-content.markdown-body ol ol) {
  padding-left: 0em;
}
</style>