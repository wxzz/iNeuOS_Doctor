"""
v1.0 Flask HTTP请求接口
基础版本，没有进行队列和线程优化。
"""

import os
import sys
import uuid
import re
import asyncio
import urllib.parse
import importlib

from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
import jwt
import datetime
from functools import wraps
from models import (
    SysUser,
    BasMedical,
    BasMedicalChat,
    BasMedicalChatMessages,
    BasInviteRecord,
    BasWechatPay,
    BasWechatWithdraw,
    SessionLocal,
    get_db,
)
from sqlalchemy import func, or_, cast
from sqlalchemy.orm import aliased
from sqlalchemy.types import Numeric
import hashlib
from decimal import Decimal, ROUND_DOWN
from IdGenerator import options, generator
import os
import base64
from medical import MedicalModel
import threading
from dotenv import load_dotenv
import secrets
import time
import random
import string
import jieba
import unicodedata
from openai import OpenAI

import matplotlib

matplotlib.use('Agg', force=True)  # 强制使用非交互式后端
matplotlib.interactive(False)  # 关闭交互模式

import requests
import json
from openai import OpenAI
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from wechatpayv3 import WeChatPay, WeChatPayType

from logger import Logger
from utils import read_file_content
from utils import convert_iso_time_to_normal
from utils import get_current_utc_time, get_current_local_time

from aliyun_sms import Aliyun_Sms

logger = Logger().logger
# logger.info('日志系统初始化成功')

# 关闭PaddleX模型源连通性检查，避免启动阶段长时间探测与额外日志
os.environ.setdefault('PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK', 'True')
# 规避部分 Paddle + oneDNN(PIR) 组合在 CPU 下的运行时不兼容问题
os.environ.setdefault('FLAGS_enable_pir_api', '0')
os.environ.setdefault('FLAGS_use_mkldnn', '0')
# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 允许跨域请求

# 全局锁和队列，用于限制并发诊断请求
lock = threading.Lock()
pay_notify_lock = threading.Lock()
withdraw_notify_lock = threading.Lock()
ocr_lock = threading.Lock()
ocr_engine = None


# JWT配置
app.config['SECRET_KEY'] = os.getenv(
    'SECRET_KEY', 'LxY8mKp3qR6tAv9wE2zN5cF7hJ1gM4nB8vD0xS3rT6yU9iW2oP5q'
)  # 生产环境请修改为强密钥
jwt_expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', '2'))
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(
    hours=jwt_expiration_hours
)  # Token过期时间24小时

# Token黑名单（用于存储已退出的token -> 过期时间戳）
# 生产环境建议使用Redis等持久化存储
token_blacklist = {}
token_blacklist_lock = threading.Lock()

# 临时PDF下载缓存（token -> {path, filename, expires_at}）
pdf_download_cache = {}
pdf_download_lock = threading.Lock()
PDF_DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'medical',
    'medical_pdf_downloads',
)
os.makedirs(PDF_DOWNLOAD_DIR, exist_ok=True)
PDF_CHAT_DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'medical',
    'medical_chat_pdf_downloads',
)
os.makedirs(PDF_CHAT_DOWNLOAD_DIR, exist_ok=True)

# worker_id: 机器ID，分布式部署时每个实例需要不同的ID
# datacenter_id: 数据中心ID，多数据中心部署时使用
options = options.IdGeneratorOptions(worker_id=1)
# 参数中，worker_id_bit_length 默认值6，支持的 worker_id 最大值为2^6-1，若 worker_id 超过64，可设置更大的 worker_id_bit_length
idgen = generator.DefaultIdGenerator()
# 保存参数
idgen.set_id_generator(options)
# 生成id

medical_model = MedicalModel()

# 初始化微信支付实例
wxpay = WeChatPay(
    wechatpay_type=WeChatPayType.NATIVE,  # 支付场景，这里以Native为例
    appid=os.getenv('WECHAT_APPID'),  # 你的微信公众账号ID或小程序ID
    mchid=os.getenv('WECHAT_MCH_ID'),
    public_key_id=os.getenv('WECHAT_API_PUBLIC_KEY_ID'),
    public_key=read_file_content(os.getenv('WECHAT_API_PUBLIC_KEY_PATH'), False),
    private_key=read_file_content(os.getenv('WECHAT_API_PRIVATE_KEY_PATH'), False),
    cert_serial_no=os.getenv('WECHAT_SERIAL_NO'),
    apiv3_key=os.getenv('WECHAT_API_V3_KEY'),
    cert_dir=os.getenv('WECHAT_CERT_DIR'),
    partner_mode=False,
    notify_url=os.getenv('WECHAT_PAY_NOTIFY_URL'),  # 默认回调地址，也可在具体下单时覆盖
    logger=logger,
)

# 短信验证码缓存：phone -> {'code': '123456', 'expires_at': datetime}
sms_code_cache = {}
aliyun_sms_client = Aliyun_Sms()


# 生成雪花ID
def next_id() -> str:
    return idgen.next_id_str()


# 获得限制文本
def get_limit_text(txt: str):
    current_result_len_limit = int(
        os.getenv('RESULT_LEN_LIMIT', '4096')
    )  # 结果字符长度限制
    if len(txt) >= current_result_len_limit:
        txt = txt[:current_result_len_limit]
    return txt


def sanitize_user_dir_name(user_account: str) -> str:
    raw_name = str(user_account or '').strip()
    if not raw_name:
        return 'unknown_user'
    # Windows 非法路径字符替换
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', raw_name)
    sanitized = sanitized.strip().strip('.')
    return sanitized or 'unknown_user'


def get_ocr_engine():
    global ocr_engine
    if ocr_engine is not None:
        return ocr_engine

    with ocr_lock:
        if ocr_engine is not None:
            return ocr_engine
        try:
            paddleocr_module = importlib.import_module('paddleocr')
            paddleocr_cls = getattr(paddleocr_module, 'PaddleOCR', None)
        except Exception:
            paddleocr_cls = None

        if paddleocr_cls is None:
            raise RuntimeError(
                '未安装PaddleOCR依赖，请先安装 paddleocr 与 paddlepaddle'
            )

        ocr_lang = 'ch'
        # 新版参数：use_textline_orientation；旧版参数：use_angle_cls
        # 优先关闭 mkldnn，避免部分版本在 CPU 推理出现 oneDNN/PIR 兼容问题
        ocr_engine = paddleocr_cls(
            use_textline_orientation=True,
            lang=ocr_lang,
            enable_mkldnn=False,
        )

        return ocr_engine


def extract_ocr_text(ocr_result) -> str:
    texts = []

    def append_text(value):
        if isinstance(value, str):
            current = value.strip()
            if current:
                texts.append(current)

    def walk(node):
        if node is None:
            return

        if isinstance(node, str):
            append_text(node)
            return

        if isinstance(node, dict):
            for key in ('rec_texts', 'texts', 'rec_text', 'text', 'transcription'):
                if key not in node:
                    continue
                value = node.get(key)
                if isinstance(value, (list, tuple)):
                    for item in value:
                        append_text(item)
                else:
                    append_text(value)

            for value in node.values():
                if isinstance(value, (dict, list, tuple)):
                    walk(value)
            return

        if isinstance(node, (list, tuple)):
            if len(node) >= 2 and isinstance(node[1], (list, tuple)) and node[1]:
                append_text(node[1][0])
            for item in node:
                walk(item)

    walk(ocr_result)

    merged = []
    seen = set()
    for text in texts:
        if text not in seen:
            seen.add(text)
            merged.append(text)

    return '\n'.join(merged).strip()


# 移除包含英文的行
def remove_english_lines(text: str) -> str:
    lines = text.splitlines()
    filtered = [
        line
        for line in lines
        if not (
            re.search(r"[A-Za-z]", line) and not re.search(r"[\u4e00-\u9fff]", line)
        )
    ]
    return "\n".join(filtered)


# 通知用户
def user_notify(user_id: str, message: str) -> None:
    """
    根据用户偏好发送通知（短信、邮件、微信等）

    Args:
        user: SysUser对象
        message: 通知内容

    Returns:
        None
    """
    notify_type = os.getenv('USER_NOTIFY_TYPE', 'none').lower()

    if notify_type == 'none':
        return

    db = SessionLocal()
    try:
        if 'sms' in notify_type:
            # 发送短信通知
            user = db.query(SysUser).filter(SysUser.id == user_id).first()
            if user and user.mobile:
                phone = user.mobile
                # 发送短信
                aliyun_sms_client.send_notify(phone)
                logger.info(
                    f"已发送短信通知给用户 {user.user_account}, 手机号 {phone}, 内容: {message}"
                )
    finally:
        db.close()


def cleanup_expired_sms_codes(now: datetime.datetime | None = None):
    """移除已过期的短信验证码，防止缓存膨胀。"""
    current = now or datetime.datetime.now()
    expired = [
        k
        for k, v in sms_code_cache.items()
        if v.get('expires_at') and v['expires_at'] <= current
    ]
    for key in expired:
        sms_code_cache.pop(key, None)


def generate_token(user_id: int, user_account: str) -> str:
    """
    生成JWT Token

    Args:
        user_id: 用户ID
        user_account: 用户账号

    Returns:
        str: JWT Token字符串
    """
    # 使用UTC时间，避免时区问题
    now_utc = get_current_utc_time()
    payload = {
        'user_id': user_id,
        'user_account': user_account,
        'exp': now_utc + app.config['JWT_EXPIRATION_DELTA'],
        'iat': now_utc,
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def session_id_from_token(token_value: str) -> str:
    """Create a stable 22-char base64url session_id from a token."""
    digest = hashlib.sha256(token_value.encode('utf-8')).digest()
    return base64.b32encode(digest[:16]).decode('ascii').rstrip('=')


def cleanup_expired_token_blacklist(now_ts: float | None = None) -> None:
    """移除已过期的黑名单token，防止缓存膨胀。"""
    current_ts = now_ts or time.time()
    with token_blacklist_lock:
        expired = [
            token
            for token, exp_ts in token_blacklist.items()
            if exp_ts is not None and exp_ts <= current_ts
        ]
        for token in expired:
            token_blacklist.pop(token, None)


def get_token_exp_timestamp(token: str) -> float | None:
    """解析token中的exp时间戳（秒），解析失败返回None。"""
    try:
        payload = jwt.decode(
            token,
            app.config['SECRET_KEY'],
            algorithms=['HS256'],
            options={'verify_exp': False},
        )
        exp = payload.get('exp')
        if isinstance(exp, datetime.datetime):
            return exp.timestamp()
        if isinstance(exp, (int, float)):
            return float(exp)
    except Exception:
        return None
    return None


def verify_token(token: str) -> dict:
    """
    验证JWT Token

    Args:
        token: JWT Token字符串

    Returns:
        dict: Token载荷，如果无效则返回None
    """
    # 先清理过期黑名单
    cleanup_expired_token_blacklist()
    # 检查token是否在黑名单中
    with token_blacklist_lock:
        if token in token_blacklist:
            return None
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """
    Token认证装饰器
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 从请求头获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                # 支持 "Bearer <token>" 格式
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            except IndexError:
                return jsonify({'code': 401, 'message': 'Token格式错误'}), 401

        if not token:
            return jsonify({'code': 401, 'message': '缺少Token'}), 401

        # 验证token
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'Token无效或已过期'}), 401

        # 将用户信息和token添加到请求上下文
        request.current_user = payload
        request.current_token = token  # 保存token以便后续使用（如加入黑名单）
        return f(*args, **kwargs)

    return decorated


def hash_password(password: str) -> str:
    """
    密码哈希（使用MD5，与数据库存储方式保持一致）
    注意：生产环境建议使用更安全的哈希算法如bcrypt

    Args:
        password: 原始密码

    Returns:
        str: 哈希后的密码
    """
    # return hashlib.md5(password.encode('utf-8')).hexdigest()
    return generate_password_hash(password, method='pbkdf2:sha256')


def cleanup_pdf_cache() -> None:
    now_ts = time.time()
    with pdf_download_lock:
        expired_tokens = [
            token
            for token, info in pdf_download_cache.items()
            if info.get('expires_at', 0) <= now_ts
        ]
        for token in expired_tokens:
            info = pdf_download_cache.pop(token, None)
            if info:
                try:
                    if os.path.exists(info['path']):
                        os.remove(info['path'])
                except Exception:
                    pass


@app.route('/api/register_user', methods=['GET', 'POST'])
def register_user():
    """
    用户注册接口

    请求参数:
        user: 用户名称
        pwd1: 输入密码
        pwd2: 确认密码
        phone: 手机号码

    返回:
        {
            "code": 200,
            "message": "注册成功，跳转到我的页" | "注册失败",
            "data": {}
        }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return (
                jsonify({'code': 400, 'message': '注册失败,参数不能为空', 'data': {}}),
                400,
            )

        user = data.get('user')
        pwd1 = data.get('pwd1')
        pwd2 = data.get('pwd2')
        phone = data.get('phone', '').strip()  # 获取手机号
        sms_code = str(data.get('sms_code', '')).strip()
        is_user_license = data.get('is_user_license', False)

        # 清理过期验证码
        cleanup_expired_sms_codes()

        # 获取邀请参数（来自URL query string）
        invite_code_param = request.args.get('invite', '').strip()
        if not invite_code_param and data:
            invite_code_param = str(data.get('invite', '')).strip()

        # 验证参数
        if not user or not pwd1 or not pwd2:
            return (
                jsonify({'code': 400, 'message': '注册失败,参数不能为空', 'data': {}}),
                400,
            )

        # 验证两次密码是否一致
        if pwd1 != pwd2:
            return (
                jsonify(
                    {
                        'code': 400,
                        'message': '注册失败,两次输入的密码不一致',
                        'data': {},
                    }
                ),
                400,
            )

        # 验证手机号格式 & 短信验证码
        if phone:
            phone_regex = r'^1[3-9]\d{9}$'
            if not re.match(phone_regex, phone):
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': '注册失败,手机号格式不正确',
                            'data': {},
                        }
                    ),
                    400,
                )

            # 短信验证码不能为空
            if not sms_code:
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': '注册失败,短信验证码不能为空',
                            'data': {},
                        }
                    ),
                    400,
                )

            cached = sms_code_cache.get(phone)
            if not cached:
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': '该手机号验证号无效，请重新获得',
                            'data': {},
                        }
                    ),
                    400,
                )

            # 检查是否过期
            if (
                cached.get('expires_at')
                and cached['expires_at'] <= datetime.datetime.now()
            ):
                sms_code_cache.pop(phone, None)
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': '该手机号验证号无效，请重新获得',
                            'data': {},
                        }
                    ),
                    400,
                )

            if cached.get('code') != sms_code:
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': '注册失败,验证码不正确',
                            'data': {},
                        }
                    ),
                    400,
                )

        # 校验是否同意协议
        if not is_user_license:
            return (
                jsonify(
                    {'code': 400, 'message': '用户没有同意注册及使用协议', 'data': {}}
                ),
                400,
            )

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 检查用户名是否已存在
            existing_user = (
                db.query(SysUser).filter(SysUser.user_account == user).first()
            )

            if existing_user:
                return (
                    jsonify(
                        {'code': 400, 'message': '注册失败,用户名已存在', 'data': {}}
                    ),
                    400,
                )
            # 检查手机号是否已被占用
            if phone:
                existing_mobile = (
                    db.query(SysUser).filter(SysUser.mobile == phone).first()
                )
                if existing_mobile:
                    return (
                        jsonify(
                            {
                                'code': 400,
                                'message': '注册失败,手机号码已存在',
                                'data': {},
                            }
                        ),
                        400,
                    )

            # 使用ID生成器生成唯一ID（类似 Yitter.IdGenerator）
            user_id = next_id()

            # 创建新用户
            hashed_pwd = hash_password(pwd1)
            new_user = SysUser(
                id=user_id,
                user_account=user,
                user_pwd=hashed_pwd,
                status=1,  # 状态：1正常
                admin_type=3,  # 账号类型：3普通账号
                account_credit=Decimal(
                    os.getenv('MEDICAL_ONE_CREDIT', '9.9')
                ),  # 账户余额默认为9.9
                create_time=datetime.datetime.now(),
                reg_ip=request.remote_addr,
                mobile=phone,  # 保存手机号
                is_user_license=is_user_license,  # 保存是否同意协议
            )

            # 注册成功后清理已使用的验证码
            if phone:
                sms_code_cache.pop(phone, None)

            db.add(new_user)
            db.commit()

            # 处理邀请逻辑
            if invite_code_param and len(invite_code_param) == 6:
                # 查询邀请者用户
                current_invite_user = (
                    db.query(SysUser)
                    .filter(SysUser.invite_code == invite_code_param)
                    .first()
                )

                if current_invite_user:
                    # 统计邀请者在当天的邀请记录数
                    '''
                    today_start = datetime.datetime.combine(
                        datetime.date.today(), datetime.time.min
                    )
                    today_end = datetime.datetime.combine(
                        datetime.date.today(), datetime.time.max
                    )
                    '''
                    today_start = get_current_local_time().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    today_end = today_start + datetime.timedelta(days=1)

                    today_invite_count = (
                        db.query(func.count(BasInviteRecord.id))
                        .filter(
                            BasInviteRecord.user_id == current_invite_user.id,
                            BasInviteRecord.invite_code == invite_code_param,
                            BasInviteRecord.invite_time >= today_start,
                            BasInviteRecord.invite_time <= today_end,
                        )
                        .scalar()
                    )

                    increase_cost = Decimal('0.0')
                    if today_invite_count < int(os.getenv('TODAY_INVITE_COUNT', '1')):
                        increase_cost = Decimal(
                            os.getenv('INVITE_REGISTER_CREDIT', '9.9')
                        )  # 每次诊断消耗的信誉度
                        current_invite_user.account_credit += increase_cost
                    # 创建邀请记录
                    tz_now = get_current_local_time()
                    new_invite_record = BasInviteRecord(
                        id=next_id(),
                        user_id=current_invite_user.id,
                        invite_code=invite_code_param,
                        invite_user_id=new_user.id,
                        invite_time=tz_now,
                        increase_cost=increase_cost,
                    )
                    db.add(new_invite_record)
                    db.commit()

            return (
                jsonify({'code': 200, 'message': '注册成功，跳转到我的页', 'data': {}}),
                200,
            )

        except Exception as e:
            db.rollback()
            return (
                jsonify({'code': 500, 'message': f'注册失败,{e}', 'data': {}}),
                500,
            )
        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'注册失败,{e}', 'data': {}}), 500


