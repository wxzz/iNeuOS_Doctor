<template>
  <div class="medical-record-container">
    <TitleBar
      title="分析记录"
      :is-logged-in="isLoggedIn"
      :user-avatar="userAvatar"
      :user-status-title="userStatusTitle"
      @status-click="handleUserStatusClick"
    />
    
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <label class="filter-label">分析状态：</label>
      <select v-model="selectedStatus" class="filter-select" @change="onStatusChange">
        <option value="全部">全部</option>
        <option value="0">分析成功</option>
        <option value="1">正在分析</option>
        <option value="-1">分析异常</option>
      </select>
      <input 
        v-model="searchInput" 
        class="filter-input" 
        type="text" 
        placeholder="搜索关键字" 
      />
      <button class="filter-button" @click="applySearch">查询</button>
    </div>
    
    <!-- 加载提示 -->
    <div v-if="isLoading" class="message-box">
      <p>正在获取数据...</p>
    </div>
    
    <!-- 空数据提示 -->
    <div v-else-if="!isLoading && records.length === 0" class="message-box">
      <p>当前没有数据记录</p>
    </div>
    
    <!-- 表格区域 -->
    <div v-else class="table-wrapper">
      <table class="record-table">
        <thead>
          <tr>
            <th>序号</th>
            <th>分析状态</th>
            <th>医学描述</th>
            <th>医学影像</th>
            <th>分析结果</th>
            <th>耗时</th>
            <th>时间</th>
            <th>算力点</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="(record, index) in records" 
            :key="index"
            :class="{
              'status-analyzing': record.status === 1,
              'status-success': record.status === 0,
              'status-error': record.status === -1
            }"
          >
            <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
            <td>
              <div>{{ record.statusText }}</div>
              <button 
                v-if="record.status === -1" 
                class="show-desc-btn" 
                @click="showStatusDesc(record)"
              >
                显示
              </button>
            </td>
            <td>{{ record.medicalText || '' }}</td>
            <td>
              <div class="image-cell" v-if="record.image" @click="showImage(record.image)" style="cursor: pointer;">
                <img :src="record.image" alt="医学影像" class="record-image" />
              </div>
              <div class="image-placeholder" v-else>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 17L12 22L22 17" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="#4A90E2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </td>
            <td>
              <div v-if="record.diagnosisResult" v-html="marked(record.diagnosisResult)" class="diagnosis-result"></div>
              <div v-else style="color: #999;"><注:未有结果></div>
            </td>
            <td class="center">{{ record.elapsedTime }}</td>
            <td>
              <div v-if="record.time">
                <div>{{ record.time.date }}</div>
                <div>{{ record.time.time }}</div>
              </div>
            </td>
            <td class="center">{{ record.credit !== null ? Number(record.credit).toFixed(2) : '' }}</td>
            <td>
              <div style="display: flex; flex-direction: column; gap: 4px;">
                <button 
                  v-if="record.id" 
                  class="delete-btn" 
                  @click="deleteRecord(index)"
                >
                  删除
                </button>
                <button 
                  v-if="record.id" 
                  class="download-btn" 
                  @click="downloadRecord(index)"
                >
                  下载
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 分页控件 -->
    <div v-if="!isLoading && records.length > 0" class="pagination-wrapper">
      <div class="pagination-info">
        共 {{ total }} 条记录，第 {{ currentPage }} / {{ totalPages }} 页
      </div>
      <div class="pagination-controls">
        <button 
          class="pagination-btn" 
          :disabled="currentPage === 1" 
          @click="goToPrevPage"
        >
          上一页
        </button>
        <button 
          v-for="page in getPageNumbers()" 
          :key="page" 
          class="pagination-btn" 
          :class="{ active: page === currentPage }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        <button 
          class="pagination-btn" 
          :disabled="currentPage === totalPages" 
          @click="goToNextPage"
        >
          下一页
        </button>
      </div>
    </div>
    
    <!-- 异常信息弹窗 -->
    <div v-if="showErrorModal" class="error-modal-overlay" @click="closeErrorModal">
      <div class="error-modal-content" @click.stop>
        <div class="error-modal-header">
          <h3>分析异常信息</h3>
          <button class="error-close-btn" @click="closeErrorModal">×</button>
        </div>
        <div class="error-modal-body">
          <p>{{ currentErrorDesc }}</p>
        </div>
      </div>
    </div>

    <!-- 医学影像预览弹窗 -->
    <div v-if="showImageModal" class="image-modal-overlay" @click="closeImageModal">
      <div class="image-modal-content" @click.stop>
        <div class="image-modal-header">
          <h3>医学影像照片</h3>
          <button class="image-modal-close-btn" @click="closeImageModal">×</button>
        </div>
        <img :src="currentImageSrc" alt="医学影像预览" class="image-modal-img" />
      </div>
    </div>

    <BottomNav active="history" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import html2pdf from 'html2pdf.js'
