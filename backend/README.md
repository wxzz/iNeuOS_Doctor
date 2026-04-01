# 后端（backend）

## 项目简介

本后端项目为“AI体征分析助手”平台的服务端，基于 Flask 框架开发，负责用户管理、医学影像分析、数据存储、支付提现等核心业务。

## 技术栈
- 框架：Flask 1.0
- 数据库：PostgreSQL
- ORM：SQLAlchemy
- 支付：微信支付V3
- 其他：阿里云短信、日志、定时任务等

## 主要功能
- 用户注册、登录、信息管理
- 医学影像/数据分析接口
- 诊断历史记录管理
- 微信支付、企业付款到零钱（提现）
- 分成、邀请奖励、短信通知
- RESTful API 设计

## 运行与开发

```bash
cd backend
pip install -r requirements.txt
python app.py
```

默认监听 http://127.0.0.1:5000

## 目录结构
- `app.py` 主入口
- `models.py` 数据模型
- `aliyun_sms.py` 短信服务
- `wechatpayv3/` 微信支付相关
- `medical/` 医学分析数据
- `logs/` 日志

## 说明

- 本系统分析结果仅供参考，不能替代专业医疗诊断。
- 如遇问题请联系开发团队。

---

更新时间：2026年1月