@app.route('/api/send_verify_sms_code', methods=['POST'])
def send_verify_sms_code():
    """
    发送短信验证码，验证码5分钟内有效。
    请求参数:
        phone: 手机号（必填）
    返回:
        {"status": "ok" | "err", "desc": ""}
    """
    try:
        cleanup_expired_sms_codes()
        data = request.get_json()
        if not data:
            return (
                jsonify({'code': 400, 'message': '发送失败,参数不能为空', 'data': {}}),
                400,
            )

        phone = str(data.get('phone', '')).strip()
        phone_regex = r'^1[3-9]\d{9}$'
        if not phone or not re.match(phone_regex, phone):
            return (
                jsonify(
                    {
                        'code': 400,
                        'message': '发送失败,手机号码格式不正确',
                        'data': {},
                    }
                ),
                400,
            )

        # 生成6位数字验证码并缓存，5分钟内有效
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        sms_code_cache[phone] = {'code': code, 'expires_at': expires_at}

        try:
            aliyun_sms_client.send_code(phone, code)
        except Exception as send_err:
            logger.exception('发送短信验证码失败')
            return (
                jsonify(
                    {
                        'code': 400,
                        'message': f'发送失败,{send_err}',
                        'data': {},
                    }
                ),
                400,
            )

        return (
            jsonify({'code': 200, 'message': '验证码已发送，5分钟内有效', 'data': {}}),
            200,
        )

    except Exception as e:
        logger.exception('发送验证码接口异常')
        return jsonify({'code': 500, 'message': f'发送失败,{e}', 'data': {}}), 500


@app.route('/api/login_user', methods=['POST'])
def login_user():
    """
    用户登录接口

    请求参数:
        user: 用户名称
        pwd: 用户密码

    返回:
        {
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": "jwt_token_string",
                "user_id": 1,
                "user_account": "username"
            }
        }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        user = data.get('user')
        pwd = data.get('pwd')

        if not user or not pwd:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 查询用户
            user_obj = db.query(SysUser).filter(SysUser.user_account == user).first()

            if not user_obj:
                return jsonify({'code': 401, 'message': '用户不存在'}), 401

            # 验证密码（假设数据库存储的是MD5哈希）
            # 如果数据库存储的是明文，直接比较；如果是哈希，需要先哈希再比较
            # hashed_pwd = hash_password(pwd)
            check_pass = check_password_hash(user_obj.user_pwd, pwd)
            # 检查密码是否匹配（支持MD5哈希和明文比较）
            if not check_pass:
                return jsonify({'code': 401, 'message': '用户密码错误'}), 401

            # 检查用户状态
            if user_obj.status != 1:
                return (
                    jsonify({'code': 403, 'message': '用户账号已被停用或审核中'}),
                    403,
                )

            # 生成Token
            token = generate_token(user_obj.id, user_obj.user_account)
            session_id = session_id_from_token(token)

            # 更新最后登录IP
            user_obj.last_login_ip = request.remote_addr
            # 更新最后登录信息（可选）
            user_obj.last_login_time = datetime.datetime.now()
            # 更新最后登录操作系统/UA
            user_obj.last_login_os = (
                request.user_agent.string if request.user_agent else ''
            )
            db.commit()

            load_dotenv(override=True)

            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '登录成功',
                        'data': {
                            'token': token,
                            'session_id': session_id,
                            'user_id': user_obj.id,
                            'user_account': user_obj.user_account,
                        },
                    }
                ),
                200,
            )

        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/login_out', methods=['POST'])
@token_required
def login_out():
    """
    用户退出接口

    请求头:
        Authorization: Bearer <token>

    返回:
        {
            "code": 200,
            "message": "退出成功"
        }
    """
    try:
        # 从请求上下文中获取token（已在token_required装饰器中解析）
        token = getattr(request, 'current_token', None)

        # 如果装饰器中没有保存token，则从请求头获取
        if not token and 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            except IndexError:
                pass

        # 将token加入黑名单，使其失效
        if token:
            exp_ts = get_token_exp_timestamp(token)
            with token_blacklist_lock:
                token_blacklist[token] = exp_ts or (time.time() + 24 * 3600)
            cleanup_expired_token_blacklist()

        current_user = getattr(request, 'current_user', {}) or {}
        logger.info(f"login_out success: user_id={current_user.get('user_id')}")
        return jsonify({'code': 200, 'message': '退出成功'}), 200

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


'''
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({'code': 200, 'message': '服务运行正常'}), 200
'''


@app.route('/api/change_password', methods=['POST'])
@token_required
def change_password():
    """
    修改密码接口

    请求头:
        Authorization: Bearer <token>

    请求参数:
        user: 用户名称
        new_pwd: 新密码

    返回:
        {
            "code": 200,
            "message": "密码修改成功"
        }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        user = data.get('user')
        old_pwd = data.get('old_pwd')
        new_pwd = data.get('new_pwd')

        if not user or not old_pwd or not new_pwd:
            return (
                jsonify({'code': 400, 'message': '用户名、旧密码和新密码不能为空'}),
                400,
            )

        # 从token中获取当前用户信息
        current_user = request.current_user
        if not current_user or current_user.get('user_account') != user:
            return jsonify({'code': 403, 'message': '无权修改此用户的密码'}), 403

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 查询用户
            user_obj = db.query(SysUser).filter(SysUser.user_account == user).first()

            if not user_obj:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            # 校验旧密码
            if not check_password_hash(user_obj.user_pwd, old_pwd):
                return jsonify({'code': 401, 'message': '旧密码错误'}), 401

            # 哈希新密码
            hashed_pwd = hash_password(new_pwd)

            # 更新密码
            user_obj.user_pwd = hashed_pwd
            db.commit()

            logger.info(f"change_password success: user={user}")
            return jsonify({'code': 200, 'message': '密码修改成功'}), 200

        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/get_medicalrecords', methods=['GET'])
@token_required
def get_medicalrecords():
    """
    获取用户的诊断记录

    请求头:
        Authorization: Bearer <token>
    可选查询参数:
        status: 分析状态，取值为 "全部" | "0" | "1" | "-1"，默认为全部
        keyword: 关键字（在 prompt_txt 或 result 中模糊匹配）
        page: 页码，默认为1
        page_size: 每页记录数，默认为10

    返回:
        {
            "code": 200,
            "message": "获取成功",
            "data": [
                {
                    "id": 1,
                    "user_id": 1,
                    "prompt_txt": "症状描述",
                    "prompt_img": "image/path.jpg",
                    "result": "分析结果",
                    "sdt": "2023-01-01T12:00:00"
                }
            ],
            "total": 100,
            "page": 1,
            "page_size": 10
        }
    """
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 解析查询参数
            status_param = request.args.get('status', default=None, type=str)
            keyword_param = request.args.get('keyword', default=None, type=str)
            page = request.args.get('page', default=1, type=int)
            page_size = request.args.get('page_size', default=10, type=int)

            # 验证分页参数
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 10
            if page_size > 100:
                page_size = 100

            # 规范化状态参数
            status_filter = None
            if status_param and status_param.strip() != '' and status_param != '全部':
                try:
                    status_filter = int(status_param)
                except Exception:
                    status_filter = None

            # 规范化关键字参数
            keyword_val = (keyword_param or '').strip()

            # 构建查询
            query = db.query(BasMedical).filter(
                BasMedical.user_id == user_id,
                BasMedical.is_delete.is_(False),
            )
            if status_filter is not None:
                query = query.filter(BasMedical.medical_status == status_filter)
            if keyword_val:
                like_expr = f"%{keyword_val}%"
                query = query.filter(
                    or_(
                        BasMedical.prompt_txt.like(like_expr),
                        BasMedical.result.like(like_expr),
                    )
                )

            # 获取总记录数
            total = query.count()

            # 按 id 降序排序并分页
            records = (
                query.order_by(BasMedical.sdt.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            # 转换为字典列表
            data = [record.to_dict() for record in records]

            for item in data:
                try:
                    # 处理耗时：对于进行中的任务，使用当前时间计算并保留两位小数
                    sdt_str = item.get('sdt')
                    edt_str = item.get('edt')
                    status = item.get('medical_status')
                    sdt_dt = (
                        datetime.datetime.fromisoformat(sdt_str) if sdt_str else None
                    )
                    if status == 1 and not edt_str and sdt_dt:
                        now_dt = datetime.datetime.now()
                        item['elapsed_time'] = round(
                            (now_dt - sdt_dt).total_seconds() / 60.0, 2
                        )

                    # 检查并处理图像
                    if item['prompt_img']:
                        # 假设prompt_img是相对于项目根目录的路径
                        img_path = os.path.join(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            item['prompt_img'],
                        )
                        if os.path.exists(img_path):
                            try:
                                with open(img_path, 'rb') as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode(
                                        'utf-8'
                                    )
                                    # 假设是JPEG，实际可根据文件扩展名判断
                                    item['image_data'] = (
                                        f"data:image/jpeg;base64,{img_base64}"
                                    )
                            except Exception as e:
                                logger.error(f"读取图像失败: {e}")
                                item['image_data'] = None
                        else:
                            item['image_data'] = None
                    else:
                        item['image_data'] = None
                except Exception as time_err:
                    item['elapsed_time'] = 0.0
                    item['image_data'] = None
                    logger.error(f"计算耗时失败: {time_err}")

            logger.info(
                f"get_medicalrecords success: user_id={user_id}, total={total}, page={page}, page_size={page_size}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '获取成功',
                        'data': data,
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                    }
                ),
                200,
            )

        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/delete_medicalrecord', methods=['DELETE'])
