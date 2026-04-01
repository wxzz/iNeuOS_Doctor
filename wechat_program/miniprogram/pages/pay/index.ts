Page({
  data: {
    loading: true
  },
  onLoad(options: Record<string, string>) {
    console.log('[Pay] onLoad options:', options)
    this.startPay(options)
  },
  startPay(options: Record<string, string>) {
    const amount = Number(options.amount || 0)
    const token = options.token || ''
    const apiBase = decodeURIComponent(options.apiBase || '')

    if (!amount || !apiBase || !token) {
      this.returnToWebview('fail', '', '参数不完整')
      return
    }
    console.log('[Pay] startPay:', { amount, apiBase })

    wx.login({
      success: (loginRes) => {
        const miniCode = loginRes && loginRes.code ? loginRes.code : ''
        console.log('[Pay] wx.login result:', loginRes)
        if (!miniCode) {
          this.returnToWebview('fail', '', '获取登录code失败')
          return
        }

        const requestData = {
          pay_amount: amount,
          code: miniCode,
          pay_scene: 'mini'
        }

        console.log('[Pay] request payload:', requestData)

        wx.request({
          url: apiBase + '/api/wechat_jsapi_pay',
          method: 'POST',
          header: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          data: requestData,
          success: (res: any) => {
            console.log('[Pay] pay response:', res)
            const data = res && res.data ? res.data : null
            if (!data || !data.success || !data.result) {
              const errMsg = (data && (data.message || data.error)) || '支付下单失败'
              wx.showModal({
                title: '支付失败',
                content: errMsg,
                showCancel: false
              })
              this.returnToWebview('fail', '', errMsg)
              return
            }
            const payParams = data.result
            wx.requestPayment({
              timeStamp: payParams.timeStamp,
              nonceStr: payParams.nonceStr,
              package: payParams.package,
              signType: payParams.signType,
              paySign: payParams.paySign,
              success: () => {
                this.returnToWebview('success', payParams.out_trade_no || '', '')
              },
              fail: (err: any) => {
                console.error('[Pay] requestPayment failed:', err)
                wx.showModal({
                  title: '支付失败',
                  content: (err && err.errMsg) || '支付失败',
                  showCancel: false
                })
                this.returnToWebview('fail', payParams.out_trade_no || '', (err && err.errMsg) || '支付失败')
              }
            })
          },
          fail: (err: any) => {
            const errMsg = err && err.errMsg ? err.errMsg : '支付请求失败'
            wx.showModal({
              title: '支付请求失败',
              content: errMsg,
              showCancel: false
            })
            this.returnToWebview('fail', '', errMsg)
          }
        })
      },
      fail: (err) => {
        console.error('[Pay] wx.login failed:', err)
        this.returnToWebview('fail', '', '登录失败')
      }
    })
  },
  returnToWebview(status: string, orderNo: string, errMsg: string) {
    const params: string[] = []
    params.push(`h5Path=${encodeURIComponent('/my-info')}`)
    if (status) {
      params.push(`payStatus=${encodeURIComponent(status)}`)
    }
    if (orderNo) {
      params.push(`orderNo=${encodeURIComponent(orderNo)}`)
    }
    if (errMsg) {
      params.push(`payErrMsg=${encodeURIComponent(errMsg)}`)
    }
    const query = params.length ? `?${params.join('&')}` : ''
    wx.redirectTo({
      url: `/pages/index/index${query}`
    })
  }
})
