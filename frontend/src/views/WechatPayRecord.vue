<template>
  <div class="wechat-pay-record-container">
    <TitleBar
      title="赞助记录"
      :is-logged-in="isLoggedIn"
      :user-avatar="userAvatar"
      :user-status-title="userStatusTitle"
      @status-click="handleUserStatusClick"
    />
    
    <!-- 加载提示 -->
    <div v-if="isLoading" class="message-box">
      <p>正在获取数据...</p>
    </div>
    
    <!-- 空数据提示 -->
    <div v-else-if="!isLoading && records.length === 0" class="message-box">
      <p>当前没有赞助记录</p>
    </div>
    
    <!-- 表格区域 -->
    <div v-else class="table-wrapper">
      <table class="record-table">
        <thead>
          <tr>
            <th class="serial-col">序号</th>
            <th class="trade-no-col">订单号</th>
            <th class="credit-col">赞助算力点</th>
            <th class="desc-col">赞助描述</th>
            <th class="success-time-col">赞助时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(record, index) in records" :key="index">
            <td class="center serial-col">{{ (currentPage - 1) * pageSize + index + 1 }}</td>
            <td class="center trade-no-col">{{ record.out_trade_no }}</td>
            <td class="right credit-col">{{ Number(record.payer_total / 100).toFixed(2) }}</td>
            <td class="center desc-col">{{ record.trade_state_desc }}</td>
            <td class="center success-time-col">{{ formatDateTime(record.success_time) }}</td>
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

    <BottomNav active="pay" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
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
  out_trade_no: string
  trade_state_desc: string
  success_time: string
  payer_total: number
}

const records = ref<Record[]>([])
const isLoading = ref(false)

// 分页相关状态
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(0)

onMounted(async () => {
  console.log('WechatPayRecord页面已挂载')
  const isLogged = checkLogin()
  isLoggedIn.value = isLogged
  if (isLogged) {
    const cachedAvatar = localStorage.getItem('user_avatar')
    if (cachedAvatar) {
      userAvatar.value = cachedAvatar.startsWith('data:image') ? cachedAvatar : `data:image/png;base64,${cachedAvatar}`
    } else {
      userAvatar.value = defaultAvatar
    }
    console.log('用户已登录，开始加载赞助记录')
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
}*/

const handleUserStatusClick = () => {
  if (isLoggedIn.value) {
    router.push('/my-info')
  } else {
    router.push('/login')
  }
}

const loadRecords = async (page?: number) => {
  isLoading.value = true
  try {
    const pageNum = page || currentPage.value
    const token = localStorage.getItem('token')
    if (!token) {
      console.error('未找到认证token')
      router.push('/login')
      return
    }

    const url = `/api/wechat_pay_record?page=${pageNum}&page_size=${pageSize.value}`
    console.log('请求URL:', url)
    console.log('请求Token:', token ? '存在' : '不存在')

    const response = await fetch(url.startsWith('/api') ? window.VITE_GLOB_API_URL + url : url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    console.log('响应状态:', response.status, response.statusText)

    if (!response.ok) {
      console.error('API响应错误:', response.status, response.statusText)
      const errorText = await response.text()
      console.error('错误详情:', errorText)
      return
    }

    const result = await response.json()
    console.log('API返回数据:', result)

    if (result.code === 200) {
      records.value = result.data.records || []
      total.value = result.data.total || 0
      currentPage.value = pageNum
      totalPages.value = Math.ceil(total.value / pageSize.value)
      console.log('赞助记录加载成功，共', total.value, '条，当前页记录数：', records.value.length)
    } else {
      console.error('获取数据失败:', result.message)
      alert(`获取数据失败：${result.message}`)
    }
  } catch (error) {
    console.error('加载赞助记录失败:', error)
    alert(`加载赞助记录失败：${error}`)
  } finally {
    isLoading.value = false
  }
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const goToPage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return
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

</script>

<style scoped>
.wechat-pay-record-container {
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
  overflow-x: auto;
  overflow-y: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-top: 10px;
}

.record-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  min-width: 600px;
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
}

.record-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #e0e0e0;
  border-right: 1px solid #e0e0e0;
  color: #333;
}

.record-table tbody tr:hover {
  background-color: #f8f9fa;
}

.record-table tbody tr:last-child td {
  border-bottom: none;
}

.center {
  text-align: center;
}

.right {
  text-align: right;
}

.serial-col {
  width: 50px;
  max-width: 50px;
}

.trade-no-col {
  width: 110px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.success-time-col {
  width: 130px;
  max-width: 170px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.desc-col {
  width: 80px;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.credit-col {
  width: 90px;
  max-width: 90px;
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

@media (max-width: 640px) {
  .wechat-pay-record-container {
    padding: 20px;
    padding-bottom: 124px;
  }

  .table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: 6px;
  }

  .record-table {
    min-width: 550px;
    font-size: 12px;
  }

  .record-table th,
  .record-table td {
    padding: 10px 6px;
  }

  .pagination-controls {
    gap: 4px;
  }
  
  .pagination-btn {
    padding: 6px 12px;
    font-size: 12px;
    min-width: 36px;
  }

  .nav-btn {
    padding: 10px;
    font-size: 14px;
    gap: 4px;
  }

  .business-menu {
    bottom: 100%;
  }

  .menu-item {
    padding: 12px 12px;
    font-size: 14px;
  }
}
</style>