@token_required
def delete_medicalrecord():
    """
    删除诊断记录

    请求头:
        Authorization: Bearer <token>

    请求参数:
        id: 记录ID

    返回:
        {
            "code": 200,
            "message": "删除成功"
        }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        record_id = data.get('id')
        if not record_id:
            return jsonify({'code': 400, 'message': '记录ID不能为空'}), 400

        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 查询记录，确保属于当前用户
            record = (
                db.query(BasMedical)
                .filter(BasMedical.id == record_id, BasMedical.user_id == user_id)
                .first()
            )

            if not record:
                return jsonify({'code': 404, 'message': '记录不存在或无权删除'}), 404

            if record.medical_status == 1:
                # 1小时内，若仍在分析中，则不允许删除
                if record.sdt:
                    now_dt = get_current_local_time()
                    time_diff_seconds = abs((now_dt - record.sdt).total_seconds())
                    if time_diff_seconds <= 3600:
                        return (
                            jsonify(
                                {
                                    'code': 400,
                                    'message': '当前分析任务正在进行中，无法执行删除操作',
                                }
                            ),
                            400,
                        )
                    else:
                        record.is_delete = True
            else:  # record.medical_status != 1
                record.is_delete = True
            # 软删除记录

            if record.is_delete:
                # 删除后重置用户当前诊断记录ID
                db.query(SysUser).filter(SysUser.id == user_id).update(
                    {SysUser.current_medical_id: None}
                )

            db.commit()

            logger.info(
                f"delete_medicalrecord success: user_id={user_id}, record_id={record_id}"
            )
            return jsonify({'code': 200, 'message': '删除成功'}), 200

        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/upload_medicalrecord_pdf', methods=['POST'])
@token_required
def upload_medicalrecord_pdf():
    """
    上传PDF文件（Base64），返回下载链接

    请求头:
        Authorization: Bearer <token>

    请求参数(JSON):
        filename: 文件名（可选）
        file_base64: Base64字符串（可包含data:application/pdf;base64,前缀）

    返回:
        {
            "code": 200,
            "message": "上传成功",
            "data": {
                "download_url": "..."
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        file_base64 = data.get('file_base64')
        filename = data.get('filename') or f"medical_record_{int(time.time())}.pdf"
        if not file_base64:
            return jsonify({'code': 400, 'message': '文件内容不能为空'}), 400

        # 清理缓存
        cleanup_pdf_cache()

        # 兼容 data URI
        if ',' in file_base64:
            file_base64 = file_base64.split(',', 1)[1]

        try:
            file_bytes = base64.b64decode(file_base64)
        except Exception:
            return jsonify({'code': 400, 'message': '文件内容解码失败'}), 400

        token = secrets.token_urlsafe(24)
        file_path = os.path.join(PDF_DOWNLOAD_DIR, f"{token}.pdf")
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        expires_at = time.time() + 10 * 60
        with pdf_download_lock:
            pdf_download_cache[token] = {
                'path': file_path,
                'filename': filename,  # 保留原始文件名（含中文）
                'expires_at': expires_at,
            }

        download_url = (
            request.host_url.rstrip('/')
            + f"/api/download_medicalrecord_pdf?token={token}"
        )

        current_user = getattr(request, 'current_user', {}) or {}
        logger.info(
            f"upload_medicalrecord_pdf success: user_id={current_user.get('user_id')}, filename={filename}"
        )
        return (
            jsonify(
                {
                    'code': 200,
                    'message': '上传成功',
                    'data': {'download_url': download_url},
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/download_medicalrecord_pdf', methods=['GET'])
def download_medicalrecord_pdf():
    """
    下载PDF文件（通过临时token）
    """
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({'code': 400, 'message': '缺少token'}), 400

        cleanup_pdf_cache()

        with pdf_download_lock:
            info = pdf_download_cache.get(token)

        if not info or not os.path.exists(info['path']):
            return jsonify({'code': 404, 'message': '文件不存在或已过期'}), 404

        # 对中文文件名进行 URL 编码以支持下载
        filename = info.get('filename') or 'medical_record.pdf'
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))

        response = send_file(
            info['path'],
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )
        # 设置 Content-Disposition 响应头以支持中文文件名
        response.headers['Content-Disposition'] = (
            f"attachment; filename*=UTF-8''{encoded_filename}"
        )
        return response

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/get_medicalchatrecods', methods=['GET'])
@token_required
def get_medicalchatrecods():
    """
    获取用户的问诊会话记录
    """
    try:
        current_user = request.current_user
        user_id = current_user.get('user_id') if current_user else None
        if not user_id:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=20, type=int)

        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100

        db = SessionLocal()
        try:
            base_filter = [
                BasMedicalChat.user_id == user_id,
                or_(
                    BasMedicalChat.is_delete.is_(False),
                    BasMedicalChat.is_delete.is_(None),
                ),
            ]

            total = (
                db.query(func.count(BasMedicalChat.id)).filter(*base_filter).scalar()
            )

            min_msg_subq = (
                db.query(
                    BasMedicalChatMessages.chat_id.label('chat_id'),
                    func.min(BasMedicalChatMessages.sdt).label('min_sdt'),
                )
                .group_by(BasMedicalChatMessages.chat_id)
                .subquery()
            )

            msg_alias = aliased(BasMedicalChatMessages)
            records = (
                db.query(BasMedicalChat, msg_alias.prompt_txt)
                .outerjoin(min_msg_subq, BasMedicalChat.id == min_msg_subq.c.chat_id)
                .outerjoin(
                    msg_alias,
                    (msg_alias.chat_id == min_msg_subq.c.chat_id)
                    & (msg_alias.sdt == min_msg_subq.c.min_sdt),
                )
                .filter(*base_filter)
                .order_by(BasMedicalChat.chat_sdt_time.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            data = []
            for chat, prompt_txt in records:
                data.append(
                    {
                        'id': chat.id,
                        'chat_sdt_time': (
                            chat.chat_sdt_time.isoformat()
                            if chat.chat_sdt_time
                            else None
                        ),
                        'chat_edt_time': (
                            chat.chat_edt_time.isoformat()
                            if chat.chat_edt_time
                            else None
                        ),
                        'prompt_txt': prompt_txt or '',
                    }
                )

            logger.info(
                f"get_medicalchatrecods success: user_id={user_id}, total={int(total or 0)}, page={page}, page_size={page_size}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '获取成功',
                        'data': data,
                        'total': int(total or 0),
                        'page': page,
                        'page_size': page_size,
                    }
                ),
                200,
            )
        finally:
            db.close()
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/get_medicalchatrecod_messages', methods=['GET'])
@token_required
def get_medicalchatrecod_messages():
    """
    获取问诊会话消息
    """
    try:
        current_user = request.current_user
        user_id = current_user.get('user_id') if current_user else None
        if not user_id:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        chat_id = request.args.get('chat_id', '').strip()
        if not chat_id:
            return jsonify({'code': 400, 'message': '缺少chat_id'}), 400

        db = SessionLocal()
        try:
            chat = (
                db.query(BasMedicalChat)
                .filter(BasMedicalChat.id == chat_id, BasMedicalChat.user_id == user_id)
                .first()
            )
            if not chat:
                return jsonify({'code': 404, 'message': '会话不存在或无权访问'}), 404

            messages = (
                db.query(BasMedicalChatMessages)
                .filter(BasMedicalChatMessages.chat_id == chat_id)
                .order_by(BasMedicalChatMessages.sdt.asc())
                .all()
            )

            data = [msg.to_dict() for msg in messages]

            logger.info(
                f"get_medicalchatrecod_messages success: user_id={user_id}, chat_id={chat_id}, count={len(data)}"
            )
            return (
                jsonify({'code': 200, 'message': '获取成功', 'data': data}),
                200,
            )
        finally:
            db.close()
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/delete_medicalchatrecod', methods=['DELETE'])
@token_required
def delete_medicalchatrecod():
    """
    软删除问诊会话记录
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        chat_id = data.get('id')
        if not chat_id:
            return jsonify({'code': 400, 'message': '会话ID不能为空'}), 400

        current_user = request.current_user
        user_id = current_user.get('user_id') if current_user else None

        db = SessionLocal()
        try:
            chat = (
                db.query(BasMedicalChat)
                .filter(BasMedicalChat.id == chat_id, BasMedicalChat.user_id == user_id)
                .first()
            )
            if not chat:
                return jsonify({'code': 404, 'message': '会话不存在或无权删除'}), 404

            chat.is_delete = True
            db.commit()
            logger.info(
                f"delete_medicalchatrecod success: user_id={user_id}, chat_id={chat_id}"
            )
            return jsonify({'code': 200, 'message': '删除成功'}), 200
        finally:
            db.close()
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/upload_medicalchatrecord_pdf', methods=['POST'])
@token_required
def upload_medicalchatrecord_pdf():
    """
    上传问诊记录PDF文件（Base64），返回下载链接
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        file_base64 = data.get('file_base64')
        filename = data.get('filename') or f"medical_chat_record_{int(time.time())}.pdf"
        if not file_base64:
            return jsonify({'code': 400, 'message': '文件内容不能为空'}), 400

        cleanup_pdf_cache()

        if ',' in file_base64:
            file_base64 = file_base64.split(',', 1)[1]

        try:
            file_bytes = base64.b64decode(file_base64)
        except Exception:
            return jsonify({'code': 400, 'message': '文件内容解码失败'}), 400

        token = secrets.token_urlsafe(24)
        file_path = os.path.join(PDF_CHAT_DOWNLOAD_DIR, f"{token}.pdf")
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        expires_at = time.time() + 10 * 60
        with pdf_download_lock:
            pdf_download_cache[token] = {
                'path': file_path,
                'filename': filename,
                'expires_at': expires_at,
            }

        download_url = (
            request.host_url.rstrip('/')
            + f"/api/download_medicalchatrecord_pdf?token={token}"
        )

        current_user = getattr(request, 'current_user', {}) or {}
        logger.info(
            f"upload_medicalchatrecord_pdf success: user_id={current_user.get('user_id')}, filename={filename}"
        )
        return (
            jsonify(
                {
                    'code': 200,
                    'message': '上传成功',
                    'data': {'download_url': download_url},
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/download_medicalchatrecord_pdf', methods=['GET'])
def download_medicalchatrecord_pdf():
    """
    下载问诊记录PDF文件（通过临时token）
    """
    try:
        token = request.args.get('token')
        if not token:
            return jsonify({'code': 400, 'message': '缺少token'}), 400

        cleanup_pdf_cache()

        with pdf_download_lock:
            info = pdf_download_cache.get(token)

        if not info or not os.path.exists(info['path']):
            return jsonify({'code': 404, 'message': '文件不存在或已过期'}), 404

        filename = info.get('filename') or 'medical_chat_record.pdf'
        encoded_filename = urllib.parse.quote(filename.encode('utf-8'))

        response = send_file(
            info['path'],
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )
        response.headers['Content-Disposition'] = (
            f"attachment; filename*=UTF-8''{encoded_filename}"
        )
        return response
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/medical_chat_ocr', methods=['POST'])
@token_required
def medical_chat_ocr():
    """
    病情问诊附件OCR识别接口（multipart/form-data）

    表单参数:
        file: 图片文件（png/jpg/jpeg, <=2MB）
    """
    try:
        current_user = request.current_user or {}
        current_user_id = current_user.get('user_id')
        user_account = current_user.get('user_account')
        if not current_user_id or not user_account:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        db = SessionLocal()
        try:
            user_check = db.query(SysUser).filter(SysUser.id == current_user_id).first()
            if not user_check:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404
            if user_check.status != 1:
                return (
                    jsonify({'code': 403, 'message': '用户账号已被停用或审核中'}),
                    403,
                )
        finally:
            db.close()

        upload_file = request.files.get('file')
        if not upload_file:
            return jsonify({'code': 400, 'message': '缺少附件文件'}), 400

        original_filename = upload_file.filename or ''
        if not original_filename.strip():
            return jsonify({'code': 400, 'message': '附件文件名无效'}), 400

        _, ext = os.path.splitext(original_filename)
        ext_lower = ext.lower()
        allowed_ext = {'.png', '.jpg', '.jpeg'}
        if ext_lower not in allowed_ext:
            return jsonify({'code': 415, 'message': '仅支持png/jpg/jpeg格式图片'}), 415

        # 文件大小限制2MB
        upload_file.stream.seek(0, os.SEEK_END)
        file_size = upload_file.stream.tell()
        upload_file.stream.seek(0)
        max_size_bytes = 2 * 1024 * 1024
        if file_size > max_size_bytes:
            return jsonify({'code': 413, 'message': '上传的图片需小于2MB'}), 413

        # 二次校验图片内容有效性
        try:
            image = Image.open(upload_file.stream)
            image.verify()
            upload_file.stream.seek(0)
        except (UnidentifiedImageError, OSError):
            return jsonify({'code': 400, 'message': '图片文件无效或已损坏'}), 400

        # backend/medical/yyyyMMdd/user_account
        base_medical_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'medical'
        )
        day_str = get_current_local_time().strftime('%Y%m%d')
        user_dir_name = sanitize_user_dir_name(user_account)
        target_dir = os.path.join(base_medical_dir, day_str, user_dir_name)
        os.makedirs(target_dir, exist_ok=True)

        # yyyyMMddHHmmssSSS_ocr + 原始扩展名
        ts_millis = get_current_local_time().strftime('%Y%m%d%H%M%S%f')[:-3]
        save_filename = f'{ts_millis}_ocr{ext}'
        save_path = os.path.join(target_dir, save_filename)
        upload_file.save(save_path)

        ocr_engine_inst = get_ocr_engine()
        ocr_result = ocr_engine_inst.ocr(save_path)
        ocr_text = get_limit_text(extract_ocr_text(ocr_result))

        if not ocr_text:
            return jsonify({'code': 400, 'message': '未识别到可用文字内容'}), 400

        logger.info(
            f"medical_chat_ocr success: user_id={current_user_id}, file={save_filename}, text_len={len(ocr_text)}"
        )
        return (
            jsonify(
                {
                    'code': 200,
                    'message': '识别成功',
                    'data': {'ocr_text': ocr_text},
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f'medical_chat_ocr failed: {e}')
        return jsonify({'code': 500, 'message': f'OCR识别失败: {str(e)}'}), 500


def call_doubao_api(prompt_txt: str, deep_thinking: bool) -> str:
    api_key = os.getenv('DOUBAO_API_KEY')
    if not api_key:
        raise ValueError('大模型API密钥未配置')

    api_url = os.getenv(
        'DOUBAO_API_URL', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
    )
    model = os.getenv('DOUBAO_MODEL', 'doubao-1-5-pro-32k-250115')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt_txt}],
        #'temperature': 0.7 if deep_thinking else 0.3,
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    result = (
        data.get('choices', [{}])[0].get('message', {}).get('content')
        or data.get('result')
        or data.get('data', {}).get('result')
        or data.get('data', {}).get('content')
    )
    if not result:
        raise ValueError('大模型返回结果为空')
    return result


def call_doubao_openai(prompt_txt: str, deep_thinking: bool):
    api_key = os.getenv('DOUBAO_API_KEY')
    if not api_key:
        raise ValueError('大模型API密钥未配置')
    # doubao-1-5-pro-256k-250115 doubao-1-5-pro-32k-250115
    model = os.getenv('DOUBAO_MODEL', 'doubao-1-5-pro-32k-250115')
    temperature = 0.7 if deep_thinking else 0.3
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )

    system_prompt = "你是一位专业的人工智能医学专家，请分析病情、推测病因、给出检查建议、制定治疗方案。回答时请尽可能详细，分点列出，提供相关的医学知识科普。对于用户的病情描述，先分析可能涉及的症状和病因，再给出检查建议和治疗方案。回答中可以包含医学术语，但请尽量通俗易懂地解释。"

    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config',
        'chat_template.txt',
    )
    if os.path.exists(template_path):
        template_content = read_file_content(template_path, False)
        if template_content:
            system_prompt = template_content

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'system',
                'content': system_prompt,
            },
            {'role': 'user', 'content': prompt_txt},
        ],
        temperature=temperature,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


