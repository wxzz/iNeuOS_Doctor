/*
 Navicat Premium Data Transfer

 Source Server         : local_progresql
 Source Server Type    : PostgreSQL
 Source Server Version : 130003 (130003)
 Source Host           : localhost:5433
 Source Catalog        : ai_doctor
 Source Schema         : public

 Target Server Type    : PostgreSQL
 Target Server Version : 130003 (130003)
 File Encoding         : 65001

 Date: 01/04/2026 15:39:23
*/


-- ----------------------------
-- Table structure for bas_invite_record
-- ----------------------------
DROP TABLE IF EXISTS "public"."bas_invite_record";
CREATE TABLE "public"."bas_invite_record" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "invite_code" varchar(6) COLLATE "pg_catalog"."default" NOT NULL,
  "invite_user_id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "invite_time" timestamp(6) NOT NULL,
  "increase_cost" numeric(10,2) NOT NULL
)
;
COMMENT ON COLUMN "public"."bas_invite_record"."id" IS '邀请记录ID';
COMMENT ON COLUMN "public"."bas_invite_record"."user_id" IS '用户ID';
COMMENT ON COLUMN "public"."bas_invite_record"."invite_code" IS '邀请码';
COMMENT ON COLUMN "public"."bas_invite_record"."invite_user_id" IS '被邀请人用户ID';
COMMENT ON COLUMN "public"."bas_invite_record"."invite_time" IS '邀请时间';
COMMENT ON COLUMN "public"."bas_invite_record"."increase_cost" IS '增加的赞助算力点';
COMMENT ON TABLE "public"."bas_invite_record" IS '邀请记录表';

-- ----------------------------
-- Table structure for bas_medical
-- ----------------------------
DROP TABLE IF EXISTS "public"."bas_medical";
CREATE TABLE "public"."bas_medical" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "prompt_txt" varchar(1024) COLLATE "pg_catalog"."default" NOT NULL,
  "prompt_img" varchar(255) COLLATE "pg_catalog"."default",
  "result" varchar(4096) COLLATE "pg_catalog"."default",
  "sdt" timestamp(6),
  "edt" timestamp(6),
  "credit" numeric(10,2) NOT NULL,
  "medical_status" int4 NOT NULL,
  "medical_status_desc" varchar(1024) COLLATE "pg_catalog"."default",
  "elapsed_time" float4 NOT NULL,
  "is_delete" bool NOT NULL DEFAULT false
)
;
COMMENT ON COLUMN "public"."bas_medical"."id" IS '主键ID';
COMMENT ON COLUMN "public"."bas_medical"."user_id" IS '用户ID';
COMMENT ON COLUMN "public"."bas_medical"."prompt_txt" IS '提示词和诊断文字';
COMMENT ON COLUMN "public"."bas_medical"."prompt_img" IS '医学影像照片，存在照片路径';
COMMENT ON COLUMN "public"."bas_medical"."result" IS '分析结果';
COMMENT ON COLUMN "public"."bas_medical"."sdt" IS '调用开始时间';
COMMENT ON COLUMN "public"."bas_medical"."edt" IS '返回结果时间';
COMMENT ON COLUMN "public"."bas_medical"."credit" IS '扣除费用，算力点';
COMMENT ON COLUMN "public"."bas_medical"."medical_status" IS '当前分析状态：0分析成功、1正在分析、-1分析异常';
COMMENT ON COLUMN "public"."bas_medical"."medical_status_desc" IS '当前分析状态描述';
COMMENT ON COLUMN "public"."bas_medical"."elapsed_time" IS '分析用时，整数部分是分钟，小数部分是秒';
COMMENT ON TABLE "public"."bas_medical" IS '医学诊断表';

-- ----------------------------
-- Table structure for bas_medical_chat
-- ----------------------------
DROP TABLE IF EXISTS "public"."bas_medical_chat";
CREATE TABLE "public"."bas_medical_chat" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "session_id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_id" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "chat_sdt_time" timestamp(6) NOT NULL,
  "is_delete" bool NOT NULL DEFAULT false,
  "chat_edt_time" timestamp(6)
)
;
COMMENT ON COLUMN "public"."bas_medical_chat"."id" IS '问诊一组会话id，系统生成';
COMMENT ON COLUMN "public"."bas_medical_chat"."session_id" IS '会话ID，本质是根据用户token生成的session_id';
COMMENT ON COLUMN "public"."bas_medical_chat"."user_id" IS '用户ID';
COMMENT ON COLUMN "public"."bas_medical_chat"."chat_sdt_time" IS '会话开始时间';
COMMENT ON COLUMN "public"."bas_medical_chat"."is_delete" IS '是否删除';
COMMENT ON COLUMN "public"."bas_medical_chat"."chat_edt_time" IS '会话结束时间';
COMMENT ON TABLE "public"."bas_medical_chat" IS '病情问诊会话';

