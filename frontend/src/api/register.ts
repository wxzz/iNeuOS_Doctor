/**
 * 用户注册 API
 */

export interface RegisterRequest {
  user: string
  pwd1: string
  pwd2: string
  invite?: string
  phone: string
  sms_code: string
  is_user_license: boolean
}

export interface RegisterResponse {
  code: number
  message: string
  data: Record<string, any>
}

export interface SendVerifyCodeResponse {
  code: number
  message: string
  data?: Record<string, any>
}

/**
 * 注册用户
 * @param data 注册数据
 * @returns 注册结果
 */
export async function registerUser(data: RegisterRequest): Promise<RegisterResponse> {
  try {
    const url = data.invite
      ? `/api/register_user?invite=${encodeURIComponent(data.invite)}`
      : '/api/register_user'

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: data.user,
        pwd1: data.pwd1,
        pwd2: data.pwd2,
        phone: data.phone,
        sms_code: data.sms_code,
        is_user_license: data.is_user_license,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result: RegisterResponse = await response.json()
    return result
  } catch (error) {
    console.error('注册请求失败:', error)
    return {
      code: 500,
      message: '注册失败：网络错误',
      data: {},
    }
  }
}

/**
 * 发送短信验证码（5分钟内有效）
 */
export async function sendVerifySmsCode(phone: string): Promise<SendVerifyCodeResponse> {
  try {
    const response = await fetch('/api/send_verify_sms_code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phone }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result: SendVerifyCodeResponse = await response.json()
    return result
  } catch (error) {
    console.error('发送验证码请求失败:', error)
    return {
      code: 500,
      message: '发送失败：网络错误',
      data: {},
    }
  }
}