@app.route('/api/medical_chat', methods=['POST'])
@token_required
def medical_chat():
    """
    病情问诊接口（豆包）

    请求头:
        Authorization: Bearer <token>

    请求参数:
        prompt_txt: 病情描述
        deep_thinking: 是否启用深度思考（可选）

    返回:
        {
            "code": 200,
            "message": "问诊成功",
            "data": {
                "result": "问诊结果"
            }
        }
    """
    try:
        current_user = request.current_user
        current_user_id = current_user.get('user_id') if current_user else None
        user_account = current_user.get('user_account') if current_user else None
        if not current_user_id:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        db = SessionLocal()
        try:
            user_check = db.query(SysUser).filter(SysUser.id == current_user_id).first()
            if not user_check:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404
            if user_check.status != 1:
                return (
                    jsonify({'code': 403, 'message': '用户账号已被停用或审核中'}),
                    403,
                )
        finally:
            db.close()

        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        prompt_txt = (data.get('prompt_txt') or '').strip()
        deep_thinking = bool(data.get('deep_thinking', True))
        session_id = (data.get('session_id') or '').strip()

        if not prompt_txt:
            return jsonify({'code': 400, 'message': '病情描述不能为空'}), 400

        if not session_id:
            token_value = getattr(request, 'current_token', '')
            if token_value:
                session_id = session_id_from_token(token_value)
            else:
                return jsonify({'code': 400, 'message': '缺少session_id'}), 400

        # 过滤词检测
        filter_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config',
            'consultation_filter.txt',
        )
        if os.path.exists(filter_path):
            filter_content = read_file_content(filter_path, False)

            filter_terms = []
            for line in (filter_content or '').splitlines():
                line_norm = unicodedata.normalize('NFKC', line or '')
                line_norm = line_norm.replace('\ufeff', '').strip()
                if not line_norm or line_norm.startswith('#'):
                    continue
                for part in re.split(r"[,，、;；]\s*", line_norm):
                    part_norm = unicodedata.normalize('NFKC', part or '')
                    part_norm = part_norm.replace('\ufeff', '').strip()
                    if part_norm:
                        filter_terms.append(part_norm)

            if filter_terms:
                prompt_norm = unicodedata.normalize('NFKC', prompt_txt or '')
                prompt_norm = prompt_norm.replace('\ufeff', '').strip()
                prompt_lower = prompt_norm.lower()
                prompt_tokens = [
                    token.strip()
                    for token in jieba.lcut(prompt_lower)
                    if token.strip() and len(token.strip()) > 1
                ]

                matched_terms = []
                for term in filter_terms:
                    term_norm = unicodedata.normalize('NFKC', term or '')
                    term_norm = term_norm.replace('\ufeff', '').strip()
                    if not term_norm:
                        continue
                    term_lower = term_norm.lower()
                    if prompt_lower == term_lower:
                        matched_terms.append(term_norm)
                        continue
                    if term_lower in prompt_lower:
                        matched_terms.append(term_norm)
                        continue
                    if term_lower and prompt_tokens:
                        for token in prompt_tokens:
                            if token.startswith(term_lower) or term_lower.startswith(
                                token
                            ):
                                matched_terms.append(term_norm)
                                break

                if matched_terms:
                    return Response(
                        '我是专业医疗Ai，无法提供其他方面的回答。',
                        mimetype='text/plain; charset=utf-8',
                    )

        chat_id = None
        message_id = None
        db = SessionLocal()
        try:
            existing_chat = (
                db.query(BasMedicalChat)
                .filter(BasMedicalChat.session_id == session_id)
                .first()
            )
            if existing_chat:
                if existing_chat.user_id != current_user_id:
                    return jsonify({'code': 403, 'message': '会话不属于当前用户'}), 403
                chat_id = existing_chat.id
            else:
                chat_id = next_id()
                new_chat = BasMedicalChat(
                    id=chat_id,
                    session_id=session_id,
                    user_id=current_user_id,
                    chat_sdt_time=get_current_local_time(),
                )
                db.add(new_chat)
                db.commit()

            message_id = next_id()
            new_message = BasMedicalChatMessages(
                id=message_id,
                chat_id=chat_id,
                prompt_txt=prompt_txt,
                result='',
                sdt=get_current_local_time(),
                state=-1,
            )
            db.add(new_message)
            db.commit()
        finally:
            db.close()

        def generate():
            db = SessionLocal()
            message = None
            current_result = ''
            try:
                message = (
                    db.query(BasMedicalChatMessages)
                    .filter(BasMedicalChatMessages.id == message_id)
                    .first()
                )
                # 返回生成结果的增量部分，并实时更新数据库中的记录
                for delta in call_doubao_openai(prompt_txt, deep_thinking):
                    current_result += delta
                    if message:
                        message.result = get_limit_text(current_result)
                        message.edt = get_current_local_time()
                        db.commit()
                    yield delta
                logger.info(f"{user_account} 问诊完成，结果长度: {len(current_result)}")
                if message:
                    message.result = get_limit_text(current_result)
                    message.edt = get_current_local_time()
                    message.state = 0
                    db.commit()
                # 更新问诊聊天记录的最后更新时间
                if chat_id:
                    chat = (
                        db.query(BasMedicalChat)
                        .filter(BasMedicalChat.id == chat_id)
                        .first()
                    )
                    if chat:
                        chat.chat_edt_time = get_current_local_time()
                        db.commit()
            except Exception as e:
                if message:
                    message.result = get_limit_text(current_result)
                    message.edt = get_current_local_time()
                    message.state = -1
                    message.error = str(e)
                    db.commit()
                # 即使问诊失败，也更新聊天记录的更新时间，避免用户长时间看到“正在问诊”的状态
                if chat_id:
                    chat = (
                        db.query(BasMedicalChat)
                        .filter(BasMedicalChat.id == chat_id)
                        .first()
                    )
                    if chat:
                        chat.chat_edt_time = get_current_local_time()
                        db.commit()
                logger.error(f"调用大模型API失败: {e}")
                yield '\n问诊暂时不可用，请稍后重试。'
            finally:
                db.close()

        logger.info(
            f"medical_chat start streaming: user_id={current_user_id}, chat_id={chat_id}, session_id={session_id}"
        )
        return Response(
            stream_with_context(generate()),
            mimetype='text/plain; charset=utf-8',
        )
    except Exception as e:
        logger.error(f"豆包问诊失败: {e}")
        return jsonify({'code': 500, 'message': '问诊暂时不可用，请稍后重试'}), 500

    # 其他通知方式（如邮件、微信）可在此扩展


@app.route('/api/medical', methods=['POST'])
@token_required
def medical():
    """
    提交诊断接口

    请求头:
        Authorization: Bearer <token>

    请求参数:
        prompt_txt: 医学文字
        image_data: base64编码的图像数据（可选）

    返回:
        {
            "code": 200,
            "message": "诊断提交成功",
            "data": {
                "result": "分析结果"
            }
        }
    """
    db = SessionLocal()
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        current_user_id = current_user.get('user_id')
        user_account = current_user.get('user_account')

        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        current_prompt_txt = data.get('prompt_txt')
        image_data = data.get('image_data')  # base64 data

        if not current_prompt_txt:
            return jsonify({'code': 400, 'message': '医学文字不能为空'}), 400

        # 检查用户是否有正在执行的任务
        user_check = db.query(SysUser).filter(SysUser.id == current_user_id).first()
        if not user_check:
            return jsonify({'code': 500, 'message': '检测用户信息错误'}), 500

        if user_check and user_check.current_medical_id:
            return jsonify({'code': 400, 'message': '当前用户已经有任务正在执行'}), 400

        # 检查并发队列
        with lock:
            medical_queue_limit = int(os.getenv('MEDICAL_QUEUE_SIZE', '5'))
            # 统计当前正在执行的任务数量（current_medical_id 不为空）
            active_count = (
                db.query(func.count(SysUser.id))
                .filter(SysUser.current_medical_id.isnot(None))
                .scalar()
            )

            if active_count >= medical_queue_limit:
                return (
                    jsonify({'code': 429, 'message': '当前排队人数过多，请稍后再试'}),
                    429,
                )

        one_credit = Decimal(
            os.getenv('MEDICAL_ONE_CREDIT', '9.9')
        )  # 每次诊断消耗的算力点
        # 判断当前捐赠算力点，如果小于9.9，则返回
        if user_check and user_check.account_credit < one_credit:
            return (
                jsonify(
                    {
                        'code': 400,
                        'message': f'当前赞助信用额为{user_check.account_credit}，每次使用为{one_credit}，请到[ 我的 ]菜单捐赠。',
                    }
                ),
                400,
            )

        # 处理图像
        current_prompt_img = ""
        if image_data:
            # 保存图像
            try:
                # 移除data:image/jpeg;base64,前缀
                if ',' in image_data:
                    header, encoded = image_data.split(',', 1)
                    img_data = base64.b64decode(encoded)
                else:
                    img_data = base64.b64decode(image_data)

                # 获取文件扩展名，假设是jpeg
                ext = 'jpg'
                if 'png' in header:
                    ext = 'png'
                elif 'gif' in header:
                    ext = 'gif'

                # 创建目录
                today = datetime.datetime.now().strftime('%Y%m%d')
                user_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'backend',
                    'medical',
                    today,
                    user_account,
                )
                os.makedirs(user_dir, exist_ok=True)

                # 生成文件名
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[
                    :-3
                ]  # 毫秒
                filename = f"{timestamp}.{ext}"
                filepath = os.path.join(user_dir, filename)

                # 保存文件
                with open(filepath, 'wb') as f:
                    f.write(img_data)

                current_prompt_img = os.path.join(
                    'backend\\medical', today, user_account, filename
                )

            except Exception as e:
                logger.error(f"保存图像失败: {e}")
                # 继续处理，不中断

        # 使用ID生成器生成唯一记录ID
        record_id = next_id()
        # 调用AI模型进行诊断
        try:
            # 创建记录开始时间
            start_time = datetime.datetime.now()
            new_record = BasMedical(
                id=record_id,
                user_id=current_user_id,
                prompt_txt=current_prompt_txt,
                prompt_img=current_prompt_img,
                sdt=start_time,
                credit=0,
                medical_status=1,  # 当前分析状态：0分析成功、1正在分析、-1分析异常
                medical_status_desc="正在分析",
                elapsed_time=0.0,  # 分析用时，整数部分是分钟，小数部分是秒钟
                # result=current_result,
                # edt=end_time,
            )
            db.add(new_record)

            # 更新用户的current_medical_id字段
            # user = db.query(SysUser).filter(SysUser.id == current_user_id).first()
            user_check.current_medical_id = record_id
            db.commit()

            logger.info(f"{user_account},开始进行AI模型诊断...")
            current_prompt_txt_cn = current_prompt_txt + " 请用中文回复。"

            current_result = medical_model.medical(
                user_name=user_account,
                prompt_text=current_prompt_txt_cn,
                image_path=current_prompt_img,
            )

            # 移除英文行并限制结果长度
            current_result = remove_english_lines(current_result)
            current_result = get_limit_text(current_result)
            # 更新记录
            new_record.result = current_result
            new_record.edt = datetime.datetime.now()
            new_record.credit = 0 - one_credit
            new_record.medical_status = 0
            new_record.medical_status_desc = "分析成功"
            new_record.elapsed_time = round(
                (new_record.edt - new_record.sdt).total_seconds() / 60.0, 2
            )
            # 扣除用户捐赠账户余额并清除当前任务ID
            user_check.current_medical_id = None  # 清除当前任务ID
            user_check.account_credit -= one_credit
            if user_check.account_credit < 0:
                user_check.account_credit = 0.0
            db.commit()

            user_notify(
                current_user_id,
                f"您的医学分析请求已完成，请前往查看结果。",
            )
            logger.info(
                f"medical success: user_id={current_user_id}, record_id={record_id}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '分析成功',
                        'data': {'result': current_result},
                    }
                ),
                200,
            )
        except Exception as e:
            logger.error(f"分析失败: {e}")

            try:
                new_record.medical_status = -1
                new_record.medical_status_desc = f"分析异常：{e}"
                # 清除当前任务ID
                # user = db.query(SysUser).filter(SysUser.id == current_user_id).first()
                user_check.current_medical_id = None
                db.commit()

            except Exception as cleanup_error:
                logger.error(f"清理失败: {cleanup_error}")

            return (
                jsonify({'code': 500, 'message': f'分析暂时不可用，请稍后重试:{e}'}),
                500,
            )

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500
    finally:
        db.close()


