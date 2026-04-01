/**
 * 用户认证 API
 */

export interface LoginRequest {
  user: string
  pwd: string
}

export interface LoginResponse {
  code: number
  message: string
  data?: {
    token: string
    user_id: number
    user_account: string
    session_id:string
  }
}

export interface LogoutResponse {
  code: number
  message: string
}

export interface ChangePasswordRequest {
  user: string
  old_pwd: string
  new_pwd: string
}

export interface ChangePasswordResponse {
  code: number
  message: string
}

export interface GetMyInfoResponse {
  code: number
  message: string
  data?: {
    user_account: string
    account_credit: number
    create_time: string
    last_login_time: string
    status: string
    mobile: string
    email: string
    avatar: string
    medical_count: number
    cost_sum: number
    cash: number
  }
}

export interface UpdateAvatarRequest {
  image_data: string // base64 or data URL
}

export interface UpdateAvatarResponse {
  code: number
  message: string
  data?: {
    avatar: string
  }
}

export interface GenerateInviteResponse {
  code: number
  message: string
  data?: {
    invite_code: string
    invite_link: string
    invite_create_time?: string
    invite_count?: number
    increase_cost_total?: number
  }
}

/**
 * 获取存储的 token
 */
export function getToken(): string | null {
  return localStorage.getItem('token')
}

/**
 * 设置 token
 */
export function setToken(token: string): void {
  localStorage.setItem('token', token)
}

/**
 * 移除 token
 */
export function removeToken(): void {
  localStorage.removeItem('token')
}

/**
 * 获取请求头（带 token）
 */
export function getAuthHeaders(): HeadersInit {
  const token = getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

/**
 * 用户登录
 * @param data 登录数据
 * @returns 登录结果
 */
export async function loginUser(data: LoginRequest): Promise<LoginResponse> {
  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/login_user', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: data.user,
        pwd: data.pwd,
      }),
    })

    let result: LoginResponse
    try {
      result = await response.json()
    } catch (e) {
      // 如果响应不是有效的JSON，使用HTTP状态码和状态文本
      result = {
        code: response.status,
        message: response.statusText || `请求失败，状态码: ${response.status}`
      }
    }
    
    // 如果JSON中没有code，使用HTTP状态码
    if (!result.code) {
      result.code = response.status
    }
    
    return result
  } catch (error) {
    console.error('登录请求失败:', error)
    return {
      code: 500,
      message: '网络错误，请稍后重试',
    }
  }
}

/**
 * 用户退出
 * @returns 退出结果
 */
export async function logoutUser(): Promise<LogoutResponse> {
  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/login_out', {
      method: 'POST',
      headers: getAuthHeaders(),
    })

    let result: LogoutResponse
    try {
      result = await response.json()
    } catch (e) {
      // 如果响应不是有效的JSON，使用HTTP状态码和状态文本
      result = {
        code: response.status,
        message: response.statusText || `请求失败，状态码: ${response.status}`
      }
    }
    
    // 如果JSON中没有code，使用HTTP状态码
    if (!result.code) {
      result.code = response.status
    }
    
    return result
  } catch (error) {
    console.error('退出请求失败:', error)
    return {
      code: 500,
      message: '网络错误，请稍后重试',
    }
  }
}

/**
 * 修改密码
 * @param data 修改密码数据
 * @returns 修改结果
 */
export async function changePassword(data: ChangePasswordRequest): Promise<ChangePasswordResponse> {
  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/change_password', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        user: data.user,
        old_pwd: data.old_pwd,
        new_pwd: data.new_pwd,
      }),
    })

    let result: ChangePasswordResponse
    try {
      result = await response.json()
    } catch (e) {
      // 如果响应不是有效的JSON，使用HTTP状态码和状态文本
      result = {
        code: response.status,
        message: response.statusText || `请求失败，状态码: ${response.status}`
      }
    }
    
    // 如果JSON中没有code，使用HTTP状态码
    if (!result.code) {
      result.code = response.status
    }
    
    return result
  } catch (error) {
    console.error('修改密码请求失败:', error)
    return {
      code: 500,
      message: '网络错误，请稍后重试',
    }
  }
}

/**
 * 获取我的信息
 * @returns 我的信息结果
 */
export async function getMyInfo(): Promise<GetMyInfoResponse> {
  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/get_myinfo', {
      method: 'GET',
      headers: getAuthHeaders(),
    })

    let result: GetMyInfoResponse
    try {
      result = await response.json()
    } catch (e) {
      // 如果响应不是有效的JSON，使用HTTP状态码和状态文本
      result = {
        code: response.status,
        message: response.statusText || `请求失败，状态码: ${response.status}`
      }
    }
    
    // 如果JSON中没有code，使用HTTP状态码
    if (!result.code) {
      result.code = response.status
    }
    
    return result
  } catch (error) {
    console.error('获取我的信息请求失败:', error)
    return {
      code: 500,
      message: '网络错误，请稍后重试',
    }
  }
}

/**
 * 更新头像
 */
export async function updateAvatar(data: UpdateAvatarRequest): Promise<UpdateAvatarResponse> {
  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/update_avatar', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        image_data: data.image_data,
      }),
    })

    let result: UpdateAvatarResponse
    try {
      result = await response.json()
    } catch (e) {
      result = {
        code: response.status,
        message: response.statusText || `请求失败，状态码: ${response.status}`
      }
    }

    if (!result.code) {
      result.code = response.status
    }

    return result
  } catch (error) {
    console.error('更新头像请求失败:', error)
    return {
      code: 500,
      message: '网络错误，请稍后重试',
    }
  }
}

/**
 * 生成邀请码与邀请链接
 */
export async function generateInviteCode(): Promise<GenerateInviteResponse> {
  try {
    const response = await fetch(window.VITE_GLOB_API_URL + '/api/generate_invite_code', {
      method: 'GET',
      headers: getAuthHeaders(),
    })

    let result: GenerateInviteResponse
    try {
      result = await response.json()
    } catch (e) {
      result = {
        code: response.status,
        message: response.statusText || `请求失败，状态码: ${response.status}`
      }
    }

    if (!result.code) {
      result.code = response.status
    }

    return result
  } catch (error) {
    console.error('生成邀请码请求失败:', error)
    return {
      code: 500,
      message: '网络错误，请稍后重试',
    }
  }
}
