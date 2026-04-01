"""
ORM模型类
使用SQLAlchemy定义数据库表模型
"""

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Float,
    DateTime,
    Numeric,
    SmallInteger,
    JSON,
    LargeBinary,
    Text,
    Boolean,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL")

# 创建数据库引擎
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


class SysUser(Base):
    """用户表模型"""

    __tablename__ = 'sys_user'

    id = Column(String(32), primary_key=True, comment='主键id')
    user_account = Column(String(64), nullable=False, comment='用户账号')
    user_pwd = Column(String(128), nullable=False, comment='用户密码')
    status = Column(
        SmallInteger, nullable=False, comment='状态：0(审核)、1正常、2停用、3删除'
    )
    mobile = Column(String(15), comment='联系电话')
    email = Column(String(64), comment='联系邮箱')
    admin_type = Column(
        SmallInteger,
        nullable=False,
        comment='账号类型：1超级管理员、2租户管理员、3普通账号',
    )
    last_login_ip = Column(String(32), comment='最后登录ip')
    last_login_time = Column(DateTime, comment='最后登录时间')
    last_login_os = Column(String(32), comment='最后登录客户端')
    create_time = Column(
        DateTime, nullable=False, default=datetime.now, comment='创建时间'
    )
    avatar = Column(LargeBinary, comment='头像')
    account_credit = Column(
        Numeric(10, 2), nullable=False, default=0.0, comment='账户余额,算力点'
    )
    invite_code = Column(String(6), comment='邀请码')
    invite_create_time = Column(DateTime, comment='邀请码生成时间')
    reg_ip = Column(String(32), comment='注册IP地址')
    current_medical_id = Column(String(32), comment='当前正在诊断的ID,没有诊断是为null')
    cash = Column(
        Numeric(10, 2),
        nullable=False,
        default=0.0,
        comment='提成费用，可以提现到微信零钱',
    )

    real_name = Column(String(10), comment='真实姓名')

    is_user_license = Column(
        Boolean, nullable=False, default=False, comment='是否同意用户注册协议'
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_account': self.user_account,
            'status': self.status,
            'mobile': self.mobile,
            'email': self.email,
            'admin_type': self.admin_type,
            'last_login_ip': self.last_login_ip,
            'last_login_time': (
                self.last_login_time.isoformat() if self.last_login_time else None
            ),
            'last_login_os': self.last_login_os,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'account_credit': self.account_credit,
            'invite_code': self.invite_code,
            'invite_create_time': (
                self.invite_create_time.isoformat() if self.invite_create_time else None
            ),
            'reg_ip': self.reg_ip,
            'current_medical_id': self.current_medical_id,
            'cash': self.cash,
            'real_name': self.real_name,
            'is_user_license': self.is_user_license,
        }


class BasMedical(Base):
    """医学诊断表模型"""

    __tablename__ = 'bas_medical'

    id = Column(String(32), primary_key=True, comment='主键ID')
    user_id = Column(String(32), nullable=False, comment='用户ID')
    prompt_txt = Column(String(255), nullable=False, comment='提示词和诊断文字')
    prompt_img = Column(String(255), comment='医学影像照片，存在照片路径')
    result = Column(String(4096), comment='分析结果')
    sdt = Column(DateTime, comment='调用开始时间')
    edt = Column(DateTime, comment='调用结束时间')
    credit = Column(
        Numeric(10, 2), nullable=False, default=0.0, comment='本次诊断消耗算力点'
    )
    medical_status = Column(
        Integer,
        nullable=False,
        comment='当前分析状态：0分析成功、1正在分析、-1分析异常',
    )
    medical_status_desc = Column(String(1024), comment='当前分析状态描述')
    elapsed_time = Column(
        Float, nullable=False, comment='分析用时，整数部分是分钟，小数部分是秒钟'
    )
    is_delete = Column(Boolean, nullable=False, default=False, comment='是否删除')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'prompt_txt': self.prompt_txt,
            'prompt_img': self.prompt_img,
            'result': self.result,
            'sdt': self.sdt.isoformat() if self.sdt else None,
            'edt': self.edt.isoformat() if self.edt else None,
            'credit': self.credit,
            'medical_status': self.medical_status,
            'medical_status_desc': self.medical_status_desc,
            'elapsed_time': self.elapsed_time,
            'is_delete': self.is_delete,
        }