-- ----------------------------
-- Table structure for bas_medical_chat_messages
-- ----------------------------
DROP TABLE IF EXISTS "public"."bas_medical_chat_messages";
CREATE TABLE "public"."bas_medical_chat_messages" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "chat_id" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "prompt_txt" varchar(1024) COLLATE "pg_catalog"."default" NOT NULL,
  "result" varchar(4096) COLLATE "pg_catalog"."default",
  "sdt" timestamp(6) NOT NULL,
  "edt" timestamp(6),
  "state" int2 NOT NULL,
  "error" varchar(1024) COLLATE "pg_catalog"."default"
)
;
COMMENT ON COLUMN "public"."bas_medical_chat_messages"."id" IS '问诊每条信息ID';
COMMENT ON COLUMN "public"."bas_medical_chat_messages"."chat_id" IS '关联bas_medical_chat表id';
COMMENT ON COLUMN "public"."bas_medical_chat_messages"."state" IS '0完整回复，-1回复失败';
COMMENT ON COLUMN "public"."bas_medical_chat_messages"."error" IS 'state为-1的时候，回复失败时的错误信息';
COMMENT ON TABLE "public"."bas_medical_chat_messages" IS '病情问诊会话消息表';

-- ----------------------------
-- Table structure for bas_wechat_pay
-- ----------------------------
DROP TABLE IF EXISTS "public"."bas_wechat_pay";
CREATE TABLE "public"."bas_wechat_pay" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "callback_id" varchar(64) COLLATE "pg_catalog"."default",
  "create_time" timestamp(6),
  "resource_type" varchar(32) COLLATE "pg_catalog"."default",
  "event_type" varchar(64) COLLATE "pg_catalog"."default",
  "summary" varchar(128) COLLATE "pg_catalog"."default",
  "mchid" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "appid" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "out_trade_no" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "transaction_id" varchar(64) COLLATE "pg_catalog"."default",
  "trade_type" varchar(32) COLLATE "pg_catalog"."default",
  "trade_state" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "trade_state_desc" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "bank_type" varchar(32) COLLATE "pg_catalog"."default",
  "attach" text COLLATE "pg_catalog"."default",
  "success_time" timestamp(6),
  "openid" varchar(64) COLLATE "pg_catalog"."default",
  "total_amount" int4 NOT NULL DEFAULT 0,
  "payer_total" int4 DEFAULT 0,
  "currency" varchar(16) COLLATE "pg_catalog"."default" DEFAULT 'CNY'::character varying,
  "payer_currency" varchar(16) COLLATE "pg_catalog"."default" DEFAULT 'CNY'::character varying,
  "create_at" timestamp(6) NOT NULL DEFAULT now(),
  "update_at" timestamp(6) NOT NULL DEFAULT now(),
  "is_notify" int2 NOT NULL
)
;
COMMENT ON COLUMN "public"."bas_wechat_pay"."id" IS '对应out_trade_no编码';
COMMENT ON COLUMN "public"."bas_wechat_pay"."user_id" IS '用户ID';
COMMENT ON COLUMN "public"."bas_wechat_pay"."callback_id" IS '回调唯一ID，作为主键（UUID格式，长度足够）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."create_time" IS '回调创建时间（带时区，匹配微信返回的+08:00）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."resource_type" IS '回调资源类型（如encrypt-resource）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."event_type" IS '事件类型（如TRANSACTION.SUCCESS）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."summary" IS '回调摘要（如支付成功）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."mchid" IS '商户号';
COMMENT ON COLUMN "public"."bas_wechat_pay"."appid" IS '公众号/小程序APPID';
COMMENT ON COLUMN "public"."bas_wechat_pay"."out_trade_no" IS '商户订单号（业务核心，非空）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."transaction_id" IS '微信支付交易号';
COMMENT ON COLUMN "public"."bas_wechat_pay"."trade_type" IS '交易类型（如NATIVE/JSAPI等）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."trade_state" IS '交易状态（如ORDER/SUCCESS/REFUND等）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."trade_state_desc" IS '交易状态描述';
COMMENT ON COLUMN "public"."bas_wechat_pay"."bank_type" IS '付款银行类型（可为空，如无银行卡支付场景）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."attach" IS ' 附加数据（长度不固定，用TEXT）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."success_time" IS '支付成功时间（交易成功时非空）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."openid" IS '用户OpenID（非空场景可加NOT NULL，根据业务调整）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."total_amount" IS '订单总金额（分）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."payer_total" IS '用户实际支付金额（分）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."currency" IS '订单币种（默认人民币）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."payer_currency" IS '用户支付币种';
COMMENT ON COLUMN "public"."bas_wechat_pay"."create_at" IS '记录入库时间（自动填充）';
COMMENT ON COLUMN "public"."bas_wechat_pay"."update_at" IS '记录更新时间';
COMMENT ON COLUMN "public"."bas_wechat_pay"."is_notify" IS '是否回执通知，-1未回执，0回执';
COMMENT ON TABLE "public"."bas_wechat_pay" IS '微信付款';

