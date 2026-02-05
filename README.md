# AI体征分析助手

## 项目介绍

**AI体征分析助手**是一款基于人工智能在医疗领域应用的智能诊断平台。系统利用先进的深度学习模型对医学影像和医疗数据进行分析和理解，为用户提供科学的初步健康筛查和分析建议。


![分析首页](https://github.com/wxzz/AI_Doctor/blob/main/%E5%88%86%E6%9E%90%E9%A6%96%E9%A1%B5.jpg)
![分析记录](https://github.com/wxzz/AI_Doctor/blob/main/%E5%88%86%E6%9E%90%E8%AE%B0%E5%BD%95.jpg)

## 核心功能
- **网站试用**：https://www.aineuos.net
### 📊 多模态医学影像分析
支持多种医学影像格式的分析，包括：
- **医学影像**：CT扫描、核磁共振(MRI)影像、组织病理成像
- **临床影像**：胸部X光片、皮肤科图像、眼科图像
- **医疗数据**：医生诊断病历、电子健康记录(EHR)、解剖特征数据

### 🔍 智能诊断分析
- 基于AI模型的影像识别与分析
- 多项临床相关基准评估验证
- 详细的分析结果报告生成
- 结构化结果展示
- 诊断排队与并发控制
- 诊断扣费与算力点管理

### 📋 分析记录管理
- 完整的分析历史记录保存
- 实时分析状态监控（分析中、分析成功、分析异常）
- 灵活的记录查询和管理功能
- 支持PDF格式下载导出
- 支持分析历史查询与筛选

### 🔐 用户系统
- 安全的账户注册与登录
- 用户信息管理
- Token-based身份验证
- 个人诊断记录隐私保护
- 短信验证码注册/校验
- 退出登录与密码修改

### 💳 支付与激励
- 微信支付下单（Native/JSAPI）
- 提现、分成与交易记录
- 邀请码与邀请奖励
- 提现记录与支付记录管理
- 邀请好友与邀请记录

## 主要优势

✨ **诊断效率高**
- 缩短诊断时间，提高工作效率
- 为医生诊断提供智能辅助

🌍 **打破地域限制**
- 突破医疗地域与资源壁垒
- 让AI医生走进千家万户

💰 **降低医疗成本**
- 普惠大众医疗服务
- 实现家庭初步健康筛查

🏥 **提升预防意识**
- 提升疾病预防的主动性
- 让居民成为自己健康的守护者

## 系统架构

### 后端技术栈
- **框架**：Flask 3.x
- **数据库**：PostgreSQL + SQLAlchemy ORM
- **鉴权**：JWT Token
- **支付**：微信支付 V3（Native/JSAPI）
- **短信**：阿里云短信
- **模型**：PyTorch + Transformers（医学诊断模型）
- **API**：RESTful API设计

### 前端技术栈
- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **路由**：Vue Router
- **样式**：Scoped CSS
- **文档渲染**：@kangc/v-md-editor / Marked
- **导出**：HTML2Canvas + HTML2PDF
- **其他**：QRCode

## 核心模块

| 模块 | 功能 | 说明 |
|------|------|------|
| 用户认证 | 注册、登录、信息管理 | 安全的身份验证 |
| 医学诊断 | 影像上传、分析、结果展示 | AI诊断核心模块 |
| 分析历史 | 记录查询、删除、PDF下载 | 完整的数据管理 |
| 个人中心 | 用户信息修改、密码修改 | 用户自助管理 |
| 支付与提现 | 微信支付、提现、支付记录、提现记录 | 资金相关能力 |
| 邀请好友 | 邀请码生成、邀请记录 | 用户增长与奖励 |

## 使用说明

### 用户流程
1. **注册登录** - 创建账户或使用现有账户登录
2. **提交诊断** - 上传医学影像和必要的医学描述
3. **等待分析** - 系统进行AI分析（显示分析状态）
4. **查看结果** - 查看详细的分析结果和建议
5. **管理记录** - 查看历史记录、下载报告、删除数据

### 关键功能操作
- **分析状态指示** - 实时显示分析进度（正在分析/分析成功/分析异常）
- **结果导出** - 支持PDF格式下载，包含完整的诊断信息
- **影像预览** - 点击表格中的影像可查看完整尺寸图片
- **Markdown展示** - 分析结果以格式化的markdown样式展示

## API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/register_user` | GET/POST | 用户注册（含短信验证码） |
| `/api/send_verify_sms_code` | POST | 发送短信验证码 |
| `/api/login_user` | POST | 用户登录 |
| `/api/login_out` | POST | 退出登录 |
| `/api/change_password` | POST | 修改密码 |
| `/api/get_myinfo` | GET | 获取用户信息 |
| `/api/update_avatar` | POST | 更新头像 |
| `/api/generate_invite_code` | GET | 生成邀请码 |
| `/api/submit_medicalrecord` | POST | 提交诊断请求 |
| `/api/get_medicalrecords` | GET | 获取诊断历史 |
| `/api/delete_medicalrecord` | DELETE | 删除诊断记录 |
| `/api/wechat_native_pay` | POST | 微信Native支付下单 |
| `/api/wechat_jsapi_pay` | POST | 微信JSAPI支付下单 |
| `/api/wechat_pay_notify` | POST | 支付回调通知 |
| `/api/wechat_pay_query` | GET | 支付订单查询 |
| `/api/wechat_withdraw` | POST | 提现申请 |
| `/api/wechat_withdraw_notify` | POST | 提现回调通知 |
| `/api/wechat_withdraw_query` | GET | 提现订单查询 |
| `/api/wechat_withdraw_record` | GET | 提现记录 |
| `/api/wechat_pay_record` | GET | 支付记录 |
| `/api/invite_record` | GET | 邀请记录 |

## 安全说明

⚠️ **重要声明**

**本AI体征分析助手为人工智能模型分析结果，不能替代正规医院诊断结果。**

系统提供的分析和建议仅供参考，不可作为医学诊断的最终依据。如有健康疑虑，请咨询专业医疗机构和医生。

## 安装部署

### 后端环境
```bash
cd backend
pip install -r requirements.txt
python app.py
```

默认监听 http://127.0.0.1:5000

### 前端环境
```bash
cd frontend
npm install
npm run dev
```

访问 http://127.0.0.1:5001 进行开发调试。

## 许可证

本项目遵循有限许可。

## 联系方式

QQ:504547114。

---

**开发团队**：iNeuOS Team

**更新时间**：2026年2月

*AI让医疗更智慧，让健康更普惠*