@app.route('/api/get_myinfo', methods=['GET'])
@token_required
def get_myinfo():
    """
    获取我的信息接口

    请求头:
        Authorization: Bearer <token>

    返回:
        {
            "code": 200,
            "data": {
                "user_account": "用户名",
                "account_credit": 0.0,
                "create_time": "2025-01-15 12:12:12",
                "status": "正常",
                "mobile": "",
                "email": "",
                "medical_count": 10,
                "cost_sum": -99.0
            }
        }
    """
    try:
        current_user = request.current_user
        current_user_id = current_user.get('user_id')

        db = SessionLocal()
        try:
            user = db.query(SysUser).filter(SysUser.id == current_user_id).first()
            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            # 统计用户的医学诊断记录
            medical_stats = (
                db.query(
                    func.count(BasMedical.id),
                    func.coalesce(
                        cast(func.sum(BasMedical.credit), Numeric(10, 2)), 0.0
                    ),
                )
                .filter(BasMedical.user_id == current_user_id)
                .first()
            )

            medical_count = (
                int(medical_stats[0])
                if medical_stats and medical_stats[0] is not None
                else 0
            )
            raw_cost_sum = (
                float(medical_stats[1])
                if medical_stats and medical_stats[1] is not None
                else 0.0
            )
            cost_sum = float(
                Decimal(str(raw_cost_sum)).quantize(
                    Decimal('0.00'), rounding=ROUND_DOWN
                )
            )

            cash = float(
                Decimal(str(user.cash or 0)).quantize(
                    Decimal('0.00'), rounding=ROUND_DOWN
                )
            )

            # 状态映射
            status_map = {0: '审核', 1: '正常', 2: '停用', 3: '删除'}

            logger.info(f"get_myinfo success: user_id={current_user_id}")
            return (
                jsonify(
                    {
                        'code': 200,
                        'data': {
                            'user_account': user.user_account,
                            'account_credit': user.account_credit,
                            'create_time': (
                                user.create_time.strftime('%Y-%m-%d %H:%M:%S')
                                if user.create_time
                                else ''
                            ),
                            'last_login_time': (
                                user.last_login_time.strftime('%Y-%m-%d %H:%M:%S')
                                if user.last_login_time
                                else ''
                            ),
                            'status': status_map.get(user.status, '未知'),
                            'mobile': user.mobile or '',
                            'email': user.email or '',
                            'avatar': (
                                base64.b64encode(user.avatar).decode('utf-8')
                                if user.avatar
                                else ''
                            ),
                            'medical_count': medical_count,
                            'cost_sum': cost_sum,
                            'cash': cash,
                        },
                    }
                ),
                200,
            )

        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/update_avatar', methods=['POST'])
@token_required
def update_avatar():
    """更新当前用户头像"""
    try:
        current_user = request.current_user or {}
        current_user_id = current_user.get('user_id')

        if not current_user_id:
            return jsonify({'code': 401, 'message': '用户未登录或token无效'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        image_data = data.get('image_data')
        if not image_data:
            return jsonify({'code': 400, 'message': '缺少头像数据'}), 400

        try:
            # 支持 data URI 或纯 base64
            payload = image_data.split(',', 1)[1] if ',' in image_data else image_data
            avatar_bytes = base64.b64decode(payload)
        except Exception:
            return jsonify({'code': 400, 'message': '头像数据格式错误'}), 400

        # 限制头像大小（约 1MB）
        if len(avatar_bytes) > 1_000_000:
            return jsonify({'code': 413, 'message': '头像过大，请压缩后再上传'}), 413

        db = SessionLocal()
        try:
            user = db.query(SysUser).filter(SysUser.id == current_user_id).first()
            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            user.avatar = avatar_bytes
            db.commit()

            avatar_base64 = (
                base64.b64encode(user.avatar).decode('utf-8') if user.avatar else ''
            )

            logger.info(f"update_avatar success: user_id={current_user_id}")
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '头像更新成功',
                        'data': {'avatar': avatar_base64},
                    }
                ),
                200,
            )
        finally:
            db.close()
    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/generate_invite_code', methods=['GET'])
@token_required
def generate_invite_code():
    """
    生成邀请链接接口

    请求头:
        Authorization: Bearer <token>

    返回:
        {
            "code": 200,
            "data": {
                "invite_code": "ABC123",
                "invite_link": "http://example.com/register-user?invite=ABC123"
            }
        }
    """
    try:
        current_user = request.current_user or {}
        user_account = current_user.get('user_account', '')
        user_id = current_user.get('user_id')

        if not user_id:
            return jsonify({'code': 400, 'message': '缺少用户信息'}), 400

        db = SessionLocal()
        try:
            user = db.query(SysUser).filter(SysUser.id == user_id).first()
            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            if user.invite_code:
                invite_code = user.invite_code
            else:
                tz_now = get_current_local_time()
                # 循环生成唯一的邀请码，检查数据库中是否已存在
                max_retries = 100
                invite_code = ''
                for attempt in range(max_retries):
                    # 基于用户账号、用户ID、当前token、北京时间戳与尝试次数生成种子
                    raw_seed = f"{user_account}-{user_id}-{getattr(request, 'current_token', '')}-{tz_now.timestamp()}-{attempt}"
                    candidate_code = (
                        hashlib.sha256(raw_seed.encode('utf-8')).hexdigest()[:6].upper()
                    )

                    # 检查是否有其他用户已使用此邀请码
                    existing = (
                        db.query(SysUser)
                        .filter(SysUser.invite_code == candidate_code)
                        .first()
                    )
                    if not existing:
                        invite_code = candidate_code
                        break

                if not invite_code:
                    return (
                        jsonify({'code': 500, 'message': '生成邀请码失败，请稍后重试'}),
                        500,
                    )

                user.invite_code = invite_code
                user.invite_create_time = tz_now

                db.commit()
                db.refresh(user)

            site_url_env = os.getenv('SITE_URL')
            '''
            host_part = site_url_env.strip('/') if site_url_env else request.host
            if host_part.startswith('http://') or host_part.startswith('https://'):
                base_url = host_part.rstrip('/')
            else:
                base_url = f"http://{host_part}".rstrip('/')
            '''
            invite_link = f"{site_url_env}register-user?invite={invite_code}"

            # 统计邀请记录人数与获得算力点（increase_cost合计数）
            stats = (
                db.query(
                    func.count(BasInviteRecord.id),
                    func.coalesce(
                        cast(func.sum(BasInviteRecord.increase_cost), Numeric(10, 2)),
                        0.0,
                    ),
                )
                .filter(
                    BasInviteRecord.user_id == user_id,
                    BasInviteRecord.invite_code == invite_code,
                )
                .first()
            )

            invite_count = int(stats[0]) if stats and stats[0] is not None else 0
            raw_increase_cost = (
                Decimal(str(stats[1]))
                if stats and stats[1] is not None
                else Decimal('0.0')
            )
            increase_cost_total = float(
                Decimal(str(raw_increase_cost)).quantize(
                    Decimal('0.00'), rounding=ROUND_DOWN
                )
            )

            logger.info(
                f"generate_invite_code success: user_id={user_id}, invite_code={invite_code}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '生成成功',
                        'data': {
                            'invite_code': invite_code,
                            'invite_link': invite_link,
                            'invite_create_time': (
                                user.invite_create_time.isoformat()
                                if user.invite_create_time
                                else None
                            ),
                            'invite_count': invite_count,
                            'increase_cost_total': increase_cost_total,
                        },
                    }
                ),
                200,
            )
        finally:
            db.close()

    except Exception as e:
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


