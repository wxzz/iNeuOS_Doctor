//import axios from 'axios'

//const API_BASE_URL = 'http://localhost:5000/api'

const MEDICAL_ANALYSIS_TIMEOUT_MS = 15 * 60 * 1000

const fetchWithTimeout = async (
  input: RequestInfo | URL,
  init: RequestInit,
  timeoutMs: number
) => {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal
    })
  } finally {
    window.clearTimeout(timeoutId)
  }
}

// 提交诊断
export const submitDiagnosis = async (data: {
  prompt_txt: string
  image_data?: string
}) => {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('未登录')
  }

  let response: Response
  try {
    response = await fetchWithTimeout(
      window.VITE_GLOB_API_URL + `/api/medical`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      },
      MEDICAL_ANALYSIS_TIMEOUT_MS
    )
  } catch (error: any) {
    if (error?.name === 'AbortError') {
      throw new Error('分析请求超时，请稍后到[ 分析记录 ]查看结果')
    }
    throw error
  }

  const responseText = await response.text()
  let result: any = null
  try {
    result = responseText ? JSON.parse(responseText) : null
  } catch (error) {
    result = {
      code: response.status,
      message: responseText || response.statusText || `请求失败，状态码: ${response.status}`
    }
  }

  if (!result || typeof result !== 'object') {
    result = {
      code: response.status,
      message: response.statusText || `请求失败，状态码: ${response.status}`
    }
  }

  if (!result.code) {
    result.code = response.status
  }

  // 无论 HTTP 状态码如何，都返回接口的业务结果，交由调用方判断 code
  return result
}

// 病情问诊
export const submitMedicalConsultationStream = async (data: {
  prompt_txt: string
  deep_thinking?: boolean
}) => {
  const token = localStorage.getItem('token')
  const sessionId = localStorage.getItem('session_id')
  if (!token) {
    throw new Error('未登录')
  }
  if (!sessionId) {
    throw new Error('缺少session_id')
  }

  return fetch(window.VITE_GLOB_API_URL + `/api/medical_chat`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ...data,
      session_id: sessionId
    })
  })
}

// 病情问诊OCR（附件识别）
export const submitMedicalChatOcr = async (file: File) => {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('未登录')
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(window.VITE_GLOB_API_URL + `/api/medical_chat_ocr`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  })

  let result: any = null
  try {
    result = await response.json()
  } catch (error) {
    throw error
  }

  return result
}