class BasMedicalChat(Base):
    """问诊会话表模型"""

    __tablename__ = 'bas_medical_chat'

    id = Column(String(32), primary_key=True, comment='问诊一组会话id，系统生成')
    session_id = Column(
        String(32),
        nullable=False,
        comment='会话ID，本质是根据用户token生成的session_id',
    )
    user_id = Column(String(128), nullable=False, comment='用户ID')
    chat_sdt_time = Column(DateTime, nullable=False, comment='会话开始时间')
    chat_edt_time = Column(DateTime, comment='会话结束时间')
    is_delete = Column(Boolean, nullable=False, default=False, comment='是否删除')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'chat_sdt_time': (
                self.chat_sdt_time.isoformat() if self.chat_sdt_time else None
            ),
            'chat_edt_time': (
                self.chat_edt_time.isoformat() if self.chat_edt_time else None
            ),
            'is_delete': self.is_delete,
        }


class BasMedicalChatMessages(Base):
    """问诊会话消息表模型"""

    __tablename__ = 'bas_medical_chat_messages'

    id = Column(String(32), primary_key=True, comment='问诊每条信息ID')
    chat_id = Column(String(64), nullable=False, comment='关联bas_medical_chat表id')
    prompt_txt = Column(String(1024), nullable=False, comment='用户问诊内容')
    result = Column(String(4096), comment='问诊结果')
    sdt = Column(DateTime, nullable=False, comment='会话消息开始时间')
    edt = Column(DateTime, comment='会话消息结束时间')
    state = Column(SmallInteger, nullable=False, comment='0完整回复，-1回复失败')
    error = Column(String(1024), comment='回复失败时的错误信息')

    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'prompt_txt': self.prompt_txt,
            'result': self.result,
            'sdt': self.sdt.isoformat() if self.sdt else None,
            'edt': self.edt.isoformat() if self.edt else None,
            'state': self.state,
            'error': self.error,
        }


class BasInviteRecord(Base):
    """邀请记录表模型"""

    __tablename__ = 'bas_invite_record'

    id = Column(String(32), primary_key=True, comment='邀请记录ID')
    user_id = Column(String(32), nullable=False, comment='用户ID')
    invite_code = Column(String(6), nullable=False, comment='邀请码')
    invite_user_id = Column(String(32), nullable=False, comment='被邀请人用户ID')
    invite_time = Column(DateTime, nullable=False, comment='邀请时间')
    increase_cost = Column(
        Numeric(10, 2), nullable=False, default=0.0, comment='增加的赞助算力点'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'invite_code': self.invite_code,
            'invite_user_id': self.invite_user_id,
            'invite_time': self.invite_time.isoformat() if self.invite_time else None,
            'increase_cost': self.increase_cost,
        }


class BasWechatPay(Base):
    """微信支付回调记录表模型"""

    __tablename__ = 'bas_wechat_pay'

    id = Column(String(32), primary_key=True, comment='对应out_trade_no编码')
    user_id = Column(String(32), nullable=False, comment='用户ID')
    callback_id = Column(
        String(64), comment='回调唯一ID，作为主键（UUID格式，长度足够）'
    )
    create_time = Column(
        DateTime, comment='回调创建时间（带时区，匹配微信返回的+08:00）'
    )
    resource_type = Column(String(32), comment='回调资源类型（如encrypt-resource）')
    event_type = Column(String(64), comment='事件类型（如TRANSACTION.SUCCESS）')
    summary = Column(String(128), comment='回调摘要（如支付成功）')
    mchid = Column(String(32), nullable=False, comment='商户号')
    appid = Column(String(64), nullable=False, comment='公众号/小程序APPID')
    out_trade_no = Column(
        String(64), nullable=False, comment='商户订单号（业务核心，非空）'
    )
    transaction_id = Column(String(64), comment='微信支付交易号')
    trade_type = Column(String(32), comment='交易类型（如NATIVE/JSAPI等）')
    trade_state = Column(
        String(32), nullable=False, comment='交易状态（如ORDER/SUCCESS/REFUND等）'
    )
    trade_state_desc = Column(String(128), nullable=False, comment='交易状态描述')
    bank_type = Column(String(32), comment='付款银行类型（可为空，如无银行卡支付场景）')
    attach = Column(Text, comment='附加数据（长度不固定，用TEXT）')
    success_time = Column(DateTime, comment='支付成功时间（交易成功时非空）')
    openid = Column(
        String(64), comment='用户OpenID（非空场景可加NOT NULL，根据业务调整）'
    )
    total_amount = Column(Integer, nullable=False, default=0, comment='订单总额（分）')
    payer_total = Column(Integer, default=0, comment='用户实际支付额（分）')
    currency = Column(String(16), default='CNY', comment='订单币种（默认人民币）')
    payer_currency = Column(String(16), default='CNY', comment='用户支付币种')
    create_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment='记录入库时间（自动填充）',
    )
    update_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment='记录更新时间',
    )
    is_notify = Column(
        SmallInteger,
        nullable=False,
        default=-1,
        comment='是否回执通知，-1未回执，0已回执',
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'callback_id': self.callback_id,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'resource_type': self.resource_type,
            'event_type': self.event_type,
            'summary': self.summary,
            'mchid': self.mchid,
            'appid': self.appid,
            'out_trade_no': self.out_trade_no,
            'transaction_id': self.transaction_id,
            'trade_type': self.trade_type,
            'trade_state': self.trade_state,
            'trade_state_desc': self.trade_state_desc,
            'bank_type': self.bank_type,
            'attach': self.attach,
            'success_time': (
                self.success_time.isoformat() if self.success_time else None
            ),
            'openid': self.openid,
            'total_amount': self.total_amount,
            'payer_total': self.payer_total,
            'currency': self.currency,
            'payer_currency': self.payer_currency,
            'create_at': self.create_at.isoformat() if self.create_at else None,
            'update_at': self.update_at.isoformat() if self.update_at else None,
            'is_notify': self.is_notify,
        }