import { marked } from 'marked'
import defaultAvatar from '@/assets/image/avatar/default_avatar.png'
import TitleBar from '@/components/TitleBar.vue'
import BottomNav from '@/components/BottomNav.vue'

const router = useRouter()
const { checkLogin } = useAuth()

const isLoggedIn = ref(false)
const userAvatar = ref('')
const userName = ref('')
const userStatusTitle = computed(() => isLoggedIn.value ? userName.value : '点击登录')

interface Record {
  id: number
  user_id: number
  userAccount: string
  medicalText: string
  image: string | null
  diagnosisResult: string
  elapsedTime: string
  status: number | null
  statusText: string
  statusDesc: string
  sdt: string
  credit: number | null
  time: {
    date: string
    time: string
  } | null
}

const records = ref<Record[]>([])
const isLoading = ref(false)
const showErrorModal = ref(false)
const currentErrorDesc = ref('')
const showImageModal = ref(false)
const currentImageSrc = ref('')

// 查询控件状态
const selectedStatus = ref<string>('全部')
const searchInput = ref<string>('')

// 分页相关状态
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = ref(0)

// 点击“查询”或状态改变时，调用后端查询
const applySearch = async () => {
  currentPage.value = 1
  await loadRecords(selectedStatus.value, searchInput.value.trim(), 1)
}

const onStatusChange = async () => {
  await applySearch()
}

const goToPage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  await loadRecords(selectedStatus.value, searchInput.value.trim(), page)
}

const goToPrevPage = async () => {
  if (currentPage.value > 1) {
    await goToPage(currentPage.value - 1)
  }
}

const goToNextPage = async () => {
  if (currentPage.value < totalPages.value) {
    await goToPage(currentPage.value + 1)
  }
}

onMounted(async () => {
  console.log('MedicalRecord页面已挂载')
  // 判断登录
  const isLogged = checkLogin()
  isLoggedIn.value = isLogged
  if (isLogged) {
    // 仅登录后读取头像
    const cachedAvatar = localStorage.getItem('user_avatar')
    if (cachedAvatar) {
      userAvatar.value = cachedAvatar.startsWith('data:image') ? cachedAvatar : `data:image/png;base64,${cachedAvatar}`
    } else {
      userAvatar.value = defaultAvatar
    }
    console.log('用户已登录，开始加载分析记录')
    await loadRecords()
  } else {
    userAvatar.value = defaultAvatar
    console.log('用户未登录，重定向到登录页')
    router.push('/login')
  }
})
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
}
*/
const handleUserStatusClick = () => {
  if (isLoggedIn.value) {
    router.push('/my-info')
  } else {
    router.push('/login')
  }
}

