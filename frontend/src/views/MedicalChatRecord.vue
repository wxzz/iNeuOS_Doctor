<template>
  <div class="medical-chat-record-container">
    <TitleBar
      title="问诊记录"
      :is-logged-in="isLoggedIn"
      :user-avatar="userAvatar"
      :user-status-title="userStatusTitle"
      @status-click="handleUserStatusClick"
    />

    <div v-if="isLoading" class="message-box">
      <p>正在获取数据...</p>
    </div>

    <div v-else-if="!isLoading && records.length === 0" class="message-box">
      <p>当前没有数据记录</p>
    </div>

    <div v-else class="table-wrapper">
      <table class="record-table">
        <thead>
          <tr>
            <th class="col-index">序号</th>
            <th>问诊内容</th>
            <th class="col-time">开始时间</th>
            <th class="col-time">结束时间</th>
            <th class="col-actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(record, index) in records" :key="record.id">
            <td class="col-index">{{ (currentPage - 1) * pageSize + index + 1 }}</td>
            <td>{{ formatPromptPreview(record.promptTxt) }}</td>
            <td class="col-time">
              <div v-if="record.chatStart">
                <div>{{ record.chatStart.date }}</div>
                <div>{{ record.chatStart.time }}</div>
              </div>
              <div v-else>-</div>
            </td>
            <td class="col-time">
              <div v-if="record.chatEnd">
                <div>{{ record.chatEnd.date }}</div>
                <div>{{ record.chatEnd.time }}</div>
              </div>
              <div v-else>-</div>
            </td>
            <td class="col-actions">
              <div style="display: flex; flex-direction: column; gap: 4px;">
                <button class="delete-btn" @click="deleteRecord(record)">删除</button>
                <button class="download-btn" @click="downloadRecord(record)">下载</button>
                <button class="show-btn" @click="showRecord(record)">显示</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!isLoading && records.length > 0" class="pagination-wrapper">
      <div class="pagination-info">
        共 {{ total }} 条记录，第 {{ currentPage }} / {{ totalPages }} 页
      </div>
      <div class="pagination-controls">
        <button class="pagination-btn" :disabled="currentPage === 1" @click="goToPrevPage">
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
        <button class="pagination-btn" :disabled="currentPage === totalPages" @click="goToNextPage">
          下一页
        </button>
      </div>
    </div>

    <div v-if="showChatModal" class="chat-modal-overlay" @click="closeChatModal">
      <div class="chat-modal-content" @click.stop>
        <div class="chat-modal-header">
          <h3>问诊会话</h3>
          <button class="chat-modal-close-btn" @click="closeChatModal">×</button>
        </div>
        <div class="consultation-tab">
          <div class="consultation-result">
            <div v-if="!chatMessages.length" class="result-placeholder">
              <p>暂无会话内容</p>
            </div>
            <div v-else class="consultation-chat">
              <div v-for="msg in chatMessages" :key="msg.id" :class="['chat-item', msg.role]">
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
                    v-html="formatAssistantMessage(msg.content)"
                  ></div>
                  <div v-else class="chat-content" v-text="msg.content"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BottomNav active="chat-history" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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
const userStatusTitle = computed(() => (isLoggedIn.value ? userName.value : '点击登录'))

interface ChatRecord {
  id: string
  promptTxt: string
  chatStart: { date: string; time: string } | null
  chatEnd: { date: string; time: string } | null
}

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const records = ref<ChatRecord[]>([])
const isLoading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)

const showChatModal = ref(false)
const chatMessages = ref<ChatMessage[]>([])

const assistantAvatar = defaultAvatar
const userDisplayName = computed(() => userName.value || '用户')

const handleUserStatusClick = () => {
  if (isLoggedIn.value) {
    router.push('/my-info')
  } else {
    router.push('/login')
  }
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return {
    date: date.toLocaleDateString('zh-CN'),
    time: date.toLocaleTimeString('zh-CN', { hour12: false }),
  }
}

const formatPromptPreview = (text: string) => {
  const value = (text || '').trim()
  if (!value) return ''
  return value
}

const loadRecords = async (page?: number) => {
  isLoading.value = true
  try {
    const params = new URLSearchParams()
    params.set('page', String(page || currentPage.value))
    params.set('page_size', String(pageSize.value))
    const url = `/api/get_medicalchatrecods?${params.toString()}`
    const response = await fetch(url.startsWith('/api') ? window.VITE_GLOB_API_URL + url : url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    })
    const result = await response.json()
    if (result.code === 200) {
      records.value = (result.data || []).map((item: any) => ({
        id: item.id,
        promptTxt: item.prompt_txt || '',
        chatStart: item.chat_sdt_time ? formatTime(item.chat_sdt_time) : null,
        chatEnd: item.chat_edt_time ? formatTime(item.chat_edt_time) : null,
      }))
      total.value = result.total || 0
      totalPages.value = Math.ceil(total.value / pageSize.value)
    }
  } catch (error) {
    console.error('加载问诊记录失败:', error)
  } finally {
    isLoading.value = false
  }
}

