# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import json
import asyncio

from typing import List

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from dotenv import load_dotenv
from logger import Logger
import ast

# AccessKey ID：AccessKey ID

# 加载环境变量
load_dotenv()


class Aliyun_Sms:
    logger = None

    def __init__(self):
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        self.logger = Logger().logger
        # 工程代码建议使用更安全的无AK方式，凭据配置方式请参见：https://help.aliyun.com/document_detail/378659.html。
        credential = CredentialClient()
        config = open_api_models.Config(credential=credential)
        # Endpoint 请参考 https://api.aliyun.com/product/Dysmsapi
        config.endpoint = f'dysmsapi.aliyuncs.com'
        config.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
        config.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
        config.connect_timeout = 5000  # 连接超时5秒（单位：毫秒）
        config.read_timeout = 10000  # 读取超时10秒（单位：毫秒）
        self.sms_client = Dysmsapi20170525Client(config)

    def create_client(self):  # -> Dysmsapi20170525Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码建议使用更安全的无AK方式，凭据配置方式请参见：https://help.aliyun.com/document_detail/378659.html。
        credential = CredentialClient()
        config = open_api_models.Config(credential=credential)
        # Endpoint 请参考 https://api.aliyun.com/product/Dysmsapi
        config.endpoint = f'dysmsapi.aliyuncs.com'
        config.access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
        config.access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
        config.connect_timeout = 5000  # 连接超时5秒（单位：毫秒）
        config.read_timeout = 10000  # 读取超时10秒（单位：毫秒）
        self.sms_client = Dysmsapi20170525Client(config)

    def send_code(self, phone: str, code: str) -> None:
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name='',
            template_code='',
            phone_numbers=phone,
            template_param=f'{{"code":"{code}"}}',
        )
        # 关键修改2：配置RuntimeOptions，禁用signal超时
        runtime = util_models.RuntimeOptions()
        runtime.connect_timeout = 5000  # 运行时连接超时（覆盖Client配置）
        runtime.read_timeout = 10000  # 运行时读取超时（覆盖Client配置）
        runtime.autoretry = False  # 关闭自动重试（避免重复触发signal）
        try:
            resp = self.sms_client.send_sms_with_options(send_sms_request, runtime)
            # resp_json = json.dumps(resp, default=str, indent=2)
            # self.logger.info(resp_json)

            body = getattr(resp, 'body', None)
            code = getattr(body, 'code', None)
            message = getattr(body, 'message', None)
            if code == "OK" and message == "OK":
                self.logger.info(f"短信验证发送成功：{phone}")
            else:
                self.logger.error(
                    f"短信验证发送失败，错误码：{code}，错误信息：{message}"
                )
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            raise RuntimeError(error.message)

    async def send_code_async(self, phone: str, code: str) -> None:
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name='',
            template_code='',
            phone_numbers=phone,
            template_param=f'{{"code":"{code}"}}',
        )
        runtime = util_models.RuntimeOptions()
        runtime.connect_timeout = 5000  # 运行时连接超时（覆盖Client配置）
        runtime.read_timeout = 10000  # 运行时读取超时（覆盖Client配置）
        runtime.autoretry = False  # 关闭自动重试（避免重复触发signal）
        try:
            resp = await self.sms_client.send_sms_with_options_async(
                send_sms_request, runtime
            )
            # resp_json = json.dumps(resp, default=str, indent=2)
            # self.logger.info(resp_json)

            body = getattr(resp, 'body', None)
            code = getattr(body, 'code', None)
            message = getattr(body, 'message', None)
            if code == "OK" and message == "OK":
                self.logger.info(f"短信验证发送成功：{phone}")
            else:
                self.logger.error(
                    f"短信验证发送失败，错误码：{code}，错误信息：{message}"
                )
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            raise RuntimeError(error.message)

    def send_notify(self, phone: str) -> None:
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name='',
            template_code='',
            phone_numbers=phone,
            template_param=f'',
        )
        # 关键修改2：配置RuntimeOptions，禁用signal超时
        runtime = util_models.RuntimeOptions()
        runtime.connect_timeout = 5000  # 运行时连接超时（覆盖Client配置）
        runtime.read_timeout = 10000  # 运行时读取超时（覆盖Client配置）
        runtime.autoretry = False  # 关闭自动重试（避免重复触发signal）
        try:
            resp = self.sms_client.send_sms_with_options(send_sms_request, runtime)
            # resp_json = json.dumps(resp, default=str, indent=2)
            # self.logger.info(resp_json)

            body = getattr(resp, 'body', None)
            code = getattr(body, 'code', None)
            message = getattr(body, 'message', None)
            if code == "OK" and message == "OK":
                self.logger.info(f"短信通知发送成功：{phone}")
            else:
                self.logger.error(
                    f"短信通知发送失败，错误码：{code}，错误信息：{message}"
                )
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            raise RuntimeError(error.message)


# if __name__ == '__main__':
#    asyncio.run(Sample.main_async(sys.argv[1:]))