class BasWechatWithdraw(Base):
    """微信提现记录表模型"""

    __tablename__ = 'bas_wechat_withdraw'

    id = Column(String(32), primary_key=True, comment='对应out_trade_no编码')
    user_id = Column(String(32), nullable=False, comment='用户ID')
    transfer_scene_id = Column(
        String(10), nullable=False, comment='转账场景ID，1005表示商业转账'
    )
    transfer_amount = Column(Integer, nullable=False, comment='转账额（分）')
    transfer_remark = Column(String(32), nullable=False, comment='转账备注，最多32字符')
    user_name = Column(String(10), nullable=False, comment='收款用户真实姓名')
    user_recv_perception = Column(
        String(255), nullable=False, comment='用户收款时展示信息'
    )
    appid = Column(String(32), nullable=False, comment='公众号appid')
    out_bill_no = Column(
        String(32), nullable=False, comment='商户账单号（商户系统内部唯一）'
    )
    create_time = Column(
        DateTime, nullable=False, comment='回调创建时间（带时区，匹配微信返回的+08:00）'
    )
    package_info = Column(
        String(255), nullable=False, comment='跳转微信支付收款页的package信息'
    )
    state = Column(String(32), nullable=False, comment='商家转账订单状态')
    transfer_bill_no = Column(String(64), nullable=False, comment='获取转账单号')
    create_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment='入库时间',
    )
    update_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
        comment='记录更新时间',
    )
    is_notify = Column(
        SmallInteger,
        nullable=False,
        default=-1,
        comment='是否回执通知，-1未回执，0回执',
    )
    notify_id = Column(String(64), comment='回调通知ID')
    resource_type = Column(String(32), comment='通知的资源数据类型')
    event_type = Column(String(32), comment='通知的类型')
    summary = Column(String(32), comment='回调摘要')
    mch_id = Column(String(32), comment='商务ID')

    update_time = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment='回执更新时间',
    )

    withdraw_amount = Column(
        Numeric(10, 2),
        nullable=False,
        comment='实际提现额，没有扣除手续费和进行分转换',
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transfer_scene_id': self.transfer_scene_id,
            'transfer_amount': self.transfer_amount,
            'transfer_remark': self.transfer_remark,
            'user_name': self.user_name,
            'user_recv_perception': self.user_recv_perception,
            'appid': self.appid,
            'out_bill_no': self.out_bill_no,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'package_info': self.package_info,
            'state': self.state,
            'transfer_bill_no': self.transfer_bill_no,
            'create_at': self.create_at.isoformat() if self.create_at else None,
            'update_at': self.update_at.isoformat() if self.update_at else None,
            'is_notify': self.is_notify,
            'notify_id': self.notify_id,
            'resource_type': self.resource_type,
            'event_type': self.event_type,
            'summary': self.summary,
            'mch_id': self.mch_id,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'withdraw_amount': self.withdraw_amount,
        }


# 获取数据库会话的依赖函数
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