-- ----------------------------
-- Table structure for bas_wechat_withdraw
-- ----------------------------
DROP TABLE IF EXISTS "public"."bas_wechat_withdraw";
CREATE TABLE "public"."bas_wechat_withdraw" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "transfer_scene_id" varchar(10) COLLATE "pg_catalog"."default" NOT NULL,
  "transfer_amount" int4 NOT NULL,
  "transfer_remark" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_name" varchar(10) COLLATE "pg_catalog"."default" NOT NULL,
  "user_recv_perception" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "appid" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "out_bill_no" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "create_time" timestamp(6) NOT NULL,
  "package_info" varchar(255) COLLATE "pg_catalog"."default" NOT NULL,
  "state" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "transfer_bill_no" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "create_at" timestamp(6) NOT NULL,
  "update_at" timestamp(6) NOT NULL,
  "is_notify" int2 NOT NULL,
  "notify_id" varchar(64) COLLATE "pg_catalog"."default",
  "resource_type" varchar(32) COLLATE "pg_catalog"."default",
  "event_type" varchar(32) COLLATE "pg_catalog"."default",
  "summary" varchar(32) COLLATE "pg_catalog"."default",
  "mch_id" varchar(32) COLLATE "pg_catalog"."default",
  "update_time" timestamp(6),
  "withdraw_amount" numeric(10,2) NOT NULL
)
;
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."id" IS '对应out_trade_no编码';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."user_id" IS '用户ID';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."transfer_scene_id" IS '转账场景ID，1005表示商业转账';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."transfer_amount" IS '转账金额（分）';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."transfer_remark" IS '转账备注，最多32字符';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."user_name" IS '收款用户真实姓名';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."user_recv_perception" IS '用户收款时展示信息';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."appid" IS '公众号appid';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."out_bill_no" IS '商户账单号（商户系统内部唯一）';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."create_time" IS '回调创建时间（带时区，匹配微信返回的+08:00）';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."package_info" IS '跳转微信支付收款页的package信息';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."state" IS '商家转账订单状态';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."transfer_bill_no" IS '获取转账单号';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."create_at" IS '入库时间';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."update_at" IS '记录更新时间';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."is_notify" IS '是否回执通知，-1未回执，0回执';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."notify_id" IS '回调通知ID';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."resource_type" IS '通知的资源数据类型';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."event_type" IS '通知的类型';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."summary" IS '回调摘要';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."mch_id" IS '商务ID';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."update_time" IS '回执更新时间';
COMMENT ON COLUMN "public"."bas_wechat_withdraw"."withdraw_amount" IS '实际提现额，没有扣除手续费和进行分转换';
COMMENT ON TABLE "public"."bas_wechat_withdraw" IS '企业付款到微信零钱（提现）';

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS "public"."sys_user";
CREATE TABLE "public"."sys_user" (
  "id" varchar(32) COLLATE "pg_catalog"."default" NOT NULL,
  "user_account" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "user_pwd" varchar(128) COLLATE "pg_catalog"."default" NOT NULL,
  "status" int2 NOT NULL,
  "mobile" varchar(15) COLLATE "pg_catalog"."default" NOT NULL,
  "email" varchar(64) COLLATE "pg_catalog"."default",
  "admin_type" int2 NOT NULL,
  "last_login_ip" varchar(32) COLLATE "pg_catalog"."default",
  "last_login_time" timestamp(6),
  "last_login_os" varchar(32) COLLATE "pg_catalog"."default",
  "create_time" timestamp(6) NOT NULL DEFAULT (now())::timestamp without time zone,
  "avatar" bytea,
  "account_credit" numeric(10,2) NOT NULL DEFAULT 0.0,
  "invite_code" varchar(6) COLLATE "pg_catalog"."default",
  "invite_create_time" timestamp(6),
  "reg_ip" varchar(32) COLLATE "pg_catalog"."default",
  "current_medical_id" varchar(32) COLLATE "pg_catalog"."default",
  "cash" numeric(10,2) NOT NULL,
  "real_name" varchar(10) COLLATE "pg_catalog"."default",
  "is_user_license" bool NOT NULL
)
;
COMMENT ON COLUMN "public"."sys_user"."id" IS '主键id';
COMMENT ON COLUMN "public"."sys_user"."user_account" IS '用户账号';
COMMENT ON COLUMN "public"."sys_user"."user_pwd" IS '用户密码';
COMMENT ON COLUMN "public"."sys_user"."status" IS '状态：0(审核)、1正常、2停用、3删除';
COMMENT ON COLUMN "public"."sys_user"."mobile" IS '联系电话';
COMMENT ON COLUMN "public"."sys_user"."email" IS '联系邮箱';
COMMENT ON COLUMN "public"."sys_user"."admin_type" IS '账号类型：1超级管理员、2租户管理员、3普通账号';
COMMENT ON COLUMN "public"."sys_user"."last_login_ip" IS '最后登录ip';
COMMENT ON COLUMN "public"."sys_user"."last_login_time" IS '最后登录时间';
COMMENT ON COLUMN "public"."sys_user"."last_login_os" IS '最后登录客户端';
COMMENT ON COLUMN "public"."sys_user"."create_time" IS '创建时间';
COMMENT ON COLUMN "public"."sys_user"."avatar" IS '头像';
COMMENT ON COLUMN "public"."sys_user"."account_credit" IS '账户余额，算力点';
COMMENT ON COLUMN "public"."sys_user"."invite_code" IS '邀请码';
COMMENT ON COLUMN "public"."sys_user"."invite_create_time" IS '邀请码生成时间';
COMMENT ON COLUMN "public"."sys_user"."reg_ip" IS '注册ip';
COMMENT ON COLUMN "public"."sys_user"."current_medical_id" IS '当前正在诊断的ID，没有诊断是为null';
COMMENT ON COLUMN "public"."sys_user"."cash" IS '提成费用，可以提现到微信零钱';
COMMENT ON COLUMN "public"."sys_user"."real_name" IS '真实姓名';
COMMENT ON COLUMN "public"."sys_user"."is_user_license" IS '是否同意用户注册协议';
COMMENT ON TABLE "public"."sys_user" IS '用户表';

-- ----------------------------
-- Primary Key structure for table bas_invite_record
-- ----------------------------
ALTER TABLE "public"."bas_invite_record" ADD CONSTRAINT "bas_invite_record_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table bas_medical
-- ----------------------------
ALTER TABLE "public"."bas_medical" ADD CONSTRAINT "bas_ai_medical_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table bas_medical_chat
-- ----------------------------
ALTER TABLE "public"."bas_medical_chat" ADD CONSTRAINT "bas_medical_chat_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table bas_medical_chat_messages
-- ----------------------------
ALTER TABLE "public"."bas_medical_chat_messages" ADD CONSTRAINT "bas_medical_chat_messages_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table bas_wechat_pay
-- ----------------------------
ALTER TABLE "public"."bas_wechat_pay" ADD CONSTRAINT "bas_wechat_pay_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table bas_wechat_withdraw
-- ----------------------------
ALTER TABLE "public"."bas_wechat_withdraw" ADD CONSTRAINT "bas_wechat_withdraw_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table sys_user
-- ----------------------------
ALTER TABLE "public"."sys_user" ADD CONSTRAINT "bas_user_pkey" PRIMARY KEY ("id", "user_account");
