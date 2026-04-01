Page({
  data: {
    loading: true
  },
  onLoad(options: Record<string, string>) {
    console.log('[Withdraw] onLoad options:', options)
    this.startWithdraw(options)
  },
  startWithdraw(options: Record<string, string>) {
    const realName = decodeURIComponent(options.realName || '')
    const amount = Number(options.amount || 0)
    const token = options.token || ''
    const apiBase = decodeURIComponent(options.apiBase || '')

    if (!realName || !amount || !apiBase || !token) {
      this.returnToWebview('fail', '', '参数不完整')
      return
    }
    console.log('[Withdraw] startWithdraw:', { realName, amount, apiBase })

    wx.login({
      success: (loginRes) => {
        const miniCode = loginRes && loginRes.code ? loginRes.code : ''
        console.log('[Withdraw] wx.login result:', loginRes)
        if (!miniCode) {
          this.returnToWebview('fail', '', '获取登录code失败')
          return
        }

        const requestData = {
          real_name: realName,
          amount: amount,
          code: miniCode,
          pay_scene: 'mini'
        }

        console.log('[Withdraw] request payload:', requestData)

        wx.request({
          url: apiBase + '/api/wechat_withdraw',
          method: 'POST',
          header: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          data: requestData,
          success: (res: any) => {
            console.log('[Withdraw] withdraw response:', res)
            const data = res && res.data ? res.data : null
            if (!data || (data.code !== 200 && !data.success)) {
              const errMsg = (data && (data.message || data.error)) || '提现申请失败'
              wx.showModal({
                title: '提现失败',
                content: errMsg,
                showCancel: false
              })
              this.returnToWebview('fail', '', errMsg)
              return
            }

            const outBillNo = data && data.data ? data.data.out_bill_no : ''
            const state = data && data.data ? data.data.state : ''
            console.log('[Withdraw] withdraw state:', state)

            if (data.data && data.data.package_info && data.data.state === 'WAIT_USER_CONFIRM') {
              const requestMerchantTransfer = (wx as any).requestMerchantTransfer
              if (!requestMerchantTransfer) {
                wx.showModal({
                  title: '提示',
                  content: '微信版本过低，不支持确认收款',
                  showCancel: false
                })
                this.returnToWebview('fail', outBillNo, '微信版本过低，不支持确认收款')
                return
              }

              console.log('[Withdraw] calling requestMerchantTransfer')
              requestMerchantTransfer({
                mchId: data.data.mch_id || '',
                appId: data.data.appid || '',
                package: data.data.package_info,
                success: () => {
                  this.returnToWebview('success', outBillNo, '')
                },
                fail: (err: any) => {
                  console.error('[Withdraw] requestMerchantTransfer failed:', err)
                  wx.showModal({
                    title: '确认收款失败',
                    content: (err && err.errMsg) || '确认收款失败',
                    showCancel: false
                  })
                  const errMsg = err && err.errMsg ? err.errMsg : '确认收款失败'
                  this.returnToWebview('fail', outBillNo, errMsg)
                }
              })
              return
            }

            wx.showModal({
              title: '未触发确认收款',
              content: `state=${state || 'unknown'}`,
              showCancel: false
            })
            this.returnToWebview('created', outBillNo, '')
          },
          fail: (err: any) => {
            const errMsg = err && err.errMsg ? err.errMsg : '提现请求失败'
            wx.showModal({
              title: '提现请求失败',
              content: errMsg,
              showCancel: false
            })
            this.returnToWebview('fail', '', errMsg)
          }
        })
      },
      fail: (err) => {
        console.error('[Withdraw] wx.login failed:', err)
        this.returnToWebview('fail', '', '登录失败')
      }
    })
  },
  returnToWebview(status: string, outBillNo: string, errMsg: string) {
    const params: string[] = []
    params.push(`h5Path=${encodeURIComponent('/my-info')}`)
    if (status) {
      params.push(`withdrawStatus=${encodeURIComponent(status)}`)
    }
    if (outBillNo) {
      params.push(`outBillNo=${encodeURIComponent(outBillNo)}`)
    }
    if (errMsg) {
      params.push(`errMsg=${encodeURIComponent(errMsg)}`)
    }

    const query = params.length ? `?${params.join('&')}` : ''
    wx.redirectTo({
      url: `/pages/index/index${query}`
    })
  }
})