const loadRecords = async (status?: string, kw?: string, page?: number) => {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    if (status && status !== '全部') params.set('status', status)
    if (kw) params.set('keyword', kw)
    params.set('page', String(page || currentPage.value))
    params.set('page_size', String(pageSize.value))
    const url = `/api/get_medicalrecords?${params.toString()}`
    const response = await fetch(url.startsWith('/api') ? window.VITE_GLOB_API_URL + url : url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    })
    const result = await response.json()
    if (result.code === 200) {
      records.value = result.data.map((item: any) => ({
        id: item.id,
        user_id: item.user_id,
        userAccount: item.user_account || '',
        medicalText: item.prompt_txt,
        image: item.image_data,
        diagnosisResult: item.result,
        elapsedTime: formatElapsed(item.elapsed_time, item.sdt, item.medical_status),
        status: typeof item.medical_status === 'number' ? item.medical_status : null,
        statusText: mapMedicalStatus(item.medical_status),
        statusDesc: item.medical_status_desc || '',
        sdt: item.sdt || '',
        credit: item.credit !== undefined ? item.credit : null,
        time: item.sdt ? formatTime(item.sdt) : null,
      }))
      total.value = result.total || 0
      totalPages.value = Math.ceil(total.value / pageSize.value)
    }
  } catch (error) {
    console.error('加载记录失败:', error)
  } finally {
    isLoading.value = false
  }
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return {
    date: date.toLocaleDateString('zh-CN'),
    time: date.toLocaleTimeString('zh-CN', { hour12: false }),
  }
}

const formatElapsed = (elapsed: any, sdt: string | null, status: number | null) => {
  // 优先使用后端返回的数值，格式化为两位小数（分钟）
  const toNumber = (val: any) => {
    const num = Number(val)
    return Number.isFinite(num) ? num : null
  }

  const fromBackend = toNumber(elapsed)
  if (fromBackend !== null) {
    return fromBackend.toFixed(2)
  }

  // 如果任务进行中且有开始时间，前端兜底计算
  if (status === 1 && sdt) {
    const start = new Date(sdt)
    if (!Number.isNaN(start.getTime())) {
      const now = new Date()
      const minutes = (now.getTime() - start.getTime()) / 60000
      return minutes.toFixed(2)
    }
  }

  return ''
}

const mapMedicalStatus = (status: number | null) => {
  if (status === 0) return '分析成功'
  if (status === 1) return '正在分析'
  if (status === -1) return '分析异常'
  return '未知'
}

const showStatusDesc = (record: Record) => {
  currentErrorDesc.value = record.statusDesc || '暂无状态描述信息'
  showErrorModal.value = true
}

const closeErrorModal = () => {
  showErrorModal.value = false
  currentErrorDesc.value = ''
}

const showImage = (imageSrc: string) => {
  currentImageSrc.value = imageSrc
  showImageModal.value = true
}

const closeImageModal = () => {
  showImageModal.value = false
  currentImageSrc.value = ''
}

const formatDateTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

const escapeHtml = (text: string) => {
  const map: { [key: string]: string } = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  }
  return text.replace(/[&<>"']/g, (m) => map[m] || m)
}

const isWeChatBrowser = () => /MicroMessenger/i.test(navigator.userAgent)

const getMiniProgramEnv = () =>
  new Promise<boolean>((resolve) => {
    const wxMini = (window as any).wx?.miniProgram
    if (!wxMini?.getEnv) {
      resolve(false)
      return
    }
    wxMini.getEnv((res: any) => resolve(!!res?.miniprogram))
  })

const normalizeDownloadUrl = (url: string) => url.replace(/^http:\/\//i, 'https://')

const blobToDataUrl = (blob: Blob) =>
  new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsDataURL(blob)
  })

const saveBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const downloadRecord = async (index: number) => {
  const record = records.value[index]
  if (!record || !record.id) return
  
  // 判断分析状态：只有状态为0（分析成功）才能下载
  if (record.status !== 0) {
    alert('当前分析结果不可用，无法正常下载。')
    return
  }
  
  try {
    // 获取当前用户名称，优先从record获取，否则从localStorage获取
    const currentUserName = record.userAccount || localStorage.getItem('user_account') || '未提供'
    
    // 格式化时间（驻掉T字符）
    const formattedDateTime = formatDateTime(record.sdt)
    
    // 处理分析结果的markdown格式（简单更换为HTML）
    const resultHtml = marked(record.diagnosisResult || '')
    
    // 构建整个HTML
    const htmlContent = `
      <html>
        <head>
          <meta charset="UTF-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
            h1 { text-align: center; margin-bottom: 10px; font-size: 24px; }
            hr { border: none; border-top: 2px solid #333; margin: 15px 0; }
            .field { margin-bottom: 12px; }
            .label { font-weight: bold; }
            .image-container { margin: 15px 0; }
            .image-container img { max-width: 400px; max-height: 300px; }
            .result-container { margin-top: 15px; padding: 10px; background-color: #f9f9f9; border-left: 3px solid #4A90E2; }
            .result-container h2 { margin-top: 0; font-size: 16px; color: #4A90E2; }
            .result-container ul, .result-container ol { padding-left: 20px; }
            .result-container li { margin-bottom: 8px; }
            .result-container strong { color: #333; }
            .disclaimer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }
          </style>
        </head>
        <body>
          <h1>Ai体征分析助手</h1>
          <hr />
          <div class="field">
            <span class="label">用户名称：</span>
            <span>${currentUserName}</span>
          </div>
          <div class="field">
            <span class="label">开始时间：</span>
            <span>${formattedDateTime}</span>
          </div>
          <div class="field">
            <span class="label">分析耗时：</span>
            <span>${record.elapsedTime} 分钟</span>
          </div>
          <div class="field">
            <span class="label">医学描述：</span>
            <span>${escapeHtml(record.medicalText || '未提交')}</span>
          </div>
          ${record.image ? `
          <div class="image-container">
            <span class="label">医学影像：</span><br>
            <img src="${record.image}" alt="医学影像" style="display: block; margin: 10px auto; max-width: 400px; max-height: 300px;" />
          </div>
          ` : `
          <div class="field">
            <span class="label">医学影像：</span>
            <span>未提交</span>
          </div>
          `}
          <div class="result-container">
            <h2>分析结果</h2>
            ${resultHtml}
          </div>
          <div class="field">
            <span class="label">下载时间：</span>
            <span>${new Date().toLocaleString('zh-CN')}</span>
          </div>
          <div class="disclaimer" style="color: red;">
            注：本医学诊断为人工智能模型分析结果,不能替代正规医院诊断结果,请咨询专业医疗机构。
          </div>
        </body>
      </html>
    `
    
    const element = document.createElement('div')
    element.innerHTML = htmlContent
    
    const opt = {
      margin: 10,
      filename: `${currentUserName}_分析结果_${new Date().getTime()}.pdf`,
      image: { type: 'jpeg' as const, quality: 0.98 },
      html2canvas: { scale: 1.0 },
      jsPDF: { orientation: 'portrait' as const, unit: 'mm', format: 'a4' }
    }
    
    const worker = html2pdf().set(opt).from(element).toPdf()
    const pdf = await worker.get('pdf')
    const blob = pdf.output('blob')

    // 微信内置浏览器：上传到服务端获取下载链接，再跳转到链接
    if (isWeChatBrowser()) {
      const dataUrl = await blobToDataUrl(blob)
      const response = await fetch(window.VITE_GLOB_API_URL + '/api/upload_medicalrecord_pdf', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: opt.filename,
          file_base64: dataUrl,
        }),
      })
      
      if (!response.ok) {
        const text = await response.text()
        console.error('上传失败，响应内容：', text)
        alert(`上传失败（HTTP ${response.status}），请检查文件大小或网络连接。`)
        return
      }
      
      const result = await response.json()
      if (result.code === 200 && result.data?.download_url) {
        const downloadUrl = normalizeDownloadUrl(result.data.download_url)
        const isMiniProgram = await getMiniProgramEnv()
        if (isMiniProgram) {
          const wxMini = (window as any).wx?.miniProgram
          const encodedUrl = encodeURIComponent(downloadUrl)
          const encodedName = encodeURIComponent(opt.filename)
          wxMini?.navigateTo({
            url: `/pages/pdf/index?url=${encodedUrl}&filename=${encodedName}`,
            fail: () => {
              alert('跳转小程序PDF页面失败，请重试。')
            }
          })
          return
        }
        else
        {
          window.location.href = downloadUrl
          alert('已生成下载链接，请在浏览器中保存或分享文件。')
          return
        }
      }
      alert(result.message || '生成下载链接失败')
      return
    }

    saveBlob(blob, opt.filename)
  } catch (error) {
    console.error('下载PDF失败:', error)
    alert('下载PDF失败，请稍后再试,'+error)
  }
}

