import { ref, computed } from 'vue'
import { loginUser, logoutUser, getToken, setToken, removeToken } from '@/api/auth'

// 登录状态
const isLoggedIn = ref<boolean>(false)
// 用户信息
const userInfo = ref<{
  user_id?: number
  user_account?: string
}>({})

// 从 localStorage 读取登录状态和用户信息
const loadAuthState = () => {
  const token = getToken()
  const savedUserId = localStorage.getItem('user_id')
  const savedUserAccount = localStorage.getItem('user_account')
  
  if (token && savedUserAccount) {
    isLoggedIn.value = true
    userInfo.value = {
      user_id: savedUserId ? Number(savedUserId) : undefined,
      user_account: savedUserAccount,
    }
  }
}

// 初始化时加载状态
loadAuthState()

export const useAuth = () => {
  const login = async (username: string, password: string): Promise<{ success: boolean; message: string }> => {
    try {
      const result = await loginUser({
        user: username,
        pwd: password,
      })
      // 严格检查：只有 code 明确为 200 且有 data 且有 token 时才认为登录成功
      if (result && result.code === 200 && result.data && result.data.token) {
        // 登录成功，保存 token 和用户信息
        setToken(result.data.token)
        localStorage.setItem('user_id', String(result.data.user_id))
        localStorage.setItem('user_account', result.data.user_account)
        if (result.data.session_id) {
          localStorage.setItem('session_id', result.data.session_id)
        }
        
        isLoggedIn.value = true
        userInfo.value = {
          user_id: result.data.user_id,
          user_account: result.data.user_account,
        }
        
        return {
          success: true,
          message: result.message || '登录成功',
        }
      } else {
        // 登录失败：code 不是 200，或者没有 data，或者没有 token
        const errorMessage = result?.message || `登录失败，错误码: ${result?.code || '未知'}`
        return {
          success: false,
          message: errorMessage,
        }
      }
    } catch (error) {
      console.error('登录异常:', error)
      return {
        success: false,
        message: '登录失败，请稍后重试',
      }
    }
  }

  const register = async (username: string, password: string): Promise<void> => {
    // 注册功能已在 RegisterUser.vue 中实现
    // 这里保留接口以保持兼容性
  }

  const logout = async (): Promise<{ success: boolean; message: string }> => {
    try {
      // 调用退出接口
      const result = await logoutUser()
      
      // 无论接口是否成功，都清除本地状态
      isLoggedIn.value = false
      userInfo.value = {}
      removeToken()
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_account')
      localStorage.removeItem('session_id')
      localStorage.removeItem('isLoggedIn')
      localStorage.removeItem('username')
      
      if (result.code === 200) {
        return {
          success: true,
          message: result.message || '退出成功',
        }
      } else {
        // 即使接口失败，本地状态已清除，也算退出成功
        return {
          success: true,
          message: '已退出登录',
        }
      }
    } catch (error) {
      console.error('退出失败:', error)
      // 即使接口失败，也清除本地状态
      isLoggedIn.value = false
      userInfo.value = {}
      removeToken()
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_account')
      localStorage.removeItem('session_id')
      localStorage.removeItem('isLoggedIn')
      localStorage.removeItem('username')
      
      return {
        success: true,
        message: '已退出登录',
      }
    }
  }

  const checkLogin = (): boolean => {
    return isLoggedIn.value && !!getToken()
  }

  const getUserInfo = () => {
    return userInfo.value
  }

  return {
    isLoggedIn: computed(() => isLoggedIn.value),
    userInfo: computed(() => userInfo.value),
    login,
    register,
    logout,
    checkLogin,
    getUserInfo,
  }
}