# -----------------微信支付-----------------
@app.route('/api/wechat_native_pay', methods=['POST'])
@token_required
def wechat_native_pay():
    """创建支付订单，返回二维码链接（用于Native支付）

    请求参数:
        pay_amount: 应付金额（单位：元）

    返回:
        {
            "success": True,
            "out_trade_no": "订单号",
            "code_url": "支付二维码链接",
            "message": "下单成功"
        }
    """
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')
        user_account = current_user.get('user_account')

        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求参数不能为空'}), 400

        pay_amount = data.get('pay_amount')  # 应付金额（单位：元）
        if not pay_amount:
            return jsonify({'success': False, 'error': '应付额不能为空'}), 400

        try:
            pay_amount = Decimal(str(pay_amount)).quantize(
                Decimal('0.00'), rounding=ROUND_DOWN
            )
            pay_min_amount = Decimal(os.getenv('WECHAT_PAY_MIN_AMOUNT', '9.90'))
            pay_max_amount = Decimal(os.getenv('WECHAT_PAY_MAX_AMOUNT', '99.00'))

            if pay_amount < pay_min_amount or pay_amount > pay_max_amount:
                return (
                    jsonify(
                        {
                            'success': False,
                            'error': f'应付额必须在{pay_min_amount}~{pay_max_amount}之间',
                        }
                    ),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '应付额格式错误'}), 400

        # 判断每日支付次数限制。
        pay_limit = int(os.getenv('WECHAT_PAY_LIMIT', '1'))
        today = get_current_local_time().date()
        db = SessionLocal()
        try:
            pay_count = (
                db.query(BasWechatPay)
                .filter(
                    BasWechatPay.user_id == user_id,
                    BasWechatPay.create_time
                    >= datetime.datetime.combine(today, datetime.time.min),
                    BasWechatPay.create_time
                    <= datetime.datetime.combine(today, datetime.time.max),
                    BasWechatPay.trade_state == 'SUCCESS',
                )
                .count()
            )
            if pay_count >= pay_limit:
                return (
                    jsonify(
                        {
                            'success': False,
                            'error': f'今日支付次数已达上限({pay_limit})',
                        }
                    ),
                    400,
                )
        finally:
            db.close()

        # 生成商户订单号（使用唯一ID生成器保证唯一性）
        out_trade_no = next_id()
        description = f"赞助信誉度-Ai体征分析助手"
        # 将应付金额（元）转换为分，微信支付金额单位为分
        amount = int(pay_amount * 100)

        # 调用统一下单接口
        code, message = wxpay.pay(
            description=description,
            pay_type=WeChatPayType.NATIVE,
            out_trade_no=out_trade_no,
            amount={"total": amount},
            # payer={
            #    "openid": "oUpF8uMuAJO_M2pxb1Q9zNjWeS6o"  # 支付用户的openid，必须与当前appid对应
            # },
        )

        if 200 <= code < 300:
            # 下单成功，解析返回数据
            result = json.loads(message)
            logger.info(
                f'订单创建成功: 用户={user_account}(ID:{user_id}), 订单号={out_trade_no}, 额度={pay_amount}, code_url={result.get("code_url")}'
            )

            # TODO: 在此处保存订单信息到数据库，例如创建BasWechatPay对象并保存
            db = SessionLocal()
            try:
                now_time = get_current_local_time()
                new_pay = BasWechatPay(
                    id=out_trade_no,
                    user_id=user_id,
                    mchid=wxpay._mchid,
                    appid=wxpay._appid,
                    out_trade_no=out_trade_no,
                    total_amount=amount,
                    currency='CNY',
                    trade_state='ORDER',
                    trade_state_desc='Native支付订单创建',
                    create_at=now_time,
                    update_at=now_time,
                    is_notify=-1,
                )
                db.add(new_pay)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"保存支付订单到数据库失败: {e}")
            finally:
                db.close()

            logger.info(
                f"wechat_native_pay success: user_id={user_id}, out_trade_no={out_trade_no}, amount={pay_amount}"
            )
            return (
                jsonify(
                    {
                        "success": True,
                        "out_trade_no": out_trade_no,
                        "pay_amount": pay_amount,
                        "code_url": result.get("code_url"),  # 用于生成支付二维码
                        "message": "下单成功",
                    }
                ),
                200,
            )
        else:
            # 下单失败
            logger.error(f"订单创建失败: {code}, {message}")
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"下单接口异常:{e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/wechat_jsapi_pay', methods=['POST'])
@token_required
def wechat_jsapi_pay():
    """
    微信JSAPI支付下单接口（适用于微信内浏览器）

    请求参数:
    {
        "pay_amount": 10.00,  # 支付金额（元）
        "code": "wx_oauth_code"  # 微信OAuth授权码
    }

    返回:
    {
        "success": true,
        "out_trade_no": "订单号",
        "pay_amount": 10.00,
        "payment_params": {  # 用于调起微信支付的参数
            "appId": "...",
            "timeStamp": "...",
            "nonceStr": "...",
            "package": "prepay_id=...",
            "signType": "RSA",
            "paySign": "..."
        }
    }
    """
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')
        user_account = current_user.get('user_account')

        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '请求参数不能为空'}), 400

        pay_amount = data.get('pay_amount')  # 应付金额（单位：元）
        code = data.get('code')  # 微信OAuth授权码或小程序code
        pay_scene = data.get('pay_scene', 'h5')  # 新增参数，默认h5，可为'mini'或'h5'

        if not pay_amount:
            return jsonify({'success': False, 'error': '应付额不能为空'}), 400

        if not code:
            return (
                jsonify({'success': False, 'error': '微信授权码/小程序code不能为空'}),
                400,
            )

        try:
            pay_amount = Decimal(str(pay_amount)).quantize(
                Decimal('0.00'), rounding=ROUND_DOWN
            )
            pay_min_amount = Decimal(os.getenv('WECHAT_PAY_MIN_AMOUNT', '9.90'))
            pay_max_amount = Decimal(os.getenv('WECHAT_PAY_MAX_AMOUNT', '99.00'))

            if pay_amount < pay_min_amount or pay_amount > pay_max_amount:
                return (
                    jsonify(
                        {
                            'success': False,
                            'error': f'应付额必须在{pay_min_amount}~{pay_max_amount}之间',
                        }
                    ),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '应付额格式错误'}), 400

        # 判断每日支付次数限制。
        pay_limit = int(os.getenv('WECHAT_PAY_LIMIT', '1'))
        today = get_current_local_time().date()
        db = SessionLocal()
        try:
            pay_count = (
                db.query(BasWechatPay)
                .filter(
                    BasWechatPay.user_id == user_id,
                    BasWechatPay.create_at
                    >= datetime.datetime.combine(today, datetime.time.min),
                    BasWechatPay.create_at
                    <= datetime.datetime.combine(today, datetime.time.max),
                    BasWechatPay.trade_state == 'SUCCESS',
                )
                .count()
            )
            if pay_count >= pay_limit:
                return (
                    jsonify(
                        {
                            'success': False,
                            'error': f'今日支付次数已达上限({pay_limit})',
                        }
                    ),
                    400,
                )
        finally:
            db.close()

        # 场景分支：小程序 or 公众号H5
        if pay_scene == 'mini':
            # 小程序支付流程
            mini_appid = os.getenv('WECHAT_MINI_APPID', '')
            mini_secret = os.getenv('WECHAT_MINI_SECRET', '')
            if not mini_appid or not mini_secret:
                logger.error(
                    '小程序配置缺失，请检查 WECHAT_MINI_APPID/WECHAT_MINI_SECRET'
                )
                return (
                    jsonify(
                        {'success': False, 'error': '小程序配置缺失，请联系管理员'}
                    ),
                    500,
                )
            # 用code换openid
            session_url = 'https://api.weixin.qq.com/sns/jscode2session'
            params = {
                'appid': mini_appid,
                'secret': mini_secret,
                'js_code': code,
                'grant_type': 'authorization_code',
            }
            try:
                resp = requests.get(session_url, params=params, timeout=5)
                session_data = resp.json()
                if 'openid' not in session_data:
                    logger.error(f'小程序获取openid失败: {session_data}')
                    return (
                        jsonify(
                            {
                                'success': False,
                                'error': f'获取openid失败: {session_data.get("errmsg", "未知错误")}',
                            }
                        ),
                        400,
                    )
                openid = session_data['openid']
                logger.info(f'小程序成功获取openid: {openid}')
            except Exception as e:
                logger.error(f'小程序调用jscode2session失败: {e}')
                return (
                    jsonify({'success': False, 'error': f'获取openid失败: {str(e)}'}),
                    500,
                )
            # 统一下单
            out_trade_no = next_id()
            description = f"赞助信誉度-Ai体征分析助手"
            amount = int(pay_amount * 100)
            # 这里需要用小程序appid
            code_status, message = wxpay.pay(
                description=description,
                pay_type=WeChatPayType.JSAPI,
                out_trade_no=out_trade_no,
                amount={"total": amount},
                payer={"openid": openid},
                appid=mini_appid,
            )
            appid_for_sign = mini_appid
        else:
            # 公众号H5流程（原有逻辑）
            wechat_secret = os.getenv('WECHAT_SECRET', '')
            if not wechat_secret:
                logger.error("缺少微信SECRET配置")
                return (
                    jsonify(
                        {'success': False, 'error': '服务器配置错误，请联系管理员'}
                    ),
                    500,
                )
            access_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
            params = {
                "appid": wxpay._appid,
                "secret": wechat_secret,
                "code": code,
                "grant_type": "authorization_code",
            }
            try:
                response = requests.get(access_token_url, params=params, timeout=5)
                oauth_result = response.json()
                if "openid" not in oauth_result:
                    logger.error(f"获取openid失败: {oauth_result}")
                    return (
                        jsonify(
                            {
                                'success': False,
                                'error': f'获取用户openid失败: {oauth_result.get("errmsg", "未知错误")}',
                            }
                        ),
                        400,
                    )
                openid = oauth_result["openid"]
                logger.info(f"成功获取openid: {openid}")
            except Exception as e:
                logger.error(f"调用微信OAuth接口失败: {e}")
                return (
                    jsonify({'success': False, 'error': f'获取用户信息失败: {str(e)}'}),
                    500,
                )
            out_trade_no = next_id()
            description = f"赞助信誉度-Ai体征分析助手"
            amount = int(pay_amount * 100)
            code_status, message = wxpay.pay(
                description=description,
                pay_type=WeChatPayType.JSAPI,
                out_trade_no=out_trade_no,
                amount={"total": amount},
                payer={"openid": openid},
            )
            appid_for_sign = wxpay._appid

        if 200 <= code_status < 300:
            # 下单成功，解析返回数据
            result = json.loads(message)
            prepay_id = result.get('prepay_id')
            timestamp = str(int(time.time()))
            noncestr = str(uuid.uuid4()).replace('-', '')
            package = 'prepay_id=' + prepay_id
            sign = wxpay.sign([appid_for_sign, timestamp, noncestr, package])
            signtype = 'RSA'

            logger.info(
                f'JSAPI订单创建成功: 用户={user_account}(ID:{user_id}), 订单号={out_trade_no}, '
                f'额度={pay_amount}, prepay_id={prepay_id}, openid={openid}, scene={pay_scene}'
            )

            # 保存订单信息到数据库
            db = SessionLocal()
            try:
                now_time = get_current_local_time()
                new_pay = BasWechatPay(
                    id=out_trade_no,
                    user_id=user_id,
                    mchid=wxpay._mchid,
                    appid=appid_for_sign,
                    out_trade_no=out_trade_no,
                    openid=openid,
                    total_amount=amount,
                    currency='CNY',
                    trade_state='ORDER',
                    trade_state_desc=f'JSAPI支付订单创建({pay_scene})',
                    create_at=now_time,
                    update_at=now_time,
                    is_notify=-1,
                )
                db.add(new_pay)
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"保存支付订单到数据库失败: {e}")
            finally:
                db.close()

            # 生成前端调起支付所需的参数
            logger.info(
                f"wechat_jsapi_pay success: user_id={user_id}, out_trade_no={out_trade_no}, amount={pay_amount}, scene={pay_scene}"
            )
            return (
                jsonify(
                    {
                        "success": True,
                        "result": {
                            "appId": appid_for_sign,
                            "timeStamp": timestamp,
                            "nonceStr": noncestr,
                            "package": "prepay_id=%s" % prepay_id,
                            "signType": signtype,
                            "paySign": sign,
                        },
                    }
                ),
                200,
            )
        else:
            # 下单失败
            logger.error(f"JSAPI订单创建失败: {code_status}, {message}")
            return jsonify({"success": False, "error": message}), 400

    except Exception as e:
        logger.error(f"JSAPI下单接口异常: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/wechat_pay_notify', methods=['POST'])
def wechat_pay_notify():
    """支付结果异步回调通知接口（微信支付服务器调用）"""
    try:
        with pay_notify_lock:
            # 1. 获取原始字节流数据
            body = request.get_data()
            # 2. 将字节流解码为字符串，再解析为Python字典
            #    这是修复错误的关键步骤！
            # body_dict = json.loads(raw_body_bytes.decode('utf-8'))

            # 3. 获取请求头（确保是字典格式）
            # headers = dict(request.headers)  # 转换为普通字典，兼容性更好
            headers = request.headers

            # 4. 使用SDK验证签名并解密（现在body_dict是字典）
            result = wxpay.callback(headers, body)

            if result is None:
                logger.error(f'回调通知签名验证失败或解密失败')
                # 验证失败必须返回失败响应码，微信会重试通知
                return jsonify({'code': 'FAIL', 'message': '处理失败'}), 500

            # 3. 处理业务逻辑
            resource = result.get('resource', {})
            out_trade_no = resource.get('out_trade_no')
            trade_state = resource.get('trade_state')
            logger.info(f'收到支付回调: 订单：{out_trade_no}, 状态：{trade_state}')
            if trade_state == 'SUCCESS':
                # TODO: 在此处更新你的数据库订单状态为“已支付”
                # 例如，查询BasWechatPay对象并更新状态
                db = SessionLocal()
                try:
                    pay_order = (
                        db.query(BasWechatPay)
                        .filter(BasWechatPay.id == out_trade_no)
                        .first()
                    )
                    if pay_order:
                        if pay_order.is_notify == 0:
                            return jsonify({'code': 'SUCCESS', 'message': '成功'}), 200

                        # 3. 逐层获取所有字段的值（安全获取，避免KeyError）
                        # --------------------- 顶层字段 ---------------------
                        callback_id = result.get('callback_id')  # 回调唯一ID
                        create_time = result.get('create_time')  # 回调创建时间
                        resource_type = result.get('resource_type')  # 回调资源类型
                        event_type = result.get('event_type')  # 事件类型
                        summary = result.get('summary')  # 回调摘要

                        # --------------------- resource层字段 ---------------------
                        # 先获取resource字典（不存在则返回空字典，避免后续get报错）
                        # resource = result.get('resource', {})
                        # mchid = resource.get('mchid')  # 商户号
                        # appid = resource.get('appid')  # 小程序/公众号APPID
                        # out_trade_no = resource.get('out_trade_no')  # 商户订单号
                        transaction_id = resource.get('transaction_id')  # 微信交易号
                        trade_type = resource.get('trade_type')  # 交易类型
                        trade_state = resource.get('trade_state')  # 交易状态
                        trade_state_desc = resource.get(
                            'trade_state_desc'
                        )  # 交易状态描述
                        bank_type = resource.get('bank_type')  # 付款银行
                        attach = resource.get('attach')  # 附加数据
                        success_time = resource.get('success_time')  # 支付成功时间

                        # --------------------- payer层字段（嵌套在resource中） ---------------------
                        payer = resource.get('payer', {})  # 先获取payer字典
                        openid = payer.get('openid')  # 用户OpenID

                        # --------------------- amount层字段（嵌套在resource中） ---------------------
                        amount = resource.get('amount', {})  # 先获取amount字典
                        # total = amount.get('total')  # 订单总金额（分）
                        payer_total = amount.get(
                            'payer_total'
                        )  # 用户实际支付金额（分）
                        currency = amount.get('currency')  # 订单币种
                        payer_currency = amount.get('payer_currency')  # 用户支付币种

                        now_time = get_current_local_time()
                        pay_order.callback_id = callback_id
                        pay_order.create_time = convert_iso_time_to_normal(create_time)
                        pay_order.resource_type = resource_type
                        pay_order.event_type = event_type
                        pay_order.summary = summary
                        pay_order.transaction_id = transaction_id
                        pay_order.trade_type = trade_type
                        pay_order.trade_state = trade_state
                        pay_order.trade_state_desc = trade_state_desc
                        pay_order.bank_type = bank_type
                        pay_order.attach = attach
                        pay_order.success_time = convert_iso_time_to_normal(
                            success_time
                        )
                        pay_order.openid = openid
                        pay_order.payer_total = payer_total
                        pay_order.currency = currency
                        pay_order.payer_currency = payer_currency
                        pay_order.update_at = now_time
                        pay_order.is_notify = 0

                        credit_amount = Decimal('0.0')
                        # 更新用户账户信誉度：将支付金额（分）转换为元并累加
                        user = (
                            db.query(SysUser)
                            .filter(SysUser.id == pay_order.user_id)
                            .first()
                        )
                        if user:
                            # payer_total是分，需要除以100转换为元
                            credit_amount = Decimal(str(payer_total)) / Decimal('100')
                            user.account_credit = (
                                user.account_credit or Decimal('0.0')
                            ) + credit_amount
                            logger.info(
                                f'用户 {user.user_account} 充值成功，额度：{credit_amount}，当前余额：{user.account_credit}'
                            )

                        # 充值成功，给邀请人分成，每笔订单充值金额的10%
                        invite_record = (
                            db.query(BasInviteRecord)
                            .filter(BasInviteRecord.invite_user_id == pay_order.user_id)
                            .first()
                        )
                        if invite_record:
                            # 查询邀请人用户记录
                            inviter_user = (
                                db.query(SysUser)
                                .filter(SysUser.id == invite_record.user_id)
                                .first()
                            )
                            if inviter_user:
                                commission = credit_amount * Decimal(
                                    os.getenv("INVITE_PERCENT_CASH", '0.1')
                                )
                                inviter_user.cash = (
                                    inviter_user.cash or Decimal('0.0')
                                ) + commission
                                logger.info(
                                    f'邀请人 {inviter_user.user_account} 获得邀请分成：{commission}元，当前cash：{inviter_user.cash}元'
                                )

                        db.commit()
                    else:
                        logger.error(f'未找到订单号为 {out_trade_no} 的支付订单记录。')
                except Exception as e:
                    db.rollback()
                    logger.error(f'更新支付订单状态失败: {e}')
                finally:
                    db.close()
                logger.info(f'订单： {out_trade_no} 支付成功，业务状态已更新。')

            # 4. 返回成功响应（必须，否则微信会重复通知）
            # 严格按照微信要求的格式返回
            return jsonify({'code': 'SUCCESS', 'message': '成功'}), 200

    except Exception as e:
        logger.error(f'处理支付回调时发生异常: {e}')
        return jsonify({'code': 'FAIL', 'message': '系统异常'}), 500


@app.route('/api/wechat_pay_query', methods=['GET'])
@token_required
def wechat_pay_query():
    """主动查询订单支付状态（用于前端轮询或对账）"""
    try:
        # 验证当前用户
        current_user = request.current_user
        user_id = current_user.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '用户信息无效'}), 401

        out_trade_no = request.args.get('out_trade_no')
        if not out_trade_no:
            return jsonify({'success': False, 'error': '缺少订单号参数'}), 400

        # 验证订单是否属于当前用户
        db = SessionLocal()
        try:
            pay_order = (
                db.query(BasWechatPay)
                .filter(
                    BasWechatPay.out_trade_no == out_trade_no,
                    BasWechatPay.user_id == user_id,
                )
                .first()
            )

            if not pay_order:
                return jsonify({'success': False, 'error': '订单不存在或无权访问'}), 404
        finally:
            db.close()

        code, message = wxpay.query(out_trade_no=out_trade_no)

        if code == 200:
            order_info = json.loads(message)
            # 返回订单信息和交易状态
            logger.info(
                f"wechat_pay_query success: user_id={user_id}, out_trade_no={out_trade_no}, trade_state={order_info.get('trade_state')}"
            )
            return (
                jsonify(
                    {
                        'success': True,
                        'trade_state': order_info.get('trade_state'),
                        'order_info': order_info,
                    }
                ),
                200,
            )
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        logger.error(f'查询订单异常: {out_trade_no}')
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_nonce_str(length=32):
    """生成随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_jsapi_ticket(access_token):
    """获取 jsapi_ticket

    jsapi_ticket 是公众号用于调用微信 JS 接口的临时票据
    有效期为 7200 秒，需要定期刷新
    """
    try:
        url = f"https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={access_token}&type=jsapi"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get('errcode') == 0:
            return data.get('ticket')
        else:
            logger.error(f"获取 jsapi_ticket 失败: {data}")
            return None
    except Exception as e:
        logger.error(f"获取 jsapi_ticket 异常: {str(e)}")
        return None


def generate_js_signature(jsapi_ticket, noncestr, timestamp, url):
    """生成微信 JS-SDK 签名

    签名算法：
    1. 对所有待签名参数按照字段名的ASCII码从小到大排序（字典序）
    2. 使用URL键值对的格式（即key1=value1&key2=value2…）拼接成字符串string1
    3. 对string1作sha1加密，字段名和字段值都采用原始值，不进行URL转义
    """
    # 参数必须按字典序排列
    params = {
        'jsapi_ticket': jsapi_ticket,
        'noncestr': noncestr,
        'timestamp': timestamp,
        'url': url,
    }

    # 排序并拼接
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    string1 = '&'.join([f'{k}={v}' for k, v in sorted_params])

    # SHA1 签名
    signature = hashlib.sha1(string1.encode('utf-8')).hexdigest()
    return signature


def get_access_token_for_jsapi():
    """获取微信 access_token（用于获取 jsapi_ticket）

    注意：access_token 有效期为 7200 秒，建议进行缓存
    这里简化处理，实际应用中应该加入缓存机制
    """
    try:
        secret = os.getenv('WECHAT_SECRET')
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={wxpay._appid}&secret={secret}"
        response = requests.get(url, timeout=10)
        data = response.json()

        if 'access_token' in data:
            return data['access_token']
        else:
            logger.error(f"获取 access_token 失败: {data}")
            return None
    except Exception as e:
        logger.error(f"获取 access_token 异常: {str(e)}")
        return None


@app.route('/api/wechat_js_signature', methods=['POST'])
@token_required
def wechat_js_signature():
    """获取微信 JS-SDK 签名配置

    请求参数:
    {
        "url": "当前页面URL（不含hash）"
    }

    返回:
    {
        "code": 200,
        "data": {
            "appId": "...",
            "timestamp": 1234567890,
            "nonceStr": "...",
            "signature": "..."
        }
    }
    """
    try:
        data = request.get_json()
        if not data or not data.get('url'):
            return jsonify({'code': 400, 'message': '页面URL不能为空'}), 400

        url = data.get('url')

        # 获取 access_token
        access_token = get_access_token_for_jsapi()
        if not access_token:
            return jsonify({'code': 500, 'message': '获取access_token失败'}), 500

        # 获取 jsapi_ticket
        jsapi_ticket = get_jsapi_ticket(access_token)
        if not jsapi_ticket:
            return jsonify({'code': 500, 'message': '获取jsapi_ticket失败'}), 500

        # 生成签名参数
        timestamp = int(time.time())
        noncestr = generate_nonce_str()
        signature = generate_js_signature(jsapi_ticket, noncestr, timestamp, url)

        logger.info(f"生成JS-SDK签名: url={url}, timestamp={timestamp}")

        logger.info(f"wechat_js_signature success: url={url}")
        return jsonify(
            {
                'code': 200,
                'message': '获取签名成功',
                'data': {
                    'appId': wxpay._appid,
                    'timestamp': timestamp,
                    'nonceStr': noncestr,
                    'signature': signature,
                },
            }
        )

    except Exception as e:
        logger.error(f"生成微信JS-SDK签名失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'message': f'生成签名失败: {str(e)}'}), 500


@app.route('/api/wechat_config', methods=['GET'])
@token_required
def wechat_config():
    """获取微信支付配置（返回appid等前端需要的信息）"""
    try:
        # 优先使用显式配置的回调地址，否则回退到 SITE_URL/#/my-info
        # 注意：WECHAT_REDIRECT_URI 必须与微信公众平台“授权回调域名”一致
        redirect_uri = os.getenv('WECHAT_REDIRECT_URI')
        current_user = getattr(request, 'current_user', {}) or {}
        logger.info(f"wechat_config success: user_id={current_user.get('user_id')}")
        return (
            jsonify(
                {
                    'code': 200,
                    'message': '获取成功',
                    'data': {
                        'appid': wxpay._appid,
                        'redirect_uri': redirect_uri,
                        'mch_id': wxpay._mchid,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({'code': 500, 'message': f'获取配置失败: {str(e)}'}), 500


@app.route('/api/wechat_withdraw', methods=['POST'])
@token_required
def wechat_withdraw():
    """企业付款到微信零钱（提现）

    请求参数:
    {
        "amount": 10.00  # 提现金额（元）
    }

    返回:
    {
        "code": 200,
        "message": "提现申请已提交"
    }
    """
    try:
        # 获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')
        user_account = current_user.get('user_account')

        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求参数不能为空'}), 400

        real_name = data.get('real_name', '').strip()
        amount = data.get('amount')
        code = data.get('code')  # 微信授权码或小程序code
        pay_scene = data.get('pay_scene')  # 支付场景，可能的值：h5、mini

        if not real_name or len(real_name) > 10:
            return (
                jsonify(
                    {'code': 400, 'message': '真实姓名不能为空,长度不能超过10个字符'}
                ),
                400,
            )

        if not amount:
            return jsonify({'code': 400, 'message': '提现额不能为空'}), 400

        try:
            amount = Decimal(str(amount)).quantize(Decimal('0.00'), rounding=ROUND_DOWN)
            min_amount = Decimal(os.getenv('WECHAT_WITHDRAW_MIN_AMOUNT', '9.90'))
            max_amount = Decimal(os.getenv('WECHAT_WITHDRAW_MAX_AMOUNT', '99.00'))
            if amount < min_amount or amount > max_amount:
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': f'提现额度为{min_amount}~{max_amount}之间',
                        }
                    ),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({'code': 400, 'message': '提现额格式错误'}), 400

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 查询用户账户信息
            user = db.query(SysUser).filter(SysUser.id == user_id).first()
            if not user:
                return jsonify({'code': 404, 'message': '用户不存在'}), 404

            # 检查用户余额是否足够
            current_cash = Decimal(str(user.cash or 0))
            if current_cash < amount:
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': f'提现额度不足，当前余额：{float(current_cash):.2f}',
                        }
                    ),
                    400,
                )

            # 检查用户今天是否已经提现过（限制每天最多提现1次）
            today_start = get_current_local_time().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            today_end = today_start + datetime.timedelta(days=1)

            today_withdraw_count = (
                db.query(func.count(BasWechatWithdraw.id))
                .filter(
                    BasWechatWithdraw.user_id == user_id,
                    BasWechatWithdraw.create_time >= today_start,
                    BasWechatWithdraw.create_time < today_end,
                    BasWechatWithdraw.state.in_(['SUCCESS', 'PROCESSING']),
                )
                .scalar()
            )

            withdraw_limit = int(os.getenv('WECHAT_WITHDRAW_LIMIT', '1'))
            if today_withdraw_count and today_withdraw_count >= withdraw_limit:
                return (
                    jsonify(
                        {
                            'code': 400,
                            'message': f'每天最多提现{withdraw_limit}次，请明天再试',
                        }
                    ),
                    400,
                )

            openid = None
            transfer_appid = wxpay._appid

            if pay_scene == 'mini':
                mini_appid = os.getenv('WECHAT_MINI_APPID', '')
                mini_secret = os.getenv('WECHAT_MINI_SECRET', '')
                if not mini_appid or not mini_secret:
                    return (
                        jsonify(
                            {
                                'code': 400,
                                'message': '小程序配置缺失，请检查 WECHAT_MINI_APPID/WECHAT_MINI_SECRET',
                            }
                        ),
                        400,
                    )

                try:
                    session_resp = requests.get(
                        'https://api.weixin.qq.com/sns/jscode2session',
                        params={
                            'appid': mini_appid,
                            'secret': mini_secret,
                            'js_code': code,
                            'grant_type': 'authorization_code',
                        },
                        timeout=10,
                    )
                    session_data = session_resp.json()
                    openid = session_data.get('openid')
                    if not openid:
                        err_msg = session_data.get('errmsg', '获取openid失败')
                        return (
                            jsonify(
                                {
                                    'code': 400,
                                    'message': f'小程序openid获取失败: {err_msg}',
                                }
                            ),
                            400,
                        )
                    transfer_appid = mini_appid
                except Exception as e:
                    return (
                        jsonify({'code': 500, 'message': f'小程序登录失败: {str(e)}'}),
                        500,
                    )
            else:
                if not code:
                    return (
                        jsonify({'code': 400, 'message': '微信授权码不能为空'}),
                        400,
                    )

                wechat_secret = os.getenv('WECHAT_SECRET', '')
                if not wechat_secret:
                    logger.error('缺少微信SECRET配置')
                    return (
                        jsonify(
                            {'code': 500, 'message': '服务器配置错误，请联系管理员'}
                        ),
                        500,
                    )

                access_token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
                try:
                    response = requests.get(
                        access_token_url,
                        params={
                            'appid': wxpay._appid,
                            'secret': wechat_secret,
                            'code': code,
                            'grant_type': 'authorization_code',
                        },
                        timeout=5,
                    )
                    oauth_result = response.json()
                    openid = oauth_result.get('openid')
                    if not openid:
                        logger.error(f"获取openid失败: {oauth_result}")
                        return (
                            jsonify(
                                {
                                    'code': 400,
                                    'message': f'获取用户openid失败: {oauth_result.get("errmsg", "未知错误")}',
                                }
                            ),
                            400,
                        )
                except Exception as e:
                    logger.error(f"调用微信OAuth接口失败: {e}")
                    return (
                        jsonify(
                            {'code': 500, 'message': f'获取用户信息失败: {str(e)}'}
                        ),
                        500,
                    )

            # 生成商户转账单号
            out_bill_no = next_id()

            # 扣除手续费
            fee_rate = Decimal(os.getenv('WECHAT_WITHDRAW_FEE_RATE', '0.00'))
            fee_rate_amount = amount * (Decimal('1.00') - fee_rate)

            # 将金额转换为分
            transfer_amount = int(fee_rate_amount * 100)

            # 调用微信企业付款接口
            try:
                # 使用 wechatpayv3 的 mch_transfer_bills 接口（/v3/fund-app/mch-transfer/transfer-bills）
                # 适用于单笔转账到零钱
                transfer_scene_id = '1005'  # 商业转账场景ID
                transfer_remark = f'{real_name}用户提现'
                user_recv_perception = '劳务报酬'
                code, message = wxpay.mch_transfer_bills(
                    out_bill_no=out_bill_no,  # 商户账单号（商户系统内部唯一）
                    transfer_scene_id=transfer_scene_id,  # 转账场景ID，1005表示商业转账
                    openid=openid,  # 收款用户openid
                    transfer_amount=transfer_amount,  # 转账金额（分）
                    transfer_remark=transfer_remark,  # 转账备注，最多32字符
                    user_name=real_name,  # 收款用户真实姓名（金额>=2000元时必填且需加密）
                    user_recv_perception=user_recv_perception,  # 用户收款时展示信息
                    transfer_scene_report_infos=[
                        {
                            'info_type': '岗位类型',
                            'info_content': '推荐介绍人员',
                        },
                        {
                            'info_type': '报酬说明',
                            'info_content': '用户充值后给介绍人分成的劳务报酬',
                        },
                    ],  # 转账场景信息
                    appid=transfer_appid,
                    notify_url=os.getenv(
                        'WECHAT_WITHDRAW_NOTIFY_URL'
                    ),  # 转账结果异步通知地址
                )

                if 200 <= code < 300:
                    # 转账请求成功
                    result = json.loads(message)

                    # 获取转账单号（bill_id）
                    transfer_bill_no = result.get('transfer_bill_no')

                    logger.info(
                        f'用户 {user_account} 提现成功，账单号：{out_bill_no}，额度：{float(amount):.2f}，'
                        f'当前余额：¥{float(user.cash):.2f}，转账单号：{transfer_bill_no}'
                    )

                    # 保存订单信息到数据库
                    # db = SessionLocal()
                    try:
                        user.real_name = real_name  # 更新用户真实姓名
                        # 更新记录。
                        now_time = get_current_local_time()
                        new_bill = BasWechatWithdraw(
                            id=out_bill_no,
                            user_id=user_id,
                            transfer_scene_id=transfer_scene_id,
                            transfer_amount=transfer_amount,
                            transfer_remark=transfer_remark,
                            user_name=real_name,
                            user_recv_perception=user_recv_perception,
                            appid=transfer_appid,
                            out_bill_no=out_bill_no,
                            create_time=convert_iso_time_to_normal(
                                result.get('create_time')
                            ),
                            package_info=result.get('package_info'),
                            state=result.get('state'),
                            transfer_bill_no=transfer_bill_no,
                            create_at=now_time,
                            update_at=now_time,
                            is_notify=-1,
                            withdraw_amount=amount,
                        )
                        db.add(new_bill)
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        logger.error(f"保存支付订单到数据库失败: {e}")
                    # finally:
                    #    db.close()

                    logger.info(
                        f"wechat_withdraw success: user_id={user_id}, out_bill_no={out_bill_no}, amount={amount}"
                    )
                    return (
                        jsonify(
                            {
                                'code': 200,
                                'message': '提现申请已提交',
                                'data': {
                                    'out_bill_no': out_bill_no,
                                    'appid': transfer_appid,
                                    'mch_id': wxpay._mchid,
                                    'package_info': result.get('package_info'),
                                    'state': result.get('state'),
                                    'transfer_bill_no': transfer_bill_no,
                                },
                            }
                        ),
                        200,
                    )
                else:
                    # 转账失败
                    error_msg = message
                    try:
                        error_data = json.loads(message)
                        error_msg = error_data.get('message', message)
                    except:
                        pass

                    logger.error(f'用户 {user_account} 提现失败: {code}, {error_msg}')
                    return (
                        jsonify({'code': 500, 'message': f'提现失败: {error_msg}'}),
                        500,
                    )

            except Exception as transfer_err:
                logger.error(f'调用微信转账接口异常: {transfer_err}')
                return (
                    jsonify({'code': 500, 'message': f'提现失败: {str(transfer_err)}'}),
                    500,
                )

        except Exception as e:
            db.rollback()
            logger.error(f'提现处理失败: {e}')
            return jsonify({'code': 500, 'message': f'提现处理失败: {str(e)}'}), 500
        finally:
            db.close()

    except Exception as e:
        logger.error(f'提现接口异常: {e}')
        return jsonify({'code': 500, 'message': f'提现失败: {str(e)}'}), 500


@app.route('/api/wechat_withdraw_notify', methods=['POST'])
def wechat_withdraw_notify():
    """企业付款（提现）结果异步回调通知接口（微信支付服务器调用）"""
    try:
        with withdraw_notify_lock:
            # 1. 获取原始字节流数据
            body = request.get_data()
            # 2. 获取请求头
            headers = request.headers

            # 3. 使用SDK验证签名并解密
            result = wxpay.callback(headers, body)

            if result is None:
                logger.error(f'企业付款回调通知签名验证失败或解密失败')
                # 验证失败必须返回失败响应码，微信会重试通知
                return jsonify({'code': 'FAIL', 'message': '处理失败'}), 500

            # 4. 处理业务逻辑
            notify_id = result['id']
            create_time = result['create_time']
            resource_type = result['resource_type']
            event_type = result['event_type']
            summary = result['summary']

            # 提取resource中的字段
            resource = result['resource']
            mch_id = resource['mch_id']
            out_bill_no = resource['out_bill_no']
            transfer_bill_no = resource['transfer_bill_no']
            transfer_amount = resource['transfer_amount']
            state = resource['state']
            # openid = resource['openid']
            create_time = resource['create_time']  # 避免与顶层create_time冲突
            update_time = resource['update_time']

            logger.info(
                f'收到企业付款回调: 订单号：{out_bill_no}, 微信单号：{transfer_bill_no}, 状态：{state}'
            )

            if state == 'SUCCESS':
                # 查询提现订单记录
                db = SessionLocal()
                try:
                    withdraw_order = (
                        db.query(BasWechatWithdraw)
                        .filter(BasWechatWithdraw.id == out_bill_no)
                        .first()
                    )

                    if withdraw_order:
                        # 如果已经处理过该通知，直接返回成功避免重复处理
                        if withdraw_order.is_notify == 0:
                            return jsonify({'code': 'SUCCESS', 'message': '成功'}), 200

                        now_time = get_current_local_time()

                        withdraw_order.notify_id = notify_id
                        withdraw_order.resource_type = resource_type
                        withdraw_order.event_type = event_type
                        withdraw_order.summary = summary
                        withdraw_order.state = state
                        withdraw_order.mch_id = mch_id
                        withdraw_order.create_time = convert_iso_time_to_normal(
                            create_time
                        )
                        withdraw_order.update_time = convert_iso_time_to_normal(
                            update_time
                        )
                        withdraw_order.update_at = now_time
                        withdraw_order.is_notify = 0  # 标记已回执
                        # 提现成功，扣除用户cash余额
                        user = (
                            db.query(SysUser)
                            .filter(SysUser.id == withdraw_order.user_id)
                            .first()
                        )
                        if user:
                            # transfer_amount是分，需要除以100转换为元
                            withdraw_amount = Decimal(str(transfer_amount)) / Decimal(
                                '100'
                            )
                            # 加上扣除的手续费
                            fee_rate = Decimal(
                                os.getenv('WECHAT_WITHDRAW_FEE_RATE', '0.00')
                            )
                            withdraw_amount = withdraw_amount / (
                                Decimal('1.00') - fee_rate
                            )

                            # 如果数据库记录的提现金额与回调计算金额不符，按数据库记录扣除
                            if withdraw_order.withdraw_amount != withdraw_amount:
                                withdraw_amount = withdraw_order.withdraw_amount
                                logger.warning(
                                    f'订单 {out_bill_no} 提现金额不匹配，按数据库记录扣除费用：{withdraw_order.withdraw_amount}，'
                                    f'回调增加扣除费用计算后：{withdraw_amount}，'
                                )

                            # 检查用户cash是否足够
                            current_cash = user.cash or Decimal('0.0')
                            if current_cash >= withdraw_amount:
                                user.cash = current_cash - withdraw_amount
                                logger.info(
                                    f'用户 {user.user_account} 提现成功，金额：{withdraw_amount}元，当前cash：{user.cash}'
                                )
                            else:
                                logger.info(
                                    f'用户 {user.user_account} cash不足，当前cash：{current_cash}元，提现额：{withdraw_amount}'
                                )

                        db.commit()
                        logger.info(f'订单 {out_bill_no} 转账状态已更新为 {state}')
                    else:
                        logger.error(f'未找到订单号为 {out_bill_no} 的提现订单记录。')

                except Exception as e:
                    db.rollback()
                    logger.error(f'更新提现订单状态失败: {e}')
                finally:
                    db.close()

            elif state in ['PROCESSING', 'PENDING']:
                # 转账处理中或待处理
                db = SessionLocal()
                try:
                    withdraw_order = (
                        db.query(BasWechatWithdraw)
                        .filter(BasWechatWithdraw.id == out_bill_no)
                        .first()
                    )

                    if withdraw_order:
                        now_time = get_current_local_time()
                        withdraw_order.state = state
                        withdraw_order.update_at = now_time

                        db.commit()
                        logger.info(f'订单 {out_bill_no} 转账状态已更新为 {state}')
                except Exception as e:
                    db.rollback()
                    logger.error(f'更新提现订单状态失败: {e}')
                finally:
                    db.close()

            # 4. 返回成功响应（必须，否则微信会重复通知）
            # 严格按照微信要求的格式返回
            return jsonify({'code': 'SUCCESS', 'message': '成功'}), 200

    except Exception as e:
        logger.error(f'处理企业付款回调时发生异常: {e}')
        return jsonify({'code': 'FAIL', 'message': '系统异常'}), 500


@app.route('/api/wechat_withdraw_query', methods=['GET'])
@token_required
def wechat_withdraw_query():
    """主动查询企业付款（提现）订单状态（从数据库查询）"""
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': '用户信息无效'}), 401

        out_bill_no = request.args.get('out_bill_no')
        if not out_bill_no:
            return jsonify({'success': False, 'error': '缺少订单号参数'}), 400

        # 从数据库查询提现订单状态
        db = SessionLocal()
        try:
            withdraw_order = (
                db.query(BasWechatWithdraw)
                .filter(
                    BasWechatWithdraw.id == out_bill_no,
                    BasWechatWithdraw.user_id == user_id,  # 验证订单属于当前用户
                )
                .first()
            )

            if not withdraw_order:
                return jsonify({'success': False, 'error': '订单不存在或无权访问'}), 404

            # 从数据库中查询状态（这是最可靠的方式，因为回调会更新数据库）
            state = withdraw_order.state
            is_notify = withdraw_order.is_notify

            # 如果已经回执通知且状态为SUCCESS，则返回成功
            # is_notify: 0 表示已回执，-1 表示未回执
            is_success = is_notify == 0 and state == 'SUCCESS'

            logger.info(
                f"wechat_withdraw_query success: user_id={user_id}, out_bill_no={out_bill_no}, state={state}, is_notify={is_notify}"
            )
            return (
                jsonify(
                    {
                        'success': is_success,
                        'state': state,
                        'is_notify': is_notify,
                    }
                ),
                200,
            )
        finally:
            db.close()

    except Exception as e:
        logger.exception(f'查询企业付款订单异常: {out_bill_no}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/wechat_withdraw_record', methods=['GET'])
@token_required
def wechat_withdraw_record():
    """获取用户提现记录，按更新时间倒序分页返回"""
    try:
        current_user = request.current_user
        user_id = current_user.get('user_id')

        if not user_id:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        db = SessionLocal()
        try:
            page = request.args.get('page', default=1, type=int)
            page_size = request.args.get('page_size', default=20, type=int)

            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 100:
                page_size = 100

            query = (
                db.query(
                    BasWechatWithdraw.out_bill_no,
                    BasWechatWithdraw.withdraw_amount,
                    BasWechatWithdraw.transfer_remark,
                    BasWechatWithdraw.user_recv_perception,
                    BasWechatWithdraw.state,
                    BasWechatWithdraw.update_time,
                )
                .filter(BasWechatWithdraw.user_id == user_id)
                .order_by(BasWechatWithdraw.update_time.desc())
            )

            total = query.count()
            records = query.offset((page - 1) * page_size).limit(page_size).all()

            data = []
            for record in records:
                data.append(
                    {
                        'out_bill_no': record.out_bill_no,
                        'withdraw_amount': record.withdraw_amount or 0,
                        'transfer_remark': record.transfer_remark or '',
                        'user_recv_perception': record.user_recv_perception or '',
                        'state': record.state or '',
                        'update_time': (
                            record.update_time.isoformat()
                            if record.update_time
                            else None
                        ),
                    }
                )

            logger.info(
                f"wechat_withdraw_record success: user_id={user_id}, total={total}, page={page}, page_size={page_size}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '获取成功',
                        'data': {'records': data, 'total': total},
                    }
                ),
                200,
            )
        except Exception as e:
            logger.error(f"获取提现记录失败: {e}")
            return jsonify({'code': 500, 'message': f'获取失败: {str(e)}'}), 500
        finally:
            db.close()
    except Exception as e:
        logger.error(f"提现记录接口错误: {e}")
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/invite_record', methods=['GET'])
@token_required
def invite_record():
    """
    获取用户的邀请记录

    请求头:
        Authorization: Bearer <token>
    可选查询参数:
        page: 页码，默认为1
        page_size: 每页记录数，默认为20

    返回:
        {
            "code": 200,
            "message": "获取成功",
            "data": {
                "records": [
                    {
                        "user_account": "被邀请人账号",
                        "increase_cost": 9.9,
                        "create_time": "2023-01-01T12:00:00",
                        "status": 1
                    }
                ],
                "total": 100
            }
        }
    """
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')

        # 验证用户ID是否存在
        if not user_id:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 解析查询参数
            page = request.args.get('page', default=1, type=int)
            page_size = request.args.get('page_size', default=20, type=int)

            # 验证分页参数
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 100:
                page_size = 100

            # 构建查询：按当前用户ID关联 bas_invite_record 表的 user_id
            # 然后关联 invite_user_id 到 bas_user 表的 id，获取被邀请用户信息
            query = (
                db.query(
                    SysUser.user_account,
                    BasInviteRecord.increase_cost,
                    SysUser.create_time,
                    SysUser.status,
                )
                .join(SysUser, BasInviteRecord.invite_user_id == SysUser.id)
                .filter(BasInviteRecord.user_id == user_id)
                .order_by(BasInviteRecord.invite_time.desc())
            )

            # 获取总记录数
            total = query.count()

            # 分页
            records = query.offset((page - 1) * page_size).limit(page_size).all()

            # 转换为字典列表
            data = []
            for record in records:
                data.append(
                    {
                        'user_account': record.user_account,
                        'increase_cost': (
                            float(record.increase_cost) if record.increase_cost else 0
                        ),
                        'create_time': (
                            record.create_time.isoformat()
                            if record.create_time
                            else None
                        ),
                        'status': record.status,
                    }
                )

            logger.info(
                f"invite_record success: user_id={user_id}, total={total}, page={page}, page_size={page_size}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '获取成功',
                        'data': {'records': data, 'total': total},
                    }
                ),
                200,
            )
        except Exception as e:
            logger.error(f"获取邀请记录失败: {e}")
            return jsonify({'code': 500, 'message': f'获取失败: {str(e)}'}), 500
        finally:
            db.close()
    except Exception as e:
        logger.error(f"邀请记录接口错误: {e}")
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/wechat_pay_record', methods=['GET'])
@token_required
def wechat_pay_record():
    """
    获取用户的赞助记录

    请求头:
        Authorization: Bearer <token>
    可选查询参数:
        page: 页码，默认为1
        page_size: 每页记录数，默认为20

    返回:
        {
            "code": 200,
            "message": "获取成功",
            "data": {
                "records": [
                    {
                        "out_trade_no": "订单号",
                        "trade_state_desc": "赞助描述",
                        "success_time": "2023-01-01T12:00:00",
                        "payer_total": 1000
                    }
                ],
                "total": 100
            }
        }
    """
    try:
        # 从token中获取当前用户信息
        current_user = request.current_user
        user_id = current_user.get('user_id')

        # 验证用户ID是否存在
        if not user_id:
            return jsonify({'code': 401, 'message': '用户信息无效'}), 401

        # 创建数据库会话
        db = SessionLocal()
        try:
            # 解析查询参数
            page = request.args.get('page', default=1, type=int)
            page_size = request.args.get('page_size', default=20, type=int)

            # 验证分页参数
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 100:
                page_size = 100

            # 构建查询：按当前用户ID查询 bas_wechat_pay 表
            # 只查询支付成功的记录（trade_state为SUCCESS）
            query = (
                db.query(
                    BasWechatPay.out_trade_no,
                    BasWechatPay.trade_state_desc,
                    BasWechatPay.success_time,
                    BasWechatPay.payer_total,
                )
                .filter(
                    BasWechatPay.user_id == user_id,
                    BasWechatPay.trade_state == 'SUCCESS',
                )
                .order_by(BasWechatPay.success_time.desc())
            )

            # 获取总记录数
            total = query.count()

            # 分页
            records = query.offset((page - 1) * page_size).limit(page_size).all()

            # 转换为字典列表
            data = []
            for record in records:
                data.append(
                    {
                        'out_trade_no': record.out_trade_no,
                        'trade_state_desc': record.trade_state_desc or '',
                        'success_time': (
                            record.success_time.isoformat()
                            if record.success_time
                            else None
                        ),
                        'payer_total': record.payer_total if record.payer_total else 0,
                    }
                )

            logger.info(
                f"wechat_pay_record success: user_id={user_id}, total={total}, page={page}, page_size={page_size}"
            )
            return (
                jsonify(
                    {
                        'code': 200,
                        'message': '获取成功',
                        'data': {'records': data, 'total': total},
                    }
                ),
                200,
            )
        except Exception as e:
            logger.error(f"获取赞助记录失败: {e}")
            return jsonify({'code': 500, 'message': f'获取失败: {str(e)}'}), 500
        finally:
            db.close()
    except Exception as e:
        logger.error(f"赞助记录接口错误: {e}")
        return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500


@app.route('/api/debug', methods=['POST'])
@token_required
def debug():
    try:
        body = request.get_data()
        logger.debug(body)
        return jsonify({'code': 200, 'message': 'Debug info logged'}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': f'Debug failed: {str(e)}'}), 500


@app.route('/api/myapi', methods=['POST', 'GET'])
def myapi():
    print("myapi called")
    return jsonify({'code': 200, 'message': 'My API response'}), 200


if __name__ == '__main__':
    # 开发环境运行
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