const getPageNumbers = () => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
}

const deleteRecord = async (index: number) => {
  const record = records.value[index]
  if (!record || !record.id) return
  
  if (confirm('确定要删除这条记录吗？')) {
    try {
      const response = await fetch(window.VITE_GLOB_API_URL + '/api/delete_medicalrecord', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: record.id }),
      })
      const result = await response.json()
      if (result.code === 200) {
        // 如果当前页删除后没有记录了，且不是第一页，则返回上一页
        if (records.value.length === 1 && currentPage.value > 1) {
          await goToPage(currentPage.value - 1)
        } else {
          await loadRecords(selectedStatus.value, searchInput.value.trim(), currentPage.value)
        }
      } else {
        alert(result.message || '删除失败')
      }
    } catch (error) {
      console.error('删除记录失败:', error)
      alert('删除失败，请稍后重试')
    }
  }
}

</script>

<style scoped>
.medical-record-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 124px;
  background-color: #f5f5f5;
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


/* 筛选栏样式 */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: #fff;
  border-radius: 8px;
  padding: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-top: -10px
}

.filter-label {
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.filter-select,
.filter-input {
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  color: #333;
  background-color: #fff;
}

.filter-input {
  flex: 1;
}

.filter-button {
  padding: 6px 16px;
  background-color: #4A90E2;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.filter-button:hover {
  background-color: #357ABD;
}

/* 移动端适配：筛选栏换行与控件全宽 */
@media (max-width: 640px) {
  .filter-bar {
    flex-wrap: wrap;
    align-items: stretch;
  }

  .filter-label {
    width: 100%;
    margin-bottom: 2px;
  }

  .filter-select,
  .filter-input,
  .filter-button {
    flex: 1 1 100%;
    min-width: 0;
  }

  .filter-button {
    text-align: center;
  }
}

.message-box {
  background-color: #fff;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin: 20px 0;
}

.message-box p {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.table-wrapper {
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-top: 8px;
}

.record-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.record-table thead {
  background-color: #f8f9fa;
}

.record-table th {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  vertical-align: top;
}

.record-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  color: #333;
  vertical-align: top;
}

.record-table tbody tr:hover {
  background-color: #f8f9fa;
}

.record-table tbody tr:last-child td {
  border-bottom: none;
}

/* 分析状态背景颜色 */
.record-table tbody tr.status-analyzing {
  background-color: #fff3cd;
}

.record-table tbody tr.status-success {
  background-color: #e8f5ec;
}

.record-table tbody tr.status-error {
  background-color: #f9e4e7;
}

.record-table tbody tr.status-analyzing:hover {
  background-color: #ffe69c;
}

.record-table tbody tr.status-success:hover {
  background-color: #d9eee2;
}

.record-table tbody tr.status-error:hover {
  background-color: #f5c6cb;
}

.image-cell {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.record-image {
  max-width: 60px;
  max-height: 60px;
  object-fit: contain;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.image-placeholder {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #fafafa;
}

.delete-btn {
  padding: 6px 16px;
  background-color: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.delete-btn:hover {
  background-color: #e0e0e0;
  color: #333;
}

.delete-btn:active {
  background-color: #d0d0d0;
}

.download-btn {
  padding: 6px 16px;
  background-color: #4A90E2;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.download-btn:hover {
  background-color: #357ABD;
}

.download-btn:active {
  background-color: #2d5ca8;
}

.show-desc-btn {
  margin-top: 4px;
  padding: 4px 12px;
  background-color: #ffc107;
  color: #fb0404;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.show-desc-btn:hover {
  background-color: #ffb300;
}

.show-desc-btn:active {
  background-color: #ffa000;
}

/* 异常信息弹窗样式 */
.error-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.error-modal-content {
  background: #fff;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.error-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px;
  border-bottom: 1px solid #ddd;
  background-color: #f8d7da;
  font-size: 20px;
  border-radius: 8px 8px 0 0;
}

.error-modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #721c24;
}

.error-close-btn {
  background: none;
  border: none;
  font-size: 32px;
  color: #721c24;
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

.error-close-btn:hover {
  color: #c82333;
}

.error-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.error-modal-body p {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 医学影像预览弹窗样式 */
.image-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.image-modal-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
}

.image-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f8f9fa;
}

.image-modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
  font-weight: bold;
}

.image-modal-img {
  flex: 1;
  max-width: 100%;
  max-height: 100%;
  display: block;
  object-fit: contain;
}

.image-modal-close-btn {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
  line-height: 1;
}

.image-modal-close-btn:hover {
  color: #e74c3c;
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
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform: rotate(180deg);
}

.menu-arrow.open {
  transform: rotate(0deg);
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
  font-weight: 500;
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

.menu-item.active-menu-item {
  color: #4A90E2;
  font-weight: 600;
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.12), rgba(118, 75, 162, 0.08));
}

/* 序号加宽 */
.record-table th:nth-child(1),
.record-table td:nth-child(1) {
  min-width: 60px;
  text-align: center;
}

/* 分析状态加宽 */
.record-table th:nth-child(2),
.record-table td:nth-child(2) {
  min-width: 75px;
  text-align: center;
}

/* 医学描述加宽 */
.record-table th:nth-child(3),
.record-table td:nth-child(3) {
  min-width: 200px;
}

/* 分析结果列加宽 */
.record-table th:nth-child(5),
.record-table td:nth-child(5) {
  min-width: 400px;
}
.diagnosis-result {
  font-size: 13px;
  line-height: 1.5;
}

.diagnosis-result h1, .diagnosis-result h2, .diagnosis-result h3, .diagnosis-result h4, .diagnosis-result h5, .diagnosis-result h6 {
  margin: 8px 0 4px 0;
  font-size: 14px;
  font-weight: bold;
}

.diagnosis-result ul, .diagnosis-result ol {
  margin: 4px 0;
  padding-left: 20px;
}

.diagnosis-result li {
  margin: 2px 0;
}

.diagnosis-result code {
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 2px;
}

.diagnosis-result strong {
  font-weight: bold;
  color: #333;
}
/* 耗时列加宽并居中 */
.record-table th:nth-child(6),
.record-table td:nth-child(6) {
  min-width: 60px;
  text-align: center;
}

/* 信誉度列居中 */
.record-table th:nth-child(8),
.record-table td:nth-child(8) {
  min-width: 60px;
  text-align: center;
}

/* 操作按钮列加宽 */
.record-table th:nth-child(9),
.record-table td:nth-child(9) {
  min-width: 80px;
  text-align: center;
}


/* 小分辨率下表格横向滚动 */
@media (max-width: 1600px) {
  .table-wrapper {
    overflow-x: auto;
  }
}

/* 分页控件样式 */
.pagination-wrapper {
  margin-top: 10px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.pagination-info {
  text-align: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pagination-btn {
  padding: 8px 16px;
  background-color: #fff;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  min-width: 40px;
}

.pagination-btn:hover:not(:disabled) {
  background-color: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
}

.pagination-btn.active {
  background-color: #4A90E2;
  color: #fff;
  border-color: #4A90E2;
  font-weight: bold;
}

.pagination-btn:disabled {
  background-color: #f5f5f5;
  color: #ccc;
  cursor: not-allowed;
  border-color: #e0e0e0;
}

/* 移动端分页样式调整 */
@media (max-width: 640px) {
  .pagination-controls {
    gap: 4px;
  }
  
  .nav-btn {
    padding: 10px;
    font-size: 14px;
    gap: 4px;
  }

  .pagination-btn {
    padding: 6px 12px;
    font-size: 12px;
    min-width: 36px;
  }
}
</style>