const goToPage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  await loadRecords(page)
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

const deleteRecord = async (record: ChatRecord) => {
  if (!record?.id) return
  if (!confirm('是否要删除该问诊会话？')) return

  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/delete_medicalchatrecod', {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ id: record.id }),
    })
    const result = await response.json()
    if (result.code === 200) {
      if (records.value.length === 1 && currentPage.value > 1) {
        await goToPage(currentPage.value - 1)
      } else {
        await loadRecords(currentPage.value)
      }
      return
    }
    alert(result.message || '删除失败')
  } catch (error) {
    console.error('删除问诊记录失败:', error)
    alert('删除失败，请稍后重试')
  }
}

const formatAssistantMessage = (content: string) => {
  if (!content) return ''
  return marked(content) as string
}

const closeChatModal = () => {
  showChatModal.value = false
  chatMessages.value = []
}

const fetchChatMessages = async (chatId: string) => {
  const url = `/api/get_medicalchatrecod_messages?chat_id=${encodeURIComponent(chatId)}`
  const response = await fetch(url.startsWith('/api') ? window.VITE_GLOB_API_URL + url : url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  const result = await response.json()
  if (result.code !== 200) {
    throw new Error(result.message || '获取会话失败')
  }
  return result.data || []
}

const showRecord = async (record: ChatRecord) => {
  if (!record?.id) return
  try {
    const data = await fetchChatMessages(record.id)
    const list: ChatMessage[] = []
    data.forEach((item: any, index: number) => {
      const userText = (item.prompt_txt || '').trim()
      const assistantText = (item.result || '').trim()
      if (userText) {
        list.push({ id: `${item.id || index}-user`, role: 'user', content: userText })
      }
      if (assistantText) {
        list.push({ id: `${item.id || index}-assistant`, role: 'assistant', content: assistantText })
      }
    })
    chatMessages.value = list
    showChatModal.value = true
  } catch (error) {
    console.error('获取会话内容失败:', error)
    alert('获取会话内容失败，请稍后重试')
  }
}

const escapeHtml = (text: string) => {
  const map: { [key: string]: string } = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
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

const buildChatHtml = (messages: ChatMessage[], record: ChatRecord, userLabel: string) => {
  const messageBlocks = messages
    .map((msg) => {
      const label = msg.role === 'assistant' ? 'Ai体征分析助手' : userLabel
      const labelClass = msg.role === 'assistant' ? 'chat-label-assistant' : 'chat-label-user'
      const content = msg.role === 'assistant' ? marked(msg.content || '') : escapeHtml(msg.content || '')
      return `
        <div class="chat-line">
          <div class="chat-label ${labelClass}">${label}：</div>
          <div class="chat-body">${content}</div>
        </div>
      `
    })
    .join('')

  return `
    <html>
      <head>
        <meta charset="UTF-8" />
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
          h1 { text-align: center; margin-bottom: 10px; font-size: 24px; color: #4A90E2; }
          hr { border: none; border-top: 2px solid #333; margin: 15px 0; }
          .field { margin-bottom: 12px; }
          .label { font-weight: bold; }
          .chat-line { margin-bottom: 10px; }
          .chat-label { font-weight: bold; margin-bottom: 4px; }
          .chat-label-user { color: #4A90E2; }
          .chat-label-assistant { color: #4A90E2; }
          .user-name { color: #4A90E2; font-weight: bold; }
          .chat-body { background: #f9f9f9; padding: 8px 10px; border-left: 3px solid #4A90E2; }
          .chat-body p { margin: 0 0 6px 0; }
          .disclaimer { margin-top: 20px; padding-top: 20px; border-top: 1px solid #ccc; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <h1>Ai体征分析助手</h1>
        <hr />
        <div class="field">
          <span class="label">用户名称：</span>
          <span class="user-name">${userLabel}</span>
        </div>
        <div class="field">
          <span class="label">问诊编号：</span>
          <span>${record.id}</span>
        </div>
        <div class="field">
          <span class="label">开始时间：</span>
          <span>${record.chatStart ? `${record.chatStart.date} ${record.chatStart.time}` : '-'}</span>
        </div>
        <div class="field">
          <span class="label">结束时间：</span>
          <span>${record.chatEnd ? `${record.chatEnd.date} ${record.chatEnd.time}` : '-'}</span>
        </div>
        <div class="field">
          <span class="label">会话内容：</span>
        </div>
        ${messageBlocks || '<div>暂无内容</div>'}
        <div class="field">
          <span class="label">下载时间：</span>
          <span>${new Date().toLocaleString('zh-CN')}</span>
        </div>
        <div class="disclaimer" style="color: red;">
          注：本医学问诊结果为人工智能模型分析内容，不能替代正规医院诊断结果，请咨询专业医疗机构。
        </div>
      </body>
    </html>
  `
}

const downloadRecord = async (record: ChatRecord) => {
  if (!record?.id) return
  try {
    const data = await fetchChatMessages(record.id)
    const list: ChatMessage[] = []
    data.forEach((item: any, index: number) => {
      const userText = (item.prompt_txt || '').trim()
      const assistantText = (item.result || '').trim()
      if (userText) {
        list.push({ id: `${item.id || index}-user`, role: 'user', content: userText })
      }
      if (assistantText) {
        list.push({ id: `${item.id || index}-assistant`, role: 'assistant', content: assistantText })
      }
    })

    const currentUserName = userName.value || localStorage.getItem('user_account') || '用户'
    const htmlContent = buildChatHtml(list, record, currentUserName)

    const element = document.createElement('div')
    element.innerHTML = htmlContent

    const opt = {
      margin: 10,
      filename: `${currentUserName}_问诊记录_${new Date().getTime()}.pdf`,
      image: { type: 'jpeg' as const, quality: 0.98 },
      html2canvas: { scale: 1.0 },
      jsPDF: { orientation: 'portrait' as const, unit: 'mm', format: 'a4' },
    }

    const worker = html2pdf().set(opt).from(element).toPdf()
    const pdf = await worker.get('pdf')
    const blob = pdf.output('blob')

    if (isWeChatBrowser()) {
      const dataUrl = await blobToDataUrl(blob)
      const response = await fetch(window.VITE_GLOB_API_URL + '/api/upload_medicalchatrecord_pdf', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
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
    console.error('下载问诊记录失败:', error)
    alert('下载失败，请稍后再试')
  }
}

onMounted(async () => {
  const isLogged = checkLogin()
  isLoggedIn.value = isLogged
  if (isLogged) {
    const cachedAvatar = localStorage.getItem('user_avatar')
    if (cachedAvatar) {
      userAvatar.value = cachedAvatar.startsWith('data:image')
        ? cachedAvatar
        : `data:image/png;base64,${cachedAvatar}`
    } else {
      userAvatar.value = defaultAvatar
    }
    userName.value = localStorage.getItem('user_account') || ''
    await loadRecords()
  } else {
    userAvatar.value = defaultAvatar
    router.push('/login')
  }
})
</script>

<style scoped>
.medical-chat-record-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: 124px;
  background-color: #f5f5f5;
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
  overflow-x: auto;
  margin-top: 10px;
}

.record-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  min-width: 720px;
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
  word-break: break-word;
}

.col-index {
  width: 50px;
  min-width: 50px;
  text-align: center;
}

.col-time {
  width: 100px;
  min-width: 80px;
  text-align: center;
}

.col-actions {
  width: 80px;
  min-width: 80px;
}

.record-table tbody tr:hover {
  background-color: #f8f9fa;
}

.record-table tbody tr:last-child td {
  border-bottom: none;
}

.delete-btn {
  padding: 6px 16px;
  background-color: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
  height: 30px;
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
  font-size: 13px;
  transition: all 0.3s;
  height: 30px;
}

.download-btn:hover {
  background-color: #357ABD;
}

.download-btn:active {
  background-color: #2d5ca8;
}

.show-btn {
  padding: 6px 16px;
  background-color: #10b981;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
  height: 30px;
}

.show-btn:hover {
  background-color: #0f9a6f;
}

.show-btn:active {
  background-color: #0b7c58;
}

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
  background-color: #fff;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  min-width: 40px;
  padding: 8px 16px;
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

.chat-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
}

.chat-modal-content {
  width: min(960px, 92vw);
  height: auto;
  max-height: min(550px, 85vh);
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.chat-modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.chat-modal-close-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.consultation-tab {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0;
  overflow: hidden;
  flex: 1;
}

.consultation-result {
  min-height: 0;
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 0;
  border-left: none;
  border-right: none;
  background-color: #fafafa;
  box-sizing: border-box;
  max-height: none;
  overflow-y: auto;
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

@media (max-width: 640px) {
  .medical-chat-record-container {
    padding: 20px;
    padding-bottom: 124px;
  }

  .table-wrapper {
    border-radius: 6px;
  }

  .chat-modal-content {
    width: 94vw;
  }
  
  .nav-btn {
    padding: 10px;
    font-size: 14px;
    gap: 4px;
  }

  .record-table th,
  .record-table td {
    font-size: 12px;
    padding: 8px 6px;
  }

  .record-table {
    min-width: 640px;
  }

  .pagination-controls {
    gap: 4px;
  }

  .pagination-btn {
    padding: 6px 12px;
    font-size: 12px;
    min-width: 36px;
  }
}
</style>
