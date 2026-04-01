from typing import Union
from datetime import datetime, timezone, timedelta
import re


def read_file_content(
    file_path: str, binary: bool = False, encoding: str = "utf-8"
) -> Union[str, bytes]:
    """
    读取文件内容。

    参数:
        file_path: 文件路径。
        binary: 是否以二进制方式读取。为 True 返回 bytes，否则返回 str。
        encoding: 文本模式下使用的编码，默认 utf-8。

    返回:
        文件内容，类型为 str 或 bytes，取决于 binary。

    异常:
        FileNotFoundError: 文件不存在。
        PermissionError: 权限不足。
        UnicodeDecodeError: 文本解码失败（当 binary=False 时）。
        OSError: 其他 I/O 错误。
    """
    if binary:
        with open(file_path, "rb") as f:
            return f.read()
    else:
        with open(file_path, "r", encoding=encoding, errors="strict") as f:
            return f.read()


def convert_iso_time_to_normal(
    iso_time_str: str, format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    将ISO 8601格式时间（如2026-01-23T14:30:28+08:00）转换为常规时间格式
    :param iso_time_str: ISO格式时间字符串
    :param format_str: 目标常规格式（默认：%Y-%m-%d %H:%M:%S）
    :return: 常规时间字符串
    """
    try:
        # 兼容Python 3.10及以下版本（fromisoformat不支持时区中的冒号）
        # 先处理时区部分的冒号（比如+08:00 → +0800）
        iso_time_str_fixed = re.sub(r"(\+|\-)(\d{2}):(\d{2})$", r"\1\2\3", iso_time_str)

        # 解析为带时区的datetime对象
        dt = datetime.fromisoformat(iso_time_str_fixed)

        # 转换为本地时间（或直接格式化，保留时区对应的时间）
        # 若需要转UTC时间：dt = dt.astimezone(datetime.timezone.utc)
        normal_time = dt.strftime(format_str)

        return normal_time
    except Exception as e:
        print(f"时间转换失败：{e}")
        return ""


def get_current_utc_time() -> datetime:
    """
    获取当前UTC时间的datetime对象
    :return: 当前UTC时间的datetime对象
    """
    return datetime.now(timezone.utc)


def get_current_local_time() -> datetime:
    """
    获取当前本地时间的datetime对象
    :return: 当前本地时间的datetime对象
    """
    return datetime.now()
