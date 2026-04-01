// index.ts
// 获取应用实例
const app = getApp<IAppOption>()
const defaultAvatarUrl = 'https://mmbiz.qpic.cn/mmbiz/icTdbqWNOwNRna42FI242Lcia07jQodd2FJGIYQfG0LAJGFxM4FbnQP6yfMxBgJ0F3YRqJCJ1aPAK2dQagdusBZg/0'

console.log('[MiniPay] index.ts loaded')

Page({
  data: {
    motto: 'Hello World',
    userInfo: {
      avatarUrl: defaultAvatarUrl,
      nickName: '',
    },
    hasUserInfo: false,
    canIUseGetUserProfile: wx.canIUse('getUserProfile'),
    canIUseNicknameComp: wx.canIUse('input.type.nickname'),
    webviewSrc: 'https://www.aineuos.net',
    //webviewSrc: 'https://359mn0dl4988.vicp.fun'
  },

  onLoad(options: Record<string, string>) {
    console.log('[MiniPay] index onLoad')
    const rawBaseUrl = this.data.webviewSrc
    const h5Path = options && options.h5Path ? decodeURIComponent(options.h5Path) : ''
    const baseUrl = h5Path
      ? rawBaseUrl.replace(/\/$/, '') + h5Path
      : rawBaseUrl
    const params: Record<string, string> = {
      isMiniProgram: '1'
    }

    if (options && options.withdrawStatus) {
      params.withdrawStatus = options.withdrawStatus
    }
    if (options && options.outBillNo) {
      params.outBillNo = options.outBillNo
    }
    if (options && options.errMsg) {
      params.errMsg = options.errMsg
    }

    const query = Object.keys(params)
      .map((key) => `${key}=${encodeURIComponent(params[key] || '')}`)
      .join('&')
    const fullUrl = baseUrl + (baseUrl.includes('?') ? '&' : '?') + query

    this.setData({
      webviewSrc: fullUrl
    })
  },
  onReady() {
    console.log('[MiniPay] index onReady')
    // 缓存 web-view 组件实例用于回传支付结果
    // @ts-ignore
  },

  onWebviewLoad(e: any) {
    // @ts-ignore
    console.log('[MiniPay] WebView load:', e)
  },
  onWebviewError(e: any) {
    console.error('[MiniPay] WebView error:', e)
  },

  onWebviewMessage(e: any) {
    const detail = e && e.detail ? e.detail : null
    const dataList = detail && detail.data ? detail.data : []
    const payload = dataList && dataList.length ? dataList[0] : null
    console.log('[MiniPay] WebView message:', payload)

    if (payload && payload.action === 'openPdf') {
      const url = payload.url
      if (!url) {
        wx.showModal({
          title: '打开失败',
          content: '下载链接为空，请重试。',
          showCancel: false
        })
        return
      }

      wx.downloadFile({
        url,
        success: (res) => {
          if (res.statusCode !== 200) {
            wx.showModal({
              title: '下载失败',
              content: `下载失败（HTTP ${res.statusCode}）`,
              showCancel: false
            })
            return
          }
          wx.openDocument({
            filePath: res.tempFilePath,
            showMenu: true,
            fail: (err) => {
              const msg = err && (err as any).errMsg ? (err as any).errMsg : '打开文件失败'
              wx.showModal({
                title: '打开失败',
                content: msg,
                showCancel: false
              })
            }
          })
        },
        fail: (err) => {
          const msg = err && (err as any).errMsg ? (err as any).errMsg : '下载失败'
          wx.showModal({
            title: '下载失败',
            content: msg,
            showCancel: false
          })
        }
      })
      return
    }
    /*
    if (payload && payload.action === 'miniWithdraw') {
      // @ts-ignore
      if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
        ;(this as any).webviewRef.postMessage({
          data: {
            action: 'miniWithdrawAck'
          }
        })
      }

      const realName = payload.realName
      const amount = payload.amount
      const token = payload.token
      const apiBase = payload.apiBase

      if (!apiBase || !token) {
        // @ts-ignore
        if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
          ;(this as any).webviewRef.postMessage({
            data: {
              action: 'miniWithdrawResult',
              status: 'fail',
              errMsg: !apiBase ? '缺少 apiBase' : '缺少 token'
            }
          })
        }
        return
      }

      wx.request({
        url: apiBase + '/api/wechat_withdraw',
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        data: {
          real_name: realName,
          amount: amount
        },
        success: (res: any) => {
          const data = res && res.data ? res.data : null
          if (!data || (data.code !== 200 && !data.success)) {
            const errMsg = (data && (data.message || data.error)) || '提现申请失败'
            // @ts-ignore
            if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
              ;(this as any).webviewRef.postMessage({
                data: {
                  action: 'miniWithdrawResult',
                  status: 'fail',
                  errMsg
                }
              })
            }
            return
          }

          const outBillNo = data && data.data ? data.data.out_bill_no : null
          if (outBillNo) {
            // @ts-ignore
            if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
              ;(this as any).webviewRef.postMessage({
                data: {
                  action: 'miniWithdrawResult',
                  status: 'created',
                  outBillNo
                }
              })
            }
          }

          if (data.data && data.data.package_info && data.data.state === 'WAIT_USER_CONFIRM') {
            const requestMerchantTransfer = (wx as any).requestMerchantTransfer
            if (!requestMerchantTransfer) {
              // @ts-ignore
              if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
                ;(this as any).webviewRef.postMessage({
                  data: {
                    action: 'miniWithdrawResult',
                    status: 'fail',
                    errMsg: '微信版本过低，不支持确认收款'
                  }
                })
              }
              return
            }

            requestMerchantTransfer({
              mchId: data.data.mch_id || '',
              appId: data.data.appid || '',
              package: data.data.package_info,
              success: () => {
                // @ts-ignore
                if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
                  ;(this as any).webviewRef.postMessage({
                    data: {
                      action: 'miniWithdrawResult',
                      status: 'success',
                      outBillNo
                    }
                  })
                }
              },
              fail: (err: any) => {
                const errMsg = err && err.errMsg ? err.errMsg : '确认收款失败'
                // @ts-ignore
                if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
                  ;(this as any).webviewRef.postMessage({
                    data: {
                      action: 'miniWithdrawResult',
                      status: 'fail',
                      errMsg
                    }
                  })
                }
              }
            })
          }
        },
        fail: (err) => {
          const errMsg = err && err.errMsg ? err.errMsg : '提现请求失败'
          // @ts-ignore
          if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
            ;(this as any).webviewRef.postMessage({
              data: {
                action: 'miniWithdrawResult',
                status: 'fail',
                errMsg
              }
            })
          }
        }
      })
      return
    }
    if (!payload || payload.action !== 'miniPay') {
      return
    }

    // 先回传收到消息，避免 WebView 侧超时
    // @ts-ignore
    if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
      ;(this as any).webviewRef.postMessage({
        data: {
          action: 'miniPayAck'
        }
      })
    }

    const amount = payload.amount
    const token = payload.token
    const apiBase = payload.apiBase

    if (!apiBase) {
      wx.showModal({
        title: '支付失败',
        content: '缺少 apiBase，请检查 WebView 传参',
        showCancel: false
      })
      // @ts-ignore
      if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
        ;(this as any).webviewRef.postMessage({
          data: {
            action: 'miniPayResult',
            status: 'fail',
            errMsg: '缺少 apiBase'
          }
        })
      }
      return
    }

    if (!token) {
      wx.showModal({
        title: '支付失败',
        content: '缺少登录 token，请重新登录',
        showCancel: false
      })
      // @ts-ignore
      if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
        ;(this as any).webviewRef.postMessage({
          data: {
            action: 'miniPayResult',
            status: 'fail',
            errMsg: '缺少 token'
          }
        })
      }
      return
    }

    wx.login({
      success: (loginRes) => {
        console.log('[MiniPay] wx.login result:', loginRes)
        if (!loginRes.code) {
          // @ts-ignore
          if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
            ;(this as any).webviewRef.postMessage({
              data: {
                action: 'miniPayResult',
                status: 'fail',
                errMsg: '获取登录code失败'
              }
            })
          }
          return
        }

        console.log('[MiniPay] request mini pay:', { apiBase, amount })

        wx.request({
          url: apiBase + '/api/wechat_jsapi_pay',
          method: 'POST',
          header: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          data: {
            pay_amount: amount,
            code: loginRes.code
          },
          success: (res: any) => {
            console.log('[MiniPay] mini pay response:', res)
            const data = res && res.data ? res.data : null
            if (!data || !data.success || !data.result) {
              const errMsg = (data && (data.error || data.message)) || '下单失败'
              // @ts-ignore
              if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
                ;(this as any).webviewRef.postMessage({
                  data: {
                    action: 'miniPayResult',
                    status: 'fail',
                    errMsg
                  }
                })
              }
              return
            }

            const params = data.result || {}
            const orderNo = data.out_trade_no
            // @ts-ignore
            if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function' && orderNo) {
              ;(this as any).webviewRef.postMessage({
                data: {
                  action: 'miniPayResult',
                  status: 'created',
                  orderNo
                }
              })
            }

            wx.requestPayment({
              timeStamp: String(params.timeStamp || ''),
              nonceStr: params.nonceStr || '',
              package: params.package || '',
              signType: params.signType || 'MD5',
              paySign: params.paySign || '',
              success: (payRes) => {
                // @ts-ignore
                if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
                  ;(this as any).webviewRef.postMessage({
                    data: {
                      action: 'miniPayResult',
                      status: 'success',
                      res: payRes
                    }
                  })
                }
              },
              fail: (err) => {
                const errMsg = err && err.errMsg ? err.errMsg : ''
                const isCancel = typeof errMsg === 'string' && errMsg.includes('cancel')
                // @ts-ignore
                if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
                  ;(this as any).webviewRef.postMessage({
                    data: {
                      action: 'miniPayResult',
                      status: isCancel ? 'cancel' : 'fail',
                      errMsg
                    }
                  })
                }
              }
            })
          },
          fail: (err) => {
            const errMsg = err && err.errMsg ? err.errMsg : '下单请求失败'
            wx.showModal({
              title: '支付失败',
              content: errMsg,
              showCancel: false
            })
            // @ts-ignore
            if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
              ;(this as any).webviewRef.postMessage({
                data: {
                  action: 'miniPayResult',
                  status: 'fail',
                  errMsg
                }
              })
            }
          }
        })
      },
      fail: () => {
        // @ts-ignore
        if ((this as any).webviewRef && typeof (this as any).webviewRef.postMessage === 'function') {
          ;(this as any).webviewRef.postMessage({
            data: {
              action: 'miniPayResult',
              status: 'fail',
              errMsg: '登录失败'
            }
          })
        }
      }
    })*/
  },
  // 事件处理函数
  bindViewTap() {
    wx.navigateTo({
      url: '../logs/logs',
    })
  },
  onChooseAvatar(e: any) {
    const { avatarUrl } = e.detail
    const { nickName } = this.data.userInfo
    this.setData({
      "userInfo.avatarUrl": avatarUrl,
      hasUserInfo: nickName && avatarUrl && avatarUrl !== defaultAvatarUrl,
    })
  },
  onInputChange(e: any) {
    const nickName = e.detail.value
    const { avatarUrl } = this.data.userInfo
    this.setData({
      "userInfo.nickName": nickName,
      hasUserInfo: nickName && avatarUrl && avatarUrl !== defaultAvatarUrl,
    })
  },
  getUserProfile() {
    // 推荐使用wx.getUserProfile获取用户信息，开发者每次通过该接口获取用户个人信息均需用户确认，开发者妥善保管用户快速填写的头像昵称，避免重复弹窗
    wx.getUserProfile({
      desc: '展示用户信息', // 声明获取用户个人信息后的用途，后续会展示在弹窗中，请谨慎填写
      success: (res) => {
        console.log(res)
        this.setData({
          userInfo: res.userInfo,
          hasUserInfo: true
        })
      }
    })
  },
})
