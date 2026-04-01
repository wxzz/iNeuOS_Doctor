Page({
  handleBack() {
    wx.navigateBack()
  },
  onLoad(options: Record<string, string>) {
    const rawUrl = options && options.url ? decodeURIComponent(options.url) : ''
    if (!rawUrl) {
      wx.showModal({
        title: '打开失败',
        content: '下载链接为空，请重试。',
        showCancel: false
      })
      return
    }

    wx.showLoading({
      title: '正在打开PDF',
      mask: true
    })

    wx.downloadFile({
      url: rawUrl,
      success: (res) => {
        if (res.statusCode !== 200) {
          wx.hideLoading()
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
          success: () => {
            wx.hideLoading()
          },
          fail: (err) => {
            wx.hideLoading()
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
        wx.hideLoading()
        const msg = err && (err as any).errMsg ? (err as any).errMsg : '下载失败'
        wx.showModal({
          title: '下载失败',
          content: msg,
          showCancel: false
        })
      }
    })
  }
})